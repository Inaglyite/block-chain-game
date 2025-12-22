# -*- coding: utf-8 -*-
import pygame
import sys
import random
import math
import json
from decimal import Decimal
from web3 import Web3
from enum import Enum

# 初始化pygame
pygame.init()

# ---------------- 中文字体加载增强 ----------------
# 动态尝试多种常见中文字体，若不可用则回退到默认字体；可在 assets/fonts 下放自定义 TTF
FONT_CANDIDATES = [
    "simhei",             # 黑体
    "wenquanyi micro hei",# 文泉驿微米黑
    "wenquanyi zen hei",  # 文泉驿正黑
    "noto sans cjk sc",   # Noto CJK 简体
    "noto sans sc",       # 简体 Noto
    "source han sans sc", # 思源黑体 SC
    "sarasa ui sc",       # 更纱黑体 SC
    "microsoft yahei",    # 微软雅黑
    "arial unicode ms",   # Arial Unicode
]
TEXT_MAIN = (225, 235, 245)
def load_chinese_font(size: int):
    available = set(pygame.font.get_fonts())  # 全部小写
    # 允许使用本地 assets 字体文件（若用户自行放置）
    custom_paths = [
        f"assets/fonts/SimHei.ttf",
        f"assets/fonts/simhei.ttf",
        f"assets/fonts/NotoSansSC-Regular.otf",
        f"assets/fonts/NotoSansSC-Regular.ttf",
    ]
    for p in custom_paths:
        try:
            return pygame.font.Font(p, size)
        except Exception:
            pass
    for name in FONT_CANDIDATES:
        key = name.lower().replace(" ", "")
        # pygame.font.get_fonts() 去掉空格，只保留字母数字；简化匹配
        # 这里做宽松包含匹配
        if any(key in f for f in available):
            try:
                fnt = pygame.font.SysFont(name, size)
                # 简单测试中文是否宽度正常（>0 且不是仅方块宽度异常）
                test_surface = fnt.render("测试中文", True, (0,0,0))
                if test_surface.get_width() > 0:
                    print(f"✅ 使用中文字体: {name} (size={size})")
                    return fnt
            except Exception:
                continue
    print(f"⚠️ 未找到合适中文字体，回退默认字体 size={size}. 建议安装：fonts-wqy-microhei 或 fonts-noto-cjk")
    return pygame.font.Font(None, size)

def draw_panel(surface, rect, title=None):
    pygame.draw.rect(surface, PANEL, rect, border_radius=10)
    pygame.draw.rect(surface, PANEL_BORDER, rect, 2, border_radius=10)
    if title:
        t = small_font.render(title, True, ACCENT_BLUE)
        surface.blit(t, (rect.x + 10, rect.y - 18))


def draw_label(surface, label, pos, value=None, value_color=TEXT_MAIN):
    l = small_font.render(label, True, TEXT_DIM)
    surface.blit(l, pos)
    if value is not None:
        v = small_font.render(str(value), True, value_color)
        surface.blit(v, (pos[0] + 90, pos[1]))


# 屏幕设置
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("区块链旋转除草NFT游戏")

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 128, 0)
LIGHT_GREEN = (144, 238, 144)
BROWN = (139, 69, 19)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
PURPLE = (128, 0, 128)
GOLD = (255, 215, 0)
GRAY = (128, 128, 128)
DARK_GREEN = (0, 100, 0)

# UI 主题色
BG_DARK = (18, 22, 28)
PANEL = (28, 32, 40)
PANEL_BORDER = (70, 90, 120)
TEXT_MAIN = (225, 235, 245)
TEXT_DIM = (160, 175, 190)
ACCENT_BLUE = (64, 156, 255)
SUCCESS_GREEN = (80, 200, 120)
WARNING_RED = (240, 90, 90)


# 字体 (改为动态中文字体加载)
font = load_chinese_font(20)
large_font = load_chinese_font(32)
small_font = load_chinese_font(16)


# 武器稀有度
class Rarity(Enum):
    COMMON = 0
    RARE = 1
    EPIC = 2
    LEGENDARY = 3

# 武器磨损度枚举
class Condition(Enum):
    S = 0  # S级 / 极佳（像全新）
    A = 1  # A级 / 优良
    B = 2  # B级 / 良好
    C = 3  # C级 / 普通
    D = 4  # D级 / 磨损
    E = 5  # E级 / 严重磨损


class BlockchainGame:
    def __init__(self):
        self.setup_blockchain()
        self.weapons = []
        self.current_weapon_index = 0
        self.score = 0
        self.coins = 0
        self.grass_patches = []
        self.angle = 0
        self.rotation_speed = 5
        self.game_state = "playing"
        self.market_weapons = []
        self.last_refresh_block = 0
        self.auto_refresh_interval = 30  # 每30帧自动尝试刷新（≈0.5秒）
        self.pending_points = 0  # 尚未上链的累计分数
        self.last_flush_ms = 0    # 上一次写链时间戳
        self.flush_interval_ms = 3000  # 每3秒尝试上链一次
        # 玩家属性
        self.player_x = WIDTH // 2
        self.player_y = HEIGHT // 2
        self.player_speed = 6
        self.player_radius = 22
        self.standing_grass_id = None  # 当前所站草块索引

        self.load_player_data()
        self.generate_grass()
        self.load_market_weapons()

        # 上架弹窗状态
        self.show_listing_modal = False
        self.listing_weapon = None
        self.listing_price_str = ""
        self.listing_min_eth = None
        self.listing_max_eth = None
        self.listing_recommended_eth = None

        print("游戏初始化完成!")

    def setup_blockchain(self):
        """设置区块链连接"""
        try:
            self.w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))

            if not self.w3.is_connected():
                raise Exception("无法连接到区块链网络")

            print(f"✅ 连接到区块链网络，最新区块: {self.w3.eth.block_number}")

            # 加载合约信息
            with open('contract-info.json', 'r') as f:
                contract_info = json.load(f)

            with open('WeedCutterNFT.json', 'r') as f:
                contract_data = json.load(f)

            raw_address = contract_info['address']
            try:
                # 转换为 checksum 地址，避免 web3.py 报错
                self.contract_address = self.w3.to_checksum_address(raw_address)
            except Exception:
                print(f"⚠️ 地址 {raw_address} 转换 checksum 失败，继续使用原始地址")
                self.contract_address = raw_address

            self.contract_abi = contract_data['abi']

            # 合约代码存在性检查（防止使用旧的地址）
            code = self.w3.eth.get_code(self.contract_address)
            if code in (b"", b"0x", b"0"):
                print("⚠️ 该地址上没有合约代码。请确认已重新部署并更新 contract-info.json")

            self.contract = self.w3.eth.contract(
                address=self.contract_address,
                abi=self.contract_abi
            )

            # 使用第一个账户（hardhat 节点默认解锁）
            self.account = self.w3.eth.accounts[0]
            print(f"使用账户: {self.account}")

        except FileNotFoundError as e:
            print(f"❌ 未找到文件: {e}. 请先运行部署脚本: npx hardhat run scripts/deploy.ts --network localhost")
            sys.exit(1)
        except Exception as e:
            print(f"❌ 区块链设置失败: {e}")
            print("请确保 Hardhat 节点正在运行: npx hardhat node，并且已执行部署脚本")
            sys.exit(1)

    # 在 BlockchainGame 类中添加这个方法
    def get_weapon_display_name(self, weapon_name, rarity):
        """将英文武器名称转换为中文显示名称"""
        weapon_base_names = {
            "Starter Cutter": "新手除草刀",
            "Sharp Sickle": "锋利除草镰",
            "Epic Sword": "史诗除草剑",
            "Common Cutter": "普通除草刀",
            "Rare Sickle": "稀有除草镰",
            "Epic Blade": "史诗除草刃",
            "Legendary Axe": "传奇除草斧"
        }

        # 如果是已知的武器名称，返回中文名
        if weapon_name in weapon_base_names:
            return weapon_base_names[weapon_name]

        # 否则根据稀有度生成中文名
        rarity_names = {
            Rarity.COMMON: "普通",
            Rarity.RARE: "稀有",
            Rarity.EPIC: "史诗",
            Rarity.LEGENDARY: "传奇"
        }

        weapon_types = ["除草刀", "除草镰", "除草剑", "除草斧", "除草锤"]
        return f"{rarity_names[rarity]}{random.choice(weapon_types)}"

    def load_player_data(self):
        """从区块链加载玩家数据"""
        try:
            # 加载本地删除黑名单（持久化，以便重启游戏后仍然生效）
            deleted_ids = self._load_local_deleted_ids()

            self.score, self.coins = self.contract.functions.getPlayerStats(self.account).call()
            weapon_ids = self.contract.functions.getUserWeapons(self.account).call()
            self.weapons = []
            # 过滤被本地删除的武器
            if deleted_ids:
                weapon_ids = [wid for wid in weapon_ids if wid not in deleted_ids]
            for weapon_id in weapon_ids:
                weapon_data = self.contract.functions.getWeaponDetails(weapon_id).call()
                display_name = self.get_weapon_display_name(
                    weapon_data[1],
                    Rarity(weapon_data[2])
                )
                # 获取磨损度/等级：合约可能只存储 Condition enum (0..5)
                wear = None
                grade = None
                if len(weapon_data) > 7:
                    try:
                        raw = weapon_data[7]
                        if isinstance(raw, (int, float)):
                            ival = int(raw)
                            # 若链上字段是 0..5，视为 Condition 枚举
                            if 0 <= ival <= 5:
                                try:
                                    grade = Condition(ival)
                                except Exception:
                                    grade = None
                            else:
                                # 否则将其视为按 1e10 缩放的 wear 值（或任意大整数编码）
                                wear = (ival % (10**10)) / 1e10
                    except Exception:
                        pass
                if wear is None:
                    # 根据 weapon_id 和 owner 生成确定性的磨损值，避免每次不一致
                    wear = self.compute_wear_seed(weapon_data[0], weapon_data[4])
                # 若链上给出了枚举优先使用，否则根据 wear 映射等级
                if grade is None:
                    grade = self.wear_to_condition_grade(wear)
                weapon = {
                    'id': weapon_data[0],
                    'name': display_name,
                    'original_name': weapon_data[1],
                    'rarity': Rarity(weapon_data[2]),
                    'damage_multiplier': weapon_data[3] / 100.0,
                    'owner': weapon_data[4],
                    'price': weapon_data[5],
                    'for_sale': weapon_data[6],
                    'condition': grade,
                    'wear': wear
                }
                self.weapons.append(weapon)

            # 排序：已上架的排后面，按稀有度和ID
            self.weapons.sort(key=lambda w: (w['for_sale'], -w['rarity'].value, w['id']))
            print(f"加载了 {len(self.weapons)} 把武器")
        except Exception as e:
            print(f"加载玩家数据失败: {e}")

    def load_market_weapons(self):
        """从链上加载市场上在售武器"""
        try:
            # 遍历所有武器ID，筛选 forSale = true (也可以扩展用 getWeaponsForSale, 这里使用逐个以兼容当前ABI). 如果合约已有 getWeaponsForSale 可调用
            sale_list = []
            try:
                # 优先尝试批量函数
                sale_list = self.contract.functions.getWeaponsForSale().call()
            except Exception:
                total_next = self.contract.functions.getNextWeaponId().call()
                for weapon_id in range(1, total_next):
                    wdata = self.contract.functions.getWeaponDetails(weapon_id).call()
                    if wdata[6]:  # forSale
                        sale_list.append(wdata)
            # 加载本地删除黑名单，避免在市场中显示已本地删除的武器
            deleted_ids = self._load_local_deleted_ids()
            self.market_weapons = []
            for w in sale_list:
                if deleted_ids and w[0] in deleted_ids:
                    continue
                display_name = self.get_weapon_display_name(w[1], Rarity(w[2]))
                # 获取磨损度/等级（优先识别合约返回的 Condition enum）
                wear = None
                grade = None
                if len(w) > 7:
                    try:
                        raw = w[7]
                        if isinstance(raw, (int, float)):
                            ival = int(raw)
                            if 0 <= ival <= 5:
                                try:
                                    grade = Condition(ival)
                                except Exception:
                                    grade = None
                            else:
                                wear = (ival % (10**10)) / 1e10
                    except Exception:
                        pass
                if wear is None:
                    wear = self.compute_wear_seed(w[0], w[4])
                if grade is None:
                    grade = self.wear_to_condition_grade(wear)
                self.market_weapons.append({
                    'id': w[0],
                    'name': display_name,
                    'original_name': w[1],
                    'rarity': Rarity(w[2]),
                    'damage_multiplier': w[3] / 100.0,
                    'owner': w[4],
                    'price': w[5],
                    'for_sale': w[6],
                    'condition': grade,
                    'wear': wear
                })
            # 排序：价格低的排前，稀有度高优先
            self.market_weapons.sort(key=lambda w: (w['price'], -w['rarity'].value))
        except Exception as e:
            print(f"加载市场数据失败: {e}")

    def _local_deleted_path(self):
        return 'deleted_weapons.json'

    def _load_local_deleted_ids(self):
        try:
            import os
            p = self._local_deleted_path()
            if not os.path.exists(p):
                return set()
            with open(p, 'r') as f:
                data = json.load(f)
            return set(int(x) for x in data)
        except Exception:
            return set()

    def _mark_local_deleted(self, weapon_id):
        try:
            p = self._local_deleted_path()
            s = self._load_local_deleted_ids()
            s.add(int(weapon_id))
            with open(p, 'w') as f:
                json.dump(sorted(list(s)), f)
        except Exception as e:
            print(f"无法写入本地删除文件: {e}")

    def delete_weapon(self, weapon):
        """尝试链上删除武器（若合约支持），否则回退到本地删除并持久化黑名单。"""
        wid = int(weapon['id'])
        # 尝试链上删除（合约可能未实现 burn/remove）
        try:
            # 通过 getattr 检查函数是否存在在 ABI 中
            burn_fn = None
            try:
                burn_fn = getattr(self.contract.functions, 'burn')
            except Exception:
                burn_fn = None

            if burn_fn:
                print(f"尝试链上销毁武器 {wid} ...")
                tx = self.contract.functions.burn(wid).build_transaction({
                    'from': self.account,
                    'gas': 200000,
                    'gasPrice': self.w3.to_wei('2', 'gwei'),
                    'nonce': self.w3.eth.get_transaction_count(self.account)
                })
                tx_hash = self.w3.eth.send_transaction(tx)
                print(f"⏳ 销毁交易发送: {tx_hash.hex()} 等待确认...")
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)
                status = receipt.get('status', 0) if isinstance(receipt, dict) else getattr(receipt, 'status', 0)
                if status == 1:
                    print("✅ 链上销毁成功")
                    self.load_player_data()
                    return
                else:
                    print("❌ 链上销毁交易失败，回退到本地删除")

        except Exception as e:
            print(f"链上删除尝试失败: {e}，回退到本地删除")

        # 本地删除
        try:
            self._mark_local_deleted(wid)
            self.weapons = [w for w in self.weapons if w['id'] != wid]
            print(f"本地已删除武器 {wid} (持久化到 deleted_weapons.json)")
        except Exception as e:
            print(f"本地删除失败: {e}")

    def record_score(self, points):
        """立即将累计分数写链（内部使用）"""
        try:
            if points <= 0:
                return
            tx = self.contract.functions.recordWeedCut(points).build_transaction({
                'from': self.account,
                'gas': 180000,
                'gasPrice': self.w3.to_wei('2', 'gwei'),
                'nonce': self.w3.eth.get_transaction_count(self.account)
            })
            tx_hash = self.w3.eth.send_transaction(tx)
            print(f"⏳ 正在上链累计分数 {points} tx={tx_hash.hex()}")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            status = getattr(receipt, 'status', 1)
            if status == 1:
                print("✅ 分数上链成功")
                self.score, self.coins = self.contract.functions.getPlayerStats(self.account).call()
            else:
                print("❌ 分数交易失败")
        except Exception as e:
            print(f"记录分数失败: {e}")

    def maybe_flush_points(self):
        """根据时间与阈值把 pending_points 写链"""
        now = pygame.time.get_ticks()
        # 若累计分数达到阈值或间隔已到则写链
        if self.pending_points >= 50 or (self.pending_points > 0 and (now - self.last_flush_ms) >= self.flush_interval_ms):
            to_flush = self.pending_points
            self.pending_points = 0
            self.last_flush_ms = now
            self.record_score(to_flush)

    def draw(self, surface):
        surface.fill(BG_DARK)

    # ===== 顶部 HUD =====
        top_bar = pygame.Rect(0, 0, WIDTH, 60)
        pygame.draw.rect(surface, PANEL, top_bar)

        title = large_font.render("⛓ Weed Slayer NFT", True, TEXT_MAIN)
        surface.blit(title, (20, 14))

        block_info = small_font.render(
            f"Block {self.w3.eth.block_number} | {self.contract_address[:10]}...",
            True, TEXT_DIM
        )
        surface.blit(block_info, (WIDTH - block_info.get_width() - 20, 22))

    # ===== 左侧玩家面板 =====
        player_panel = pygame.Rect(20, 80, 260, 170)
        draw_panel(surface, player_panel, "PLAYER")

        draw_label(surface, "Address", (30, 100), self.account[:8] + "...")
        draw_label(
            surface,
            "Score",
            (30, 125),
            f"{self.score} (+{self.pending_points})",
            SUCCESS_GREEN if self.pending_points == 0 else WARNING_RED
        )
        draw_label(surface, "Gold", (30, 150), self.coins, GOLD)
        draw_label(surface, "Weapons", (30, 175), len(self.weapons))

    # ===== 主界面 =====
        if self.game_state == "playing":
            self.draw_game(surface)
        elif self.game_state == "marketplace":
            self.draw_marketplace(surface)
        elif self.game_state == "inventory":
            self.draw_inventory(surface)

        # 若弹窗打开，绘制弹窗（覆盖在最上层）
        if self.show_listing_modal:
            self.draw_listing_modal(surface)

    # ===== 底部技能栏 =====
        skill_bar = pygame.Rect(0, HEIGHT - 60, WIDTH, 60)
        pygame.draw.rect(surface, PANEL, skill_bar)

        skills = [
            ("SPACE", "Slash"),
            ("N", "Forge"),
            ("M", "Market"),
            ("I", "Bag"),
            ("ESC", "Back")
        ]

        x = 20
        for key, name in skills:
            box = pygame.Rect(x, HEIGHT - 45, 95, 36)
            pygame.draw.rect(surface, PANEL_BORDER, box, 1, border_radius=6)
            txt = small_font.render(f"{key}  {name}", True, TEXT_MAIN)
            surface.blit(txt, (box.x + 8, box.y + 8))
            x += 105


    # --- 新增：2.5D 投影核心算法 ---
    def to_iso(self, x, y):
        """将逻辑坐标(2D)转换为等轴测屏幕坐标(2.5D)"""
        # 这里的 0.5 决定了视角的倾斜度
        iso_x = (x - y) + WIDTH // 2  # 将原点移到屏幕中心
        iso_y = (x + y) * 0.5 + 50     # +50 是垂直偏移量
        return int(iso_x), int(iso_y)

    # --- 新增：绘制立体方块 ---
    def draw_iso_cube(self, surface, x, y, width, height, color_top, color_side, z_height=0):
        """
        在逻辑坐标 (x,y) 处绘制一个立体方块
        width/height: 方块在逻辑世界的大小
        z_height: 方块的厚度/高度
        """
        # 计算四个角的逻辑坐标
        half_w = width / 2
        half_h = height / 2
        
        # 逻辑顶点 (Top-Left, Top-Right, Bottom-Right, Bottom-Left)
        pts_logic = [
            (x - half_w, y - half_h),
            (x + half_w, y - half_h),
            (x + half_w, y + half_h),
            (x - half_w, y + half_h)
        ]
        
        # 投影到屏幕坐标
        pts_iso = [self.to_iso(px, py) for px, py in pts_logic]
        
        # 提升高度 (Y轴向上减)
        pts_top = [(ix, iy - z_height) for ix, iy in pts_iso]
        
        # 颜色变暗处理 (模拟阴影)
        def darken(c, f): return (int(c[0]*f), int(c[1]*f), int(c[2]*f))
        c_side_r = darken(color_side, 0.8) # 右侧面较暗
        c_side_l = darken(color_side, 0.6) # 左侧面更暗

        # 1. 绘制左侧面 (连接 Top[3]-Top[0] 和 Bottom[3]-Bottom[0])
        # 顶点顺序: Top[3], Top[0], Bottom[0], Bottom[3] (Bottom其实就是pts_iso)
        # 实际上侧面是连接 Top 和 Base。
        # 左侧面: Left Point (3) -> Bottom Point (2) 
        # 让我们用更通用的顶点索引：0:Top, 1:Right, 2:Bottom, 3:Left
        # 注意：to_iso 变换后，pts_iso[0]是上，[1]是右，[2]是下，[3]是左 (取决于 x-y)
        # 修正：(x-y) 变换后：
        # (x-half, y-half) -> Top (最远)
        # (x+half, y-half) -> Right
        # (x+half, y+half) -> Bottom (最近)
        # (x-half, y+half) -> Left
        
        # 绘制右侧面 (连接 Right(1) 和 Bottom(2))
        poly_right = [pts_top[1], pts_top[2], pts_iso[2], pts_iso[1]]
        pygame.draw.polygon(surface, c_side_r, poly_right)
        
        # 绘制左侧面 (连接 Left(3) 和 Bottom(2))
        poly_left = [pts_top[2], pts_top[3], pts_iso[3], pts_iso[2]]
        pygame.draw.polygon(surface, c_side_l, poly_left)
        
        # 绘制顶面
        pygame.draw.polygon(surface, color_top, pts_top)
        # 顶面描边
        pygame.draw.polygon(surface, darken(color_top, 0.5), pts_top, 1)

    def draw_game(self, surface):
        """绘制2.5D游戏画面"""
        # 1. 准备渲染列表 (为了正确的遮挡关系，我们需要排序)
        render_list = []

        # 添加草地到渲染列表
        for grass in self.grass_patches:
            # 计算中心点用于排序
            center_x = grass['x'] + grass['width'] / 2
            center_y = grass['y'] + grass['height'] / 2
            
            is_cut = grass['health'] <= 50
            # 设置颜色和高度
            item = {
                'type': 'grass',
                'sort_depth': center_x + center_y, # 简单的深度排序键
                'x': center_x,
                'y': center_y,
                'w': grass['width'],
                'h': grass['height'],
                'color': GREEN if not is_cut else BROWN,
                'side_color': DARK_GREEN if not is_cut else (100, 50, 0),
                'height': 20 if not is_cut else 5, # 未除草比较高，除草后变矮
                'health': grass['health'],
                'player_on': grass.get('player_on', False)
            }
            render_list.append(item)

        # 添加玩家到渲染列表
        render_list.append({
            'type': 'player',
            'sort_depth': self.player_x + self.player_y,
            'x': self.player_x,
            'y': self.player_y
        })

        # 2. 排序：按照 sort_depth 从小到大画 (从远到近)
        render_list.sort(key=lambda item: item['sort_depth'])

        # 3. 绘制循环
        for item in render_list:
            if item['type'] == 'grass':
                # 高亮判定
                top_c = item['color']
                if item['player_on']:
                    top_c = LIGHT_GREEN # 踩上去变亮
                
                self.draw_iso_cube(surface, item['x'], item['y'], item['w'], item['h'], 
                                   top_c, item['side_color'], item['height'])
                
                # 绘制简单的血条 (悬浮在方块上方)
                iso_pos = self.to_iso(item['x'], item['y'])
                hp_screen_x, hp_screen_y = iso_pos[0], iso_pos[1] - item['height'] - 10
                if item['health'] < 100:
                    width_hp = 40 * (item['health'] / 100)
                    pygame.draw.rect(surface, RED, (hp_screen_x - 20, hp_screen_y, width_hp, 4))

            elif item['type'] == 'player':
                self.draw_player_iso(surface)

        # 4. 提示 UI (画在最上层)
        tip = font.render("按住空格键旋转除草，分数将记录到区块链!", True, DARK_GREEN)
        surface.blit(tip, (WIDTH // 2 - tip.get_width() // 2, HEIGHT - 80))
        
        # 调试信息
        if self.standing_grass_id is not None:
             stand_tip = small_font.render(f"位置: {int(self.player_x)},{int(self.player_y)}", True, BLUE)
             surface.blit(stand_tip, (WIDTH - 150, 100))

    def draw_player_iso(self, surface):
        """专门绘制2.5D玩家和武器"""
        # 玩家身体 (简单的蓝色立方体)
        self.draw_iso_cube(surface, self.player_x, self.player_y, 40, 40, BLUE, (0, 0, 150), 35)
        
        # 玩家头部 (稍微偏移一点)
        head_pos = self.to_iso(self.player_x, self.player_y)
        head_y = head_pos[1] - 45 # 身体高度之上
        pygame.draw.circle(surface, (255, 200, 150), (head_pos[0], int(head_y)), 12)
        
        # --- 武器绘制 (关键：投影旋转) ---
        # 计算武器在逻辑平面的终点
        weapon_len = 100
        angle_rad = math.radians(self.angle)
        
        start_logic = (self.player_x, self.player_y)
        end_logic_x = self.player_x + weapon_len * math.cos(angle_rad)
        end_logic_y = self.player_y + weapon_len * math.sin(angle_rad)
        
        # 将起点和终点都投影到 ISO 屏幕坐标
        start_iso = self.to_iso(*start_logic)
        end_iso = self.to_iso(end_logic_x, end_logic_y)
        
        # 修正高度：武器应该拿在手里，而不是地上
        hand_height = 25
        s_iso = (start_iso[0], start_iso[1] - hand_height)
        e_iso = (end_iso[0], end_iso[1] - hand_height)
        
        # 获取武器颜色
        curr_w = self.get_current_weapon()
        w_color = self.get_rarity_color(curr_w['rarity']) if curr_w else GRAY
        
        # 画刀身
        pygame.draw.line(surface, w_color, s_iso, e_iso, 6)
        
        # 画拖尾 (如果是旋转状态)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            # 简单的模拟拖尾：画几条更透明的线
            for i in range(1, 4):
                offset_ang = math.radians(self.angle - i * 10)
                tail_x = self.player_x + weapon_len * math.cos(offset_ang)
                tail_y = self.player_y + weapon_len * math.sin(offset_ang)
                tail_iso = self.to_iso(tail_x, tail_y)
                t_iso = (tail_iso[0], tail_iso[1] - hand_height)
                # 注意：pygame 不直接支持 alpha line，这里简单用细线模拟
                pygame.draw.line(surface, w_color, s_iso, t_iso, 2)

    def draw_marketplace(self, surface):
        """绘制市场"""
        title = large_font.render("NFT武器市场 - 链上实时在售", True, BLACK)
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 120))

        if not self.market_weapons:
            empty_text = font.render("当前没有武器在售。去背包上架一些吧!", True, BLACK)
            surface.blit(empty_text, (WIDTH // 2 - empty_text.get_width() // 2, 200))
            return

        for i, weapon in enumerate(self.market_weapons):
            y_pos = 180 + i * 130
            rarity_color = self.get_rarity_color(weapon['rarity'])
            card_rect = pygame.Rect(100, y_pos, 1000, 110)
            pygame.draw.rect(surface, rarity_color, card_rect)
            pygame.draw.rect(surface, rarity_color, card_rect, 3)

            name_text = font.render(f"名称: {weapon['name']}", True, BLACK)
            rarity_text = font.render(f"稀有度: {self.get_rarity_name(weapon['rarity'])}", True, BLACK)
            damage_text = font.render(f"伤害倍率: {weapon['damage_multiplier']:.1f}", True, BLACK)
            price_eth = self.w3.from_wei(weapon['price'], 'ether')
            owner_short = weapon['owner'][:10] + '...'
            owner_text = font.render(f"卖家: {owner_short}", True, BLACK)
            price_text = font.render(f"价格: {price_eth:.4f} ETH", True, BLACK)

            surface.blit(name_text, (120, y_pos + 15))
            surface.blit(rarity_text, (120, y_pos + 45))
            surface.blit(damage_text, (120, y_pos + 75))
            # 添加磨损度显示（显示精确 wear）
            condition_text = font.render(f"磨损度: {self.get_condition_name(weapon['wear'])}", True, BLACK)
            surface.blit(condition_text, (400, y_pos + 15))
            surface.blit(price_text, (400, y_pos + 45))
            surface.blit(owner_text, (400, y_pos + 75))

            buy_button = pygame.Rect(800, y_pos + 35, 120, 40)
            pygame.draw.rect(surface, GREEN, buy_button)
            pygame.draw.rect(surface, BLACK, buy_button, 2)
            buy_text = font.render("购买", True, BLACK)
            surface.blit(buy_text, (830, y_pos + 45))

    def draw_inventory(self, surface):
        """绘制背包"""
        title = large_font.render("我的武器库 - 链上NFT", True, BLACK)
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 120))

        if not self.weapons:
            no_weapons = font.render("您还没有任何武器，去市场购买吧！", True, BLACK)
            surface.blit(no_weapons, (WIDTH // 2 - no_weapons.get_width() // 2, 200))
            return

        for i, weapon in enumerate(self.weapons):
            y_pos = 180 + i * 130
            rarity_color = self.get_rarity_color(weapon['rarity'])
            card_rect = pygame.Rect(100, y_pos, 1000, 110)
            pygame.draw.rect(surface, rarity_color, card_rect)
            pygame.draw.rect(surface, BLACK, card_rect, 3)

            name_text = font.render(f"名称: {weapon['name']}", True, BLACK)
            rarity_text = font.render(f"稀有度: {self.get_rarity_name(weapon['rarity'])}", True, BLACK)
            damage_text = font.render(f"伤害倍率: {weapon['damage_multiplier']:.1f}", True, BLACK)
            token_text = font.render(f"Token ID: {weapon['id']}", True, BLACK)
            status_text = font.render("状态: 在售" if weapon['for_sale'] else "状态: 未上架", True, BLACK)

            surface.blit(name_text, (120, y_pos + 15))
            surface.blit(rarity_text, (120, y_pos + 45))
            surface.blit(damage_text, (120, y_pos + 75))
            surface.blit(token_text, (400, y_pos + 15))
            # 添加磨损度显示（显示精确 wear）
            condition_text = font.render(f"磨损度: {self.get_condition_name(weapon['wear'])}", True, BLACK)
            surface.blit(condition_text, (400, y_pos + 45))
            surface.blit(status_text, (400, y_pos + 75))

            equip_button = pygame.Rect(750, y_pos + 15, 100, 35)
            is_current = i == self.current_weapon_index
            pygame.draw.rect(surface, GOLD if is_current else BLUE, equip_button)
            pygame.draw.rect(surface, BLACK, equip_button, 2)
            equip_text = font.render("已装备" if is_current else "装备", True, BLACK)
            surface.blit(equip_text, (equip_button.x + 10, equip_button.y + 7))

            list_button = pygame.Rect(870, y_pos + 15, 130, 35)
            pygame.draw.rect(surface, GREEN if not weapon['for_sale'] else GRAY, list_button)
            pygame.draw.rect(surface, BLACK, list_button, 2)
            list_text = font.render("上架出售" if not weapon['for_sale'] else "已上架", True, BLACK)
            surface.blit(list_text, (list_button.x + 10, list_button.y + 7))

            # 删除按钮（需按住 Shift 点击以确认）
            delete_button = pygame.Rect(1010, y_pos + 15, 100, 35)
            pygame.draw.rect(surface, WARNING_RED, delete_button)
            pygame.draw.rect(surface, BLACK, delete_button, 2)
            delete_text = font.render("删除", True, BLACK)
            surface.blit(delete_text, (delete_button.x + 28, delete_button.y + 7))

    def get_rarity_color(self, rarity):
        colors = {
            Rarity.COMMON: GRAY,
            Rarity.RARE: BLUE,
            Rarity.EPIC: PURPLE,
            Rarity.LEGENDARY: GOLD
        }
        return colors[rarity]

    def get_current_weapon(self):
        if self.weapons and self.current_weapon_index < len(self.weapons):
            return self.weapons[self.current_weapon_index]
        return {'rarity': Rarity.COMMON, 'damage_multiplier': 1.0, 'name': '空手'}

    def handle_click(self, pos):
        if self.game_state == "marketplace":
            for i, weapon in enumerate(self.market_weapons):
                button_rect = pygame.Rect(800, 180 + i * 130 + 35, 120, 40)
                if button_rect.collidepoint(pos):
                    self.purchase_weapon(weapon)
                    return
        elif self.game_state == "inventory":
            for i, weapon in enumerate(self.weapons):
                equip_rect = pygame.Rect(750, 180 + i * 130 + 15, 100, 35)
                list_rect = pygame.Rect(870, 180 + i * 130 + 15, 130, 35)
                delete_rect = pygame.Rect(1010, 180 + i * 130 + 15, 100, 35)
                if equip_rect.collidepoint(pos):
                    self.current_weapon_index = i
                    return
                if list_rect.collidepoint(pos) and not weapon['for_sale']:
                    # 打开自定义价格弹窗
                    self.open_list_modal(weapon)
                    return
                if delete_rect.collidepoint(pos):
                    # 需要按住 Shift 才会真正删除，避免误操作
                    mods = pygame.key.get_mods()
                    if mods & pygame.KMOD_SHIFT:
                        self.delete_weapon(weapon)
                    else:
                        print("提示：按住 Shift 并点击删除以确认操作")
                    return

    def purchase_weapon(self, weapon):
        try:
            # 不再检查是否是自己的武器，允许购买自己的武器
            if weapon['owner'] == self.account:
                print("⚠️  购买自己上架的武器")
            
            # 检查武器是否在出售状态
            if not weapon['for_sale']:
                print("❌ 武器不在出售中")
                return
            
            # 检查账户余额
            balance = self.w3.eth.get_balance(self.account)
            price_eth = self.w3.from_wei(weapon['price'], 'ether')
            balance_eth = self.w3.from_wei(balance, 'ether')
            print(f"尝试购买武器 ID {weapon['id']} 价格 {price_eth} ETH")
            print(f"当前账户余额: {balance_eth} ETH")
            
            if balance < weapon['price']:
                print(f"❌ 账户余额不足，需要 {price_eth} ETH，但只有 {balance_eth} ETH")
                return
            
            # 先刷新武器状态，确保获取最新的在售信息
            print("刷新武器状态中...")
            self.load_market_weapons()
            # 重新找到这个武器
            updated_weapon = None
            for w in self.market_weapons:
                if w['id'] == weapon['id']:
                    updated_weapon = w
                    break
            
            if not updated_weapon:
                print(f"❌ 武器 ID {weapon['id']} 不再在售，刷新后未找到")
                return
            
            # 使用更新后的武器信息
            weapon = updated_weapon
            
            # 优化交易参数以避免Internal error
            try:
                # 尝试使用自动gas估算
                gas_estimate = self.contract.functions.purchaseWeapon(weapon['id']).estimate_gas({
                    'from': self.account,
                    'value': weapon['price']
                })
                print(f"自动估算的gas: {gas_estimate}")
                gas_limit = int(gas_estimate * 1.5)  # 增加50%的缓冲
            except Exception as gas_error:
                print(f"Gas估算失败: {gas_error}，使用默认值")
                gas_limit = 600000  # 更高的默认gas限制
            
            # 获取当前gas价格
            try:
                current_gas_price = self.w3.eth.gas_price
                print(f"当前网络gas价格: {self.w3.from_wei(current_gas_price, 'gwei')} gwei")
                gas_price = int(current_gas_price * 1.2)  # 稍微提高一点
            except:
                gas_price = self.w3.to_wei('5', 'gwei')  # 默认值
            
            # 获取nonce，使用两种方式确保正确
            try:
                nonce = self.w3.eth.get_transaction_count(self.account, 'pending')
            except:
                nonce = self.w3.eth.get_transaction_count(self.account)
            print(f"使用nonce: {nonce}")
            
            # 构建交易
            tx = self.contract.functions.purchaseWeapon(weapon['id']).build_transaction({
                'from': self.account,
                'value': weapon['price'],
                'gas': gas_limit,
                'gasPrice': gas_price,
                'nonce': nonce,
                'chainId': self.w3.eth.chain_id  # 添加chainId确保交易正确
            })
            
            # 发送交易
            print("正在发送交易...")
            try:
                tx_hash = self.w3.eth.send_transaction(tx)
                print(f"⏳ 购买交易发送: {tx_hash.hex()} 等待确认...")
                
                # 使用较短的超时时间，避免长时间等待
                try:
                    receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)
                    status = receipt.get('status', 0) if isinstance(receipt, dict) else getattr(receipt, 'status', 0)
                    
                    if status == 1:
                        print("✅ 购买成功")
                        import time
                        time.sleep(1)
                        self.load_player_data()
                        self.load_market_weapons()
                    else:
                        print(f"❌ 购买交易失败，状态码: {status}")
                except TimeoutError:
                    print("⏳ 交易正在确认中，请等待...")
                    # 即使超时也尝试刷新数据
                    self.load_player_data()
                    self.load_market_weapons()
            except Exception as tx_error:
                print(f"交易发送失败: {tx_error}")
                # 尝试使用不同的参数重试一次
                print("尝试使用不同参数重试...")
                try:
                    retry_tx = self.contract.functions.purchaseWeapon(weapon['id']).build_transaction({
                        'from': self.account,
                        'value': weapon['price'],
                        'gas': 800000,  # 使用更高的gas限制
                        'gasPrice': self.w3.to_wei('10', 'gwei'),  # 使用更高的gas价格
                        'nonce': nonce + 1,  # 使用下一个nonce避免冲突
                        'chainId': self.w3.eth.chain_id
                    })
                    retry_tx_hash = self.w3.eth.send_transaction(retry_tx)
                    print(f"⏳ 重试交易发送: {retry_tx_hash.hex()}")
                except Exception as retry_error:
                    print(f"重试失败: {retry_error}")
                    
        except Exception as e:
            print(f"购买失败: {str(e)}")
            # 分析错误信息
            error_str = str(e)
            print(f"错误详情: {error_str}")
            
            if "insufficient funds" in error_str.lower():
                print("错误分析：账户余额不足，请确保有足够的ETH")
            elif "cannot buy your own weapon" in error_str.lower():
                print("错误分析：不能购买自己的武器")
            elif "weapon not for sale" in error_str.lower():
                print("错误分析：武器不在出售状态")
            elif "internal error" in error_str.lower():
                print("错误分析：区块链节点内部错误")
                print("建议：")
                print("1. 重新启动Hardhat节点")
                print("2. 重新部署合约")
                print("3. 尝试再次上架武器后购买")
            else:
                print("错误分析：请检查区块链连接和合约状态")
                print("建议重新启动游戏和区块链节点")

    def list_weapon_for_sale(self, weapon):
        try:
            # 简单定价：基础 0.01 ETH * (1 + rarity.value*0.5)
            base_price_eth = 0.01 * (1 + weapon['rarity'].value * 0.5)
            price_wei = self.w3.to_wei(base_price_eth, 'ether')
            print(f"上架武器 ID {weapon['id']} 价格 {base_price_eth:.4f} ETH")
            tx = self.contract.functions.listWeaponForSale(weapon['id'], price_wei).build_transaction({
                'from': self.account,
                'gas': 250000,
                'gasPrice': self.w3.to_wei('2', 'gwei'),
                'nonce': self.w3.eth.get_transaction_count(self.account)
            })
            tx_hash = self.w3.eth.send_transaction(tx)
            print(f"⏳ 上架交易发送: {tx_hash.hex()} 等待确认...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            status = receipt.get('status', 1) if isinstance(receipt, dict) else getattr(receipt, 'status', 1)
            if status == 1:
                print("✅ 上架成功")
                self.load_player_data()
                self.load_market_weapons()
            else:
                print("❌ 上架交易失败")
        except Exception as e:
            print(f"上架失败: {e}")

    def tick_auto_refresh(self):
        # 每隔一定帧数检查是否有新区块，若有则刷新市场与玩家数据
        current_block = self.w3.eth.block_number
        if pygame.time.get_ticks() % (self.auto_refresh_interval * 10) == 0:  # 简单节流
            if current_block != self.last_refresh_block:
                self.last_refresh_block = current_block
                self.load_player_data()
                if self.game_state == 'marketplace':
                    self.load_market_weapons()

    def handle_player_movement(self):
        """处理玩家移动 (WASD / 方向键)"""
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= self.player_speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += self.player_speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= self.player_speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += self.player_speed
        # 斜向速度归一 (简单做法)
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071
        self.player_x += dx
        self.player_y += dy
        # 边界限制
        margin = 40
        self.player_x = max(margin, min(WIDTH - margin, self.player_x))
        self.player_y = max(margin + 100, min(HEIGHT - margin, self.player_y))
        self.update_player_on_grass()

    def update_player_on_grass(self):
        """检测玩家是否站在草块上并标记"""
        self.standing_grass_id = None
        for idx, grass in enumerate(self.grass_patches):
            rect = grass['rect']
            # 玩家中心在草块矩形内则视为站立
            inside = rect.collidepoint(int(self.player_x), int(self.player_y))
            grass['player_on'] = inside
            if inside:
                self.standing_grass_id = idx

    def rotate_weapon(self):
        self.angle += self.rotation_speed
        if self.angle >= 360:
            self.angle = 0

        center_x, center_y = int(self.player_x), int(self.player_y)
        weapon_length = 120
        end_x = center_x + weapon_length * math.cos(math.radians(self.angle))
        end_y = center_y + weapon_length * math.sin(math.radians(self.angle))

        current_weapon = self.get_current_weapon()
        damage = 8 * current_weapon['damage_multiplier']

        points_earned = 0

        # 使用武器尖端的圆形碰撞，提高手感，避免整条线矩形过度命中
        tip_radius = 14
        tip_rect = pygame.Rect(int(end_x - tip_radius), int(end_y - tip_radius), tip_radius * 2, tip_radius * 2)

        for grass in self.grass_patches[:]:
            if tip_rect.colliderect(grass['rect']):
                grass['health'] -= damage
                if grass['health'] <= 0:
                    self.grass_patches.remove(grass)
                    points_earned += 10

        if points_earned > 0:
            self.pending_points += points_earned
            self.score += points_earned
        self.maybe_flush_points()

    def generate_grass(self):
        """生成草地格子"""
        self.grass_patches = []
        for i in range(6):
            for j in range(6):
                x = 150 + i * 70
                y = 200 + j * 70
                self.grass_patches.append({
                    'x': x, 'y': y, 'width': 50, 'height': 50,
                    'health': 100, 'rect': pygame.Rect(x, y, 50, 50)
                })

    def get_rarity_name(self, rarity):
        names = {
            Rarity.COMMON: "普通",
            Rarity.RARE: "稀有",
            Rarity.EPIC: "史诗",
            Rarity.LEGENDARY: "传奇"
        }
        return names[rarity]
    
    def compute_price_range(self, weapon):
        """计算同稀有度武器在市场中的价格区间（以 ETH 返回）。
        返回 (min_eth, max_eth, recommended_eth)
        """
        same = [w for w in self.market_weapons if w['rarity'] == weapon['rarity'] and w['id'] != weapon['id']]
        if not same:
            base_price_eth = 0.01 * (1 + weapon['rarity'].value * 0.5)
            return (base_price_eth * 0.5, base_price_eth * 2.0, base_price_eth)
        prices = [float(self.w3.from_wei(w['price'], 'ether')) for w in same]
        min_p = min(prices)
        max_p = max(prices)
        # 推荐价格：使用中位数与基础的平均
        try:
            import statistics
            median = statistics.median(prices)
            recommended = (median + float(0.01 * (1 + weapon['rarity'].value * 0.5))) / 2
        except Exception:
            recommended = sum(prices) / len(prices)
        return (min_p, max_p, recommended)

    def open_list_modal(self, weapon):
        """打开上架弹窗，自动填充推荐价格并显示同类价格区间。"""
        self.listing_weapon = weapon
        mn, mx, rec = self.compute_price_range(weapon)
        self.listing_min_eth = mn
        self.listing_max_eth = mx
        self.listing_recommended_eth = rec
        # 自动填入推荐价格，保留 4 位小数显示
        self.listing_price_str = f"{rec:.4f}"
        self.show_listing_modal = True

    def close_listing_modal(self):
        self.show_listing_modal = False
        self.listing_weapon = None
        self.listing_price_str = ""
        self.listing_min_eth = None
        self.listing_max_eth = None
        self.listing_recommended_eth = None

    def draw_listing_modal(self, surface):
        if not self.show_listing_modal or not self.listing_weapon:
            return
        # 半透明遮罩
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        # 中央面板
        w, h = 560, 260
        rect = pygame.Rect((WIDTH - w) // 2, (HEIGHT - h) // 2, w, h)
        pygame.draw.rect(surface, PANEL, rect, border_radius=8)
        pygame.draw.rect(surface, PANEL_BORDER, rect, 2, border_radius=8)

        title = large_font.render("自定义上架价格", True, TEXT_MAIN)
        surface.blit(title, (rect.x + 16, rect.y + 12))

        info_y = rect.y + 64
        rarity_text = small_font.render(f"稀有度: {self.get_rarity_name(self.listing_weapon['rarity'])}", True, TEXT_MAIN)
        surface.blit(rarity_text, (rect.x + 20, info_y))

        range_text = small_font.render(
            f"同类价格区间: {self.listing_min_eth:.4f} ETH  -  {self.listing_max_eth:.4f} ETH", True, TEXT_DIM)
        surface.blit(range_text, (rect.x + 20, info_y + 28))

        rec_text = small_font.render(f"推荐价格: {self.listing_recommended_eth:.4f} ETH", True, SUCCESS_GREEN)
        surface.blit(rec_text, (rect.x + 20, info_y + 56))

        # 输入框
        input_box = pygame.Rect(rect.x + 20, info_y + 96, 260, 36)
        pygame.draw.rect(surface, WHITE, input_box)
        pygame.draw.rect(surface, BLACK, input_box, 2)
        inp = small_font.render(self.listing_price_str, True, BLACK)
        surface.blit(inp, (input_box.x + 8, input_box.y + 6))

        hint = small_font.render("输入价格（ETH），按 Enter 确认，Esc 取消", True, TEXT_DIM)
        surface.blit(hint, (rect.x + 300, info_y + 100))

        # 按钮
        confirm_btn = pygame.Rect(rect.x + 120, rect.y + h - 60, 140, 40)
        cancel_btn = pygame.Rect(rect.x + 280, rect.y + h - 60, 140, 40)
        pygame.draw.rect(surface, GREEN, confirm_btn)
        pygame.draw.rect(surface, BLACK, confirm_btn, 2)
        pygame.draw.rect(surface, WARNING_RED, cancel_btn)
        pygame.draw.rect(surface, BLACK, cancel_btn, 2)
        ctxt = font.render("确认上架", True, BLACK)
        ctxt2 = font.render("取消", True, BLACK)
        surface.blit(ctxt, (confirm_btn.x + 30, confirm_btn.y + 8))
        surface.blit(ctxt2, (cancel_btn.x + 50, cancel_btn.y + 8))

        # 保存按钮 rect 供事件使用
        self._listing_confirm_rect = confirm_btn
        self._listing_cancel_rect = cancel_btn

    def handle_listing_key(self, event):
        # 只处理数字、点、Backspace、Enter、Escape
        if event.key == pygame.K_ESCAPE:
            self.close_listing_modal()
            return
        if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
            self.confirm_listing()
            return
        if event.key == pygame.K_BACKSPACE:
            self.listing_price_str = self.listing_price_str[:-1]
            return
        # 允许数字、小数点
        ch = None
        if event.unicode and event.unicode.isprintable():
            ch = event.unicode
        if ch and (ch.isdigit() or ch == '.'):
            # 只保留一个小数点
            if ch == '.' and '.' in self.listing_price_str:
                return
            # 限制长度
            if len(self.listing_price_str) < 16:
                self.listing_price_str += ch

    def handle_listing_click(self, pos):
        if hasattr(self, '_listing_confirm_rect') and self._listing_confirm_rect.collidepoint(pos):
            self.confirm_listing()
            return
        if hasattr(self, '_listing_cancel_rect') and self._listing_cancel_rect.collidepoint(pos):
            self.close_listing_modal()
            return

    def confirm_listing(self):
        # 验证输入并调用链上上架
        try:
            if not self.listing_weapon:
                self.close_listing_modal()
                return
            s = self.listing_price_str.strip()
            if not s:
                print("请输入价格后再确认上架")
                return
            # 使用 Decimal 提升精度
            price_eth = Decimal(s)
            price_wei = int(price_eth * Decimal(10**18))

            wid = int(self.listing_weapon['id'])
            print(f"上架武器 {wid} 价格 {price_eth} ETH -> {price_wei} wei")
            tx = self.contract.functions.listWeaponForSale(wid, price_wei).build_transaction({
                'from': self.account,
                'gas': 300000,
                'gasPrice': self.w3.to_wei('2', 'gwei'),
                'nonce': self.w3.eth.get_transaction_count(self.account)
            })
            tx_hash = self.w3.eth.send_transaction(tx)
            print(f"⏳ 上架交易发送: {tx_hash.hex()} 等待确认...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            status = receipt.get('status', 0) if isinstance(receipt, dict) else getattr(receipt, 'status', 0)
            if status == 1:
                print("✅ 上架成功")
                self.close_listing_modal()
                self.load_player_data()
                self.load_market_weapons()
            else:
                print("❌ 上架交易失败")
        except Exception as e:
            print(f"上架失败: {e}")
    
    def get_condition_name(self, condition):
        # 支持传入 wear (float) 或 Condition 枚举
        if isinstance(condition, (float, int)):
            wear = float(condition)
            grade = self.wear_to_condition_grade(wear)
            names = {
                Condition.S: "S级（极佳）",
                Condition.A: "A级（优良）",
                Condition.B: "B级（良好）",
                Condition.C: "C级（普通）",
                Condition.D: "D级（磨损）",
                Condition.E: "E级（严重磨损）",
            }
            return f"{names.get(grade,'未知')} {wear:.10f}"
        else:
            names = {
                Condition.S: "S级（极佳）",
                Condition.A: "A级（优良）",
                Condition.B: "B级（良好）",
                Condition.C: "C级（普通）",
                Condition.D: "D级（磨损）",
                Condition.E: "E级（严重磨损）",
            }
            return names.get(condition, "未知")

    def compute_wear_seed(self, weapon_id, owner_addr):
        """根据 weapon_id 与 owner 地址生成确定性的 wear（10位小数）。"""
        try:
            import hashlib
            seed = f"{weapon_id}-{owner_addr}".encode()
            h = hashlib.sha256(seed).digest()
            val = int.from_bytes(h, 'big') % (10**10)
            return val / 1e10
        except Exception:
            return round(random.random(), 10)

    def wear_to_condition_grade(self, wear: float) -> Condition:
        """将 wear(0..1) 映射到粗糙等级（枚举），wear 越小表示武器越新。"""
        # 目标概率分布 (S, A, B, C, D, E) = (0.05, 0.10, 0.15, 0.20, 0.25, 0.25)
        # 对应累积阈值: 0.05, 0.15, 0.30, 0.50, 0.75, 1.00
        if wear < 0.05:
            return Condition.S
        if wear < 0.15:
            return Condition.A
        if wear < 0.30:
            return Condition.B
        if wear < 0.50:
            return Condition.C
        if wear < 0.75:
            return Condition.D
        return Condition.E

    def mint_random_weapon(self):
        """铸造一个随机新武器(需要一定金币)"""
        try:
            # 需求金币阈值
            required_coins = 20
            if self.coins < required_coins:
                print(f"金币不足，需 {required_coins}，当前 {self.coins}")
                return
            # 随机稀有度（倾斜概率）
            roll = random.random()
            if roll < 0.60:
                rarity = Rarity.COMMON
            elif roll < 0.85:
                rarity = Rarity.RARE
            elif roll < 0.97:
                rarity = Rarity.EPIC
            else:
                rarity = Rarity.LEGENDARY
            base_names = {
                Rarity.COMMON: ["Common Cutter", "Simple Sickle"],
                Rarity.RARE: ["Rare Sickle", "Polished Blade"],
                Rarity.EPIC: ["Epic Blade", "Runed Sword"],
                Rarity.LEGENDARY: ["Legendary Axe", "Phoenix Cutter"]
            }
            name = random.choice(base_names[rarity])
            # 伤害乘数整数存储（100 基础）
            damage_multiplier = {
                Rarity.COMMON: 100,
                Rarity.RARE: 120,
                Rarity.EPIC: 150,
                Rarity.LEGENDARY: 190
            }[rarity]
            print(f"铸造武器: {name} 稀有度 {rarity.name} 伤害 {damage_multiplier}")
            tx = self.contract.functions.mintWeapon(self.account, name, rarity.value, damage_multiplier).build_transaction({
                'from': self.account,
                'gas': 350000,
                'gasPrice': self.w3.to_wei('2', 'gwei'),
                'nonce': self.w3.eth.get_transaction_count(self.account)
            })
            tx_hash = self.w3.eth.send_transaction(tx)
            print(f"⏳ 铸造交易发送: {tx_hash.hex()} 等待确认...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            status = receipt.get('status', 1) if isinstance(receipt, dict) else getattr(receipt, 'status', 1)
            if status == 1:
                print("✅ 铸造成功")
                self.load_player_data()
                # 不减少链上金币（合约未实现扣除），可在未来扩展。这里仅提示。
                print("提示: 合约暂未扣减金币，后续可添加 spend 函数。")
            else:
                print("❌ 铸造交易失败")
        except Exception as e:
            print(f"铸造失败: {e}")


def main():
    game = BlockchainGame()
    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                # 若上架弹窗打开，则由弹窗处理键盘事件
                if game.show_listing_modal:
                    game.handle_listing_key(event)
                else:
                    if event.key == pygame.K_m:
                        game.game_state = "marketplace"
                    elif event.key == pygame.K_i:
                        game.game_state = "inventory"
                        game.load_player_data()  # 刷新数据
                    elif event.key == pygame.K_r:
                        game.generate_grass()
                    elif event.key == pygame.K_ESCAPE:
                        game.game_state = "playing"
                    elif event.key == pygame.K_n:
                        game.mint_random_weapon()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # 若弹窗打开则由弹窗处理点击
                    if game.show_listing_modal:
                        game.handle_listing_click(event.pos)
                    else:
                        game.handle_click(event.pos)

        # 旋转除草
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            game.rotate_weapon()
        # 玩家移动
        game.handle_player_movement()
        # 定时尝试 flush（在不旋转时也能触发）
        game.maybe_flush_points()
        game.tick_auto_refresh()

        game.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()