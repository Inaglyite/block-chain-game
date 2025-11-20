# -*- coding: utf-8 -*-
import pygame
import sys
import random
import math
import json
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
            self.score, self.coins = self.contract.functions.getPlayerStats(self.account).call()
            weapon_ids = self.contract.functions.getUserWeapons(self.account).call()
            self.weapons = []

            for weapon_id in weapon_ids:
                weapon_data = self.contract.functions.getWeaponDetails(weapon_id).call()
                display_name = self.get_weapon_display_name(
                    weapon_data[1],
                    Rarity(weapon_data[2])
                )
                weapon = {
                    'id': weapon_data[0],
                    'name': display_name,
                    'original_name': weapon_data[1],
                    'rarity': Rarity(weapon_data[2]),
                    'damage_multiplier': weapon_data[3] / 100.0,
                    'owner': weapon_data[4],
                    'price': weapon_data[5],
                    'for_sale': weapon_data[6]
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
            self.market_weapons = []
            for w in sale_list:
                display_name = self.get_weapon_display_name(w[1], Rarity(w[2]))
                self.market_weapons.append({
                    'id': w[0],
                    'name': display_name,
                    'original_name': w[1],
                    'rarity': Rarity(w[2]),
                    'damage_multiplier': w[3] / 100.0,
                    'owner': w[4],
                    'price': w[5],
                    'for_sale': w[6]
                })
            # 排序：价格低的排前，稀有度高优先
            self.market_weapons.sort(key=lambda w: (w['price'], -w['rarity'].value))
        except Exception as e:
            print(f"加载市场数据失败: {e}")

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
        """绘制游戏界面"""
        surface.fill(WHITE)

        # 标题
        title = large_font.render("区块链旋转除草NFT游戏 - 真实链上版本", True, BLACK)
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 20))

        # 区块链状态
        block_text = font.render(f"区块链高度: {self.w3.eth.block_number} | 合约: {self.contract_address[:10]}...",
                                 True, BLUE)
        surface.blit(block_text, (20, 70))

        # 玩家信息
        player_text = font.render(
            f"玩家: {self.account[:10]}... | 分数: {self.score} (+{self.pending_points}*) | 金币: {self.coins} | 武器: {len(self.weapons)}", True,
            BLACK)
        surface.blit(player_text, (20, 100))
        if self.pending_points > 0:
            hint = small_font.render("*待上链", True, RED)
            surface.blit(hint, (20 + player_text.get_width() - 60, 120))

        if self.game_state == "playing":
            self.draw_game(surface)
        elif self.game_state == "marketplace":
            self.draw_marketplace(surface)
        elif self.game_state == "inventory":
            self.draw_inventory(surface)

        # 控制说明
        controls = small_font.render("空格键: 旋转除草 | N: 铸造新武器 | M: 市场 | I: 背包 | R: 重置草地 | ESC: 返回", True, BLACK)
        surface.blit(controls, (20, HEIGHT - 30))

    def draw_game(self, surface):
        """绘制游戏画面"""
        # 绘制草地
        for grass in self.grass_patches:
            color = GREEN if grass['health'] > 50 else LIGHT_GREEN
            # 如果玩家站在此草块，进行高亮描边
            if grass.get('player_on'):
                pygame.draw.rect(surface, GOLD, grass['rect'])
            else:
                pygame.draw.rect(surface, color, grass['rect'])
            pygame.draw.rect(surface, BLACK, grass['rect'], 1)

            # 生命条
            health_width = 50 * (grass['health'] / 100)
            health_rect = pygame.Rect(grass['x'], grass['y'] - 5, health_width, 3)
            pygame.draw.rect(surface, RED, health_rect)

        # 绘制除草刀
        center_x, center_y = int(self.player_x), int(self.player_y)
        weapon_length = 120

        current_weapon = self.get_current_weapon()
        weapon_color = self.get_rarity_color(current_weapon['rarity']) if current_weapon else GRAY

        end_x = center_x + weapon_length * math.cos(math.radians(self.angle))
        end_y = center_y + weapon_length * math.sin(math.radians(self.angle))

        pygame.draw.line(surface, weapon_color, (center_x, center_y), (end_x, end_y), 8)
        pygame.draw.circle(surface, BROWN, (center_x, center_y), 12)

        # 绘制玩家（大圆，区分中心点）
        pygame.draw.circle(surface, (80, 80, 200), (center_x, center_y), self.player_radius)
        pygame.draw.circle(surface, (255, 255, 255), (center_x, center_y), self.player_radius - 10)

        # 玩家所站草块提示
        if self.standing_grass_id is not None:
            stand_tip = small_font.render("站在草块上: +伤害判定中心", True, DARK_GREEN)
            surface.blit(stand_tip, (WIDTH - stand_tip.get_width() - 20, 120))

        # 武器信息
        if current_weapon:
            weapon_text = font.render(
                f"当前武器: {current_weapon['name']} (伤害: x{current_weapon['damage_multiplier']:.1f})", True,
                weapon_color)
            surface.blit(weapon_text, (WIDTH - 350, 150))

        # 提示
        tip = font.render("按住空格键旋转除草，分数将记录到区块链!", True, DARK_GREEN)
        surface.blit(tip, (WIDTH // 2 - tip.get_width() // 2, HEIGHT - 80))

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
            pygame.draw.rect(surface, BLACK, card_rect, 3)

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
            surface.blit(status_text, (400, y_pos + 45))

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
                if equip_rect.collidepoint(pos):
                    self.current_weapon_index = i
                    return
                if list_rect.collidepoint(pos) and not weapon['for_sale']:
                    self.list_weapon_for_sale(weapon)
                    return

    def purchase_weapon(self, weapon):
        try:
            print(f"尝试购买武器 ID {weapon['id']} 价格 {self.w3.from_wei(weapon['price'], 'ether')} ETH")
            tx = self.contract.functions.purchaseWeapon(weapon['id']).build_transaction({
                'from': self.account,
                'value': weapon['price'],
                'gas': 300000,
                'gasPrice': self.w3.to_wei('2', 'gwei'),
                'nonce': self.w3.eth.get_transaction_count(self.account)
            })
            tx_hash = self.w3.eth.send_transaction(tx)
            print(f"⏳ 购买交易发送: {tx_hash.hex()} 等待确认...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            status = receipt.get('status', 1) if isinstance(receipt, dict) else getattr(receipt, 'status', 1)
            if status == 1:
                print("✅ 购买成功")
                self.load_player_data()
                self.load_market_weapons()
            else:
                print("❌ 购买交易失败")
        except Exception as e:
            print(f"购买失败: {e}")

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