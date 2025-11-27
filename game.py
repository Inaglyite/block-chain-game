# -*- coding: utf-8 -*-
import pygame
import sys
import random
import math
import json
import os
import pytmx
from pytmx.util_pygame import load_pygame
from web3 import Web3
from enum import Enum
import logging

# 初始化pygame
pygame.init()
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(message)s")

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
pygame.display.set_caption("区块链��转除草NFT游戏")

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
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TMX_PATH = os.path.join(BASE_DIR, "kenney_roguelike-rpg-pack", "Map", "sample_map.tmx")


class TileMap:
    def __init__(self, tmx_path: str):
        if not os.path.exists(tmx_path):
            raise FileNotFoundError(f"未找到 TMX 地图: {tmx_path}")
        self.tmx_data = load_pygame(tmx_path)
        self.pixel_width = self.tmx_data.width * self.tmx_data.tilewidth
        self.pixel_height = self.tmx_data.height * self.tmx_data.tileheight
        self.surface = pygame.Surface((self.pixel_width, self.pixel_height), pygame.SRCALPHA).convert_alpha()
        self._render_layers()

    def _render_layers(self):
        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer.tiles():
                    if isinstance(gid, pygame.Surface):
                        tile = gid
                    else:
                        try:
                            tile = self.tmx_data.get_tile_image_by_gid(int(gid)) if gid else None
                        except (TypeError, ValueError):
                            continue
                    if tile:
                        self.surface.blit(
                            tile,
                            (x * self.tmx_data.tilewidth, y * self.tmx_data.tileheight)
                        )

    def draw(self, target_surface: pygame.Surface, camera_rect: pygame.Rect):
        target_surface.blit(self.surface, (0, 0), camera_rect)

    def sample_color(self, x: float, y: float):
        if 0 <= x < self.pixel_width and 0 <= y < self.pixel_height:
            return self.surface.get_at((int(x), int(y)))
        return None

    def looks_like_grass(self, x: float, y: float) -> bool:
        color = self.sample_color(x, y)
        if color is None or color.a == 0:
            return False
        return color.g > color.r + 10 and color.g > color.b + 10


class ProceduralTileMap:
    def __init__(self, width: int, height: int, tile_size: int = 32):
        self.pixel_width = width
        self.pixel_height = height
        self.tilewidth = tile_size
        self.tileheight = tile_size
        self.surface = pygame.Surface((self.pixel_width, self.pixel_height), pygame.SRCALPHA).convert_alpha()
        self._generate_pattern()

    def _generate_pattern(self):
        grass_colors = [(46, 142, 73), (38, 122, 60), (64, 160, 90)]
        water_colors = [(64, 115, 158), (52, 101, 140)]
        dirt_color = (130, 95, 60)
        for y in range(0, self.pixel_height, self.tileheight):
            for x in range(0, self.pixel_width, self.tilewidth):
                roll = random.random()
                if roll < 0.75:
                    color = random.choice(grass_colors)
                elif roll < 0.90:
                    color = dirt_color
                else:
                    color = random.choice(water_colors)
                pygame.draw.rect(self.surface, color, pygame.Rect(x, y, self.tilewidth, self.tileheight))

    def draw(self, target_surface: pygame.Surface, camera_rect: pygame.Rect):
        target_surface.blit(self.surface, (0, 0), camera_rect)

    def sample_color(self, x: float, y: float):
        if 0 <= x < self.pixel_width and 0 <= y < self.pixel_height:
            return self.surface.get_at((int(x), int(y)))
        return None

    def looks_like_grass(self, x: float, y: float) -> bool:
        color = self.sample_color(x, y)
        if color is None or color.a == 0:
            return False
        return color.g > color.r + 10 and color.g > color.b + 10


# 武器稀有度
class Rarity(Enum):
    COMMON = 0
    RARE = 1
    EPIC = 2
    LEGENDARY = 3


class BlockchainGame:
    def __init__(self):
        self.blockchain_available = False
        self.offline_reason = ""
        self.w3 = None
        self.contract = None
        self.account = "0x0000000000000000000000000000000000000000"
        self.contract_address = "N/A"
        self.rpc_url = os.getenv("RPC_URL", "http://127.0.0.1:8545")
        self.setup_blockchain()
        self.weapons = []
        self.current_weapon_index = 0
        self.score = 0
        self.coins = 0
        self.grass_patches = []
        self.angle = 0
        self.rotation_speed = 5
        self.game_state = "playing"
        self.inventory_selection = 0
        self.market_selection = 0
        self.market_weapons = []
        self.last_refresh_block = 0
        self.auto_refresh_interval = 30  # 每30帧自动尝试刷新（≈0.5秒）
        self.pending_points = 0  # 尚未上链的累计分数
        self.last_flush_ms = 0    # 上一次写链时间戳
        self.flush_interval_ms = 3000  # 每3秒尝试上链一次
        # 玩家属性
        self.player_x = 0
        self.player_y = 0
        self.player_speed = 6
        self.player_radius = 5
        self.weapon_length = 70
        self.standing_grass_id = None  # 当前所站草块索引
        self.tile_map_error = None

        try:
            self.tile_map = TileMap(DEFAULT_TMX_PATH)
        except Exception as err:
            self.tile_map_error = str(err)
            print(f"⚠️ 无法加载 TMX 地图，使用内置程序化地图: {err}")
            fallback_size = 1600
            self.tile_map = ProceduralTileMap(fallback_size, fallback_size)
        self.world_bounds = pygame.Rect(0, 0, self.tile_map.pixel_width, self.tile_map.pixel_height)
        self.camera_zoom = 2.5
        camera_w = max(200, int(WIDTH / self.camera_zoom))
        camera_h = max(150, int(HEIGHT / self.camera_zoom))
        self.camera_rect = pygame.Rect(0, 0, camera_w, camera_h)
        self.scene_surface = pygame.Surface((camera_w, camera_h), pygame.SRCALPHA).convert_alpha()
        self.player_x = self.world_bounds.width // 2
        self.player_y = self.world_bounds.height // 2
        self.update_camera()

        self.load_player_data()
        self.generate_grass()
        self.load_market_weapons()
        self.input_cooldown_ms = 200
        self.last_state_toggle = 0

        print("游戏初始化完成!")

    def set_game_state(self, state):
        self.game_state = state
        self.last_state_toggle = pygame.time.get_ticks()

    def toggle_inventory(self):
        now = pygame.time.get_ticks()
        if now - self.last_state_toggle < self.input_cooldown_ms:
            return
        if self.game_state == "inventory":
            self.set_game_state("playing")
        else:
            self.inventory_selection = 0
            self.set_game_state("inventory")

    def toggle_market(self):
        now = pygame.time.get_ticks()
        if now - self.last_state_toggle < self.input_cooldown_ms:
            return
        if self.game_state == "marketplace":
            self.set_game_state("playing")
        else:
            self.market_selection = 0
            self.set_game_state("marketplace")

    def _load_json_with_fallback(self, candidates, description):
        """从多个候选路径中加载 JSON，返回 (数据, 使用的路径)"""
        errors = []
        for path in candidates:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f), path
            except FileNotFoundError:
                errors.append(f"{path}: 文件不存在")
            except json.JSONDecodeError as err:
                errors.append(f"{path}: JSON 解析失败 ({err})")
        detail = " | ".join(errors)
        raise FileNotFoundError(f"{description} 未找到，已尝试: {', '.join(candidates)}. {detail}")

    def _resolve_contract_address(self, candidates):
        """寻找包含已部署合约地址的文件，返回 (checksum 地址, 合约信息, 路径)"""
        errors = []
        for path in candidates:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    info = json.load(f)
            except FileNotFoundError:
                errors.append(f"{path}: 文件不存在")
                continue
            raw_address = info.get('address')
            if not raw_address:
                errors.append(f"{path}: 缺少 address 字段")
                continue
            try:
                checksum = self.w3.to_checksum_address(raw_address)
            except Exception as err:
                errors.append(f"{path}: 地址无效 ({raw_address}) -> {err}")
                continue
            code = self.w3.eth.get_code(checksum)
            if code and any(byte != 0 for byte in code):
                return checksum, info, path
            errors.append(f"{path}: 地址 {raw_address} 上没有已部署合约")
        detail = " | ".join(errors)
        raise RuntimeError(f"无法找到可用的合约地址。请重新部署合约。详情: {detail}")

    def setup_blockchain(self):
        """设置区块链连接"""
        try:
            print(f"🔌 正在连接区块链 RPC: {self.rpc_url}")
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url, request_kwargs={"timeout": 5}))
            try:
                block_number = self.w3.eth.block_number
                print(f"✅ 连接到区块链网络，最新区块: {block_number}")
            except Exception as block_err:
                raise RuntimeError(f"无法获取区块高度: {block_err}") from block_err
            abi_data, abi_path = self._load_json_with_fallback(
                ["WeedCutterNFT.json", "scripts/WeedCutterNFT.json"],
                "合约 ABI"
            )
            self.contract_abi = abi_data['abi']
            if abi_path != "WeedCutterNFT.json":
                print(f"⚠️ 使用备用 ABI 文件: {abi_path}")

            self.contract_address, contract_info, info_path = self._resolve_contract_address(
                ["contract-info.json", "scripts/contract-info.json"]
            )
            if info_path != "contract-info.json":
                print(f"⚠️ 主目录 contract-info.json 未同步，已使用 {info_path}")

            self.contract = self.w3.eth.contract(
                address=self.contract_address,
                abi=self.contract_abi
            )

            self.account = self.w3.eth.accounts[0]
            print(f"使用账户: {self.account}")

            self.blockchain_available = True  # 成功连接后标记为可用

        except Exception as e:
            import traceback
            print(f"❌ 区块链设置失败，进入离线模式: {e}")
            traceback.print_exc()
            self.blockchain_available = False
            self.offline_reason = f"{e} (RPC: {self.rpc_url})"
            print("提示: 请确保 Hardhat 节点运行并部署合约后再重开游戏。")

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

    def get_current_weapon(self):
        # 没有链上武器时提供默认新手武器，避免渲染阶段崩溃
        if not self.weapons:
            return {
                'id': -1,
                'name': "新手除草刀",
                'original_name': "Starter Cutter",
                'rarity': Rarity.COMMON,
                'damage_multiplier': 1.0,
                'owner': self.account,
                'price': 0,
                'for_sale': False
            }
        self.current_weapon_index %= len(self.weapons)
        return self.weapons[self.current_weapon_index]

    def get_rarity_color(self, rarity: Rarity):
        palette = {
            Rarity.COMMON: GRAY,
            Rarity.RARE: BLUE,
            Rarity.EPIC: PURPLE,
            Rarity.LEGENDARY: GOLD
        }
        return palette.get(rarity, GRAY)

    def load_player_data(self):
        """从区块链加载玩家数据"""
        if not self.blockchain_available:
            self.score = 0
            self.coins = 0
            self.weapons = []
            return
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
        if not self.blockchain_available:
            self.market_weapons = []
            return
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
        if not self.blockchain_available:
            self.score += points
            return
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

    def update_camera(self):
        self.camera_rect.center = (int(self.player_x), int(self.player_y))
        self.camera_rect.clamp_ip(self.world_bounds)

    def world_point_to_screen(self, x: float, y: float):
        return int(x - self.camera_rect.left), int(y - self.camera_rect.top)

    def world_rect_to_screen(self, rect: pygame.Rect):
        return pygame.Rect(
            rect.x - self.camera_rect.left,
            rect.y - self.camera_rect.top,
            rect.width,
            rect.height
        )

    def draw_hud(self, surface, translucent: bool):
        if translucent:
            top_panel = pygame.Surface((WIDTH, 140), pygame.SRCALPHA)
            top_panel.fill((255, 255, 255, 215))
            surface.blit(top_panel, (0, 0))
        title = large_font.render("区块链旋转除草NFT游戏 - 真实链上版本", True, BLACK)
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 20))

        player_text = font.render(
            f"玩家: {self.account[:10]}... | 分数: {self.score} (+{self.pending_points}*) | 金币: {self.coins} | 武器: {len(self.weapons)}",
            True,
            BLACK
        ) if self.blockchain_available else font.render(
            f"离线模式 | 分数: {self.score} (+{self.pending_points}*) | 金币: {self.coins}",
            True,
            BLACK
        )
        surface.blit(player_text, (20, 100))
        if not self.blockchain_available and self.offline_reason:
            warn = small_font.render(f"离线原因: {self.offline_reason}", True, RED)
            surface.blit(warn, (20, 130))
        if self.tile_map_error:
            map_warn = small_font.render(f"地图加载失败: {self.tile_map_error}", True, RED)
            surface.blit(map_warn, (20, 150))

        if self.pending_points > 0:
            hint = small_font.render("*待上链", True, RED)
            surface.blit(hint, (20 + player_text.get_width() - 60, 120))

        if self.standing_grass_id is not None:
            stand_tip = small_font.render("站在草块上: 旋转命中判定更稳定", True, DARK_GREEN)
            surface.blit(stand_tip, (WIDTH - stand_tip.get_width() - 20, 70))

        controls = small_font.render(
            "WASD/方向键: 移动 | 空格: 旋转除草 | N: 铸造 | M: 市场 | I: 背包 | R: 重置草地 | ESC: 返回",
            True,
            BLACK
        )
        if translucent:
            bottom_panel = pygame.Surface((WIDTH, 30), pygame.SRCALPHA)
            bottom_panel.fill((255, 255, 255, 200))
            surface.blit(bottom_panel, (0, HEIGHT - 30))
        surface.blit(controls, (20, HEIGHT - 25))

        block_text = font.render(
            f"区块链高度: {self.w3.eth.block_number} | 合约: {self.contract_address[:10]}...",
            True,
            BLUE
        ) if self.blockchain_available else font.render("离线模式 - 未连接区块链", True, RED)
        surface.blit(block_text, (WIDTH - block_text.get_width() - 20, 10))

    def draw(self, surface):
        if self.game_state == "playing":
            self.draw_game(surface)
        elif self.game_state == "marketplace":
            surface.fill(WHITE)
            self.draw_marketplace(surface)
        elif self.game_state == "inventory":
            surface.fill(WHITE)
            self.draw_inventory(surface)
        self.draw_hud(surface, translucent=(self.game_state == "playing"))

    def draw_inventory(self, surface):
        title = large_font.render("背包 - 已拥有武器", True, BLACK)
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 60))
        if not self.weapons:
            empty = font.render("暂无武器，去市场收集吧!", True, RED)
            surface.blit(empty, (WIDTH // 2 - empty.get_width() // 2, HEIGHT // 2))
            return
        start_y = 140
        line_height = 40
        max_visible = 10
        offset = max(0, self.inventory_selection - max_visible + 1)
        for idx in range(offset, min(len(self.weapons), offset + max_visible)):
            weapon = self.weapons[idx]
            y = start_y + (idx - offset) * line_height
            color = self.get_rarity_color(weapon['rarity'])
            text = font.render(
                f"#{weapon['id']:02d} {weapon['name']} | 稀有度: {weapon['rarity'].name} | 伤害x{weapon['damage_multiplier']:.1f}",
                True,
                color
            )
            surface.blit(text, (120, y))
            if idx == self.inventory_selection:
                pygame.draw.rect(surface, GOLD, pygame.Rect(100, y - 5, WIDTH - 200, line_height), 2)
        hint = small_font.render("↑↓ 选择 | Enter 切换武器 | I 返回游戏", True, BLACK)
        surface.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 80))

    def draw_marketplace(self, surface):
        title = large_font.render("市场 - 链上武器交易所", True, BLACK)
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 60))
        if not self.market_weapons:
            empty = font.render("当前没有上架的武器，稍后再来!", True, RED)
            surface.blit(empty, (WIDTH // 2 - empty.get_width() // 2, HEIGHT // 2))
            return
        start_y = 140
        line_height = 40
        max_visible = 10
        offset = max(0, self.market_selection - max_visible + 1)
        for idx in range(offset, min(len(self.market_weapons), offset + max_visible)):
            weapon = self.market_weapons[idx]
            y = start_y + (idx - offset) * line_height
            color = self.get_rarity_color(weapon['rarity'])
            text = font.render(
                f"#{weapon['id']:02d} {weapon['name']} | 稀有度: {weapon['rarity'].name} | 价格: {weapon['price']} | 持有者: {weapon['owner'][:10]}...",
                True,
                color
            )
            surface.blit(text, (80, y))
            if idx == self.market_selection:
                pygame.draw.rect(surface, BLUE, pygame.Rect(60, y - 5, WIDTH - 120, line_height), 2)
        hint = small_font.render("↑↓ 选择 | Enter 购买 (占位) | M 返回游戏", True, BLACK)
        surface.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 80))

    def handle_inventory_input(self, event):
        if not self.weapons:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_i:
                self.toggle_inventory()
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.inventory_selection = max(0, self.inventory_selection - 1)
            elif event.key == pygame.K_DOWN:
                self.inventory_selection = min(len(self.weapons) - 1, self.inventory_selection + 1)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.current_weapon_index = self.inventory_selection
            elif event.key == pygame.K_i:
                self.toggle_inventory()

    def handle_market_input(self, event):
        if not self.market_weapons:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                self.toggle_market()
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.market_selection = max(0, self.market_selection - 1)
            elif event.key == pygame.K_DOWN:
                self.market_selection = min(len(self.market_weapons) - 1, self.market_selection + 1)
            elif event.key == pygame.K_m:
                self.toggle_market()

    def generate_grass(self):
        """生成草地格子"""
        self.grass_patches = []
        patch_size = 18
        target = 150
        attempts = 0
        max_attempts = target * 40
        while len(self.grass_patches) < target and attempts < max_attempts:
            attempts += 1
            x = random.randint(0, max(1, self.world_bounds.width - patch_size))
            y = random.randint(100, max(100, self.world_bounds.height - patch_size))
            center_x = x + patch_size // 2
            center_y = y + patch_size // 2
            if not self.tile_map.looks_like_grass(center_x, center_y):
                continue
            rect = pygame.Rect(x, y, patch_size, patch_size)
            if any(rect.colliderect(existing['rect']) for existing in self.grass_patches):
                continue
            self.grass_patches.append({
                'x': x,
                'y': y,
                'width': patch_size,
                'height': patch_size,
                'health': 100,
                'rect': rect,
                'player_on': False
            })
        if not self.grass_patches:
            self._generate_default_grass_grid()
        self.update_player_on_grass()

    def _generate_default_grass_grid(self):
        patch_size = 18
        spacing = 4
        grid = 7
        start_x = int(self.player_x) - (grid // 2) * (patch_size + spacing)
        start_y = int(self.player_y) - (grid // 2) * (patch_size + spacing)
        start_x = max(0, min(self.world_bounds.width - grid * (patch_size + spacing), start_x))
        start_y = max(0, min(self.world_bounds.height - grid * (patch_size + spacing), start_y))
        self.grass_patches = []
        for i in range(grid):
            for j in range(grid):
                x = start_x + i * (patch_size + spacing)
                y = start_y + j * (patch_size + spacing)
                rect = pygame.Rect(x, y, patch_size, patch_size)
                self.grass_patches.append({
                    'x': x,
                    'y': y,
                    'width': patch_size,
                    'height': patch_size,
                    'health': 100,
                    'rect': rect,
                    'player_on': False
                })

    def handle_player_movement(self):
        if self.game_state != "playing":
            return
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
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071
        self.player_x = max(self.player_radius, min(self.world_bounds.width - self.player_radius, self.player_x + dx))
        self.player_y = max(self.player_radius, min(self.world_bounds.height - self.player_radius, self.player_y + dy))
        self.update_camera()
        self.update_player_on_grass()

    def update_player_on_grass(self):
        self.standing_grass_id = None
        for idx, grass in enumerate(self.grass_patches):
            inside = grass['rect'].collidepoint(int(self.player_x), int(self.player_y))
            grass['player_on'] = inside
            if inside:
                self.standing_grass_id = idx

    def rotate_weapon(self):
        if self.game_state != "playing":
            return
        self.angle = (self.angle + self.rotation_speed) % 360
        weapon = self.get_current_weapon()
        multiplier = weapon['damage_multiplier'] if weapon else 1.0
        damage = 8 * multiplier
        tip_radius = 14
        radians_angle = math.radians(self.angle)
        tip_x = self.player_x + self.weapon_length * math.cos(radians_angle)
        tip_y = self.player_y + self.weapon_length * math.sin(radians_angle)
        tip_rect = pygame.Rect(int(tip_x - tip_radius), int(tip_y - tip_radius), tip_radius * 2, tip_radius * 2)
        points_earned = 0
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

    def draw_game(self, surface):
        self.scene_surface.fill((0, 0, 0, 0))
        if self.tile_map:
            self.tile_map.draw(self.scene_surface, self.camera_rect)
        for grass in self.grass_patches:
            rect = self.world_rect_to_screen(grass['rect'])
            color = GREEN if grass['health'] > 50 else LIGHT_GREEN
            if grass.get('player_on'):
                pygame.draw.rect(self.scene_surface, GOLD, rect)
            else:
                pygame.draw.rect(self.scene_surface, color, rect)
            pygame.draw.rect(self.scene_surface, BLACK, rect, 1)
            if grass['health'] > 0:
                bar_width = int(rect.width * (grass['health'] / 100))
                if bar_width > 0:
                    bar = pygame.Rect(rect.x, rect.y - 4, bar_width, 3)
                    pygame.draw.rect(self.scene_surface, RED, bar)
        player_pos = self.world_point_to_screen(self.player_x, self.player_y)
        pygame.draw.circle(self.scene_surface, (80, 80, 200), player_pos, self.player_radius)
        pygame.draw.circle(self.scene_surface, (255, 255, 255), player_pos, max(2, self.player_radius - 8))
        weapon = self.get_current_weapon()
        if weapon:
            radians_angle = math.radians(self.angle)
            tip_x = self.player_x + self.weapon_length * math.cos(radians_angle)
            tip_y = self.player_y + self.weapon_length * math.sin(radians_angle)
            weapon_tip = self.world_point_to_screen(tip_x, tip_y)
            pygame.draw.line(self.scene_surface, self.get_rarity_color(weapon['rarity']), player_pos, weapon_tip, 6)
            pygame.draw.circle(self.scene_surface, BROWN, player_pos, max(6, self.player_radius // 2))
        if self.scene_surface.get_size() != (WIDTH, HEIGHT):
            scaled = pygame.transform.smoothscale(self.scene_surface, (WIDTH, HEIGHT))
            surface.blit(scaled, (0, 0))
        else:
            surface.blit(self.scene_surface, (0, 0))

    def tick_auto_refresh(self):
        if not self.blockchain_available or not self.w3:
            return
        now = pygame.time.get_ticks()
        if now - getattr(self, 'last_auto_refresh_ms', 0) < 500:
            return
        self.last_auto_refresh_ms = now
        try:
            current_block = self.w3.eth.block_number
        except Exception:
            return
        if current_block != self.last_refresh_block:
            self.last_refresh_block = current_block
            self.load_player_data()
            if self.game_state == "marketplace":
                self.load_market_weapons()

    def mint_random_weapon(self):
        if not self.blockchain_available:
            print("⚠️ 离线模式无法铸造武器")
            return
        required_coins = 20
        if self.coins < required_coins:
            print(f"金币不足，需 {required_coins}，当前 {self.coins}")
            return
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
        damage_multiplier = {
            Rarity.COMMON: 100,
            Rarity.RARE: 120,
            Rarity.EPIC: 150,
            Rarity.LEGENDARY: 190
        }[rarity]
        try:
            tx = self.contract.functions.mintWeapon(
                self.account,
                name,
                rarity.value,
                damage_multiplier
            ).build_transaction({
                'from': self.account,
                'gas': 350000,
                'gasPrice': self.w3.to_wei('2', 'gwei'),
                'nonce': self.w3.eth.get_transaction_count(self.account)
            })
            tx_hash = self.w3.eth.send_transaction(tx)
            print(f"⏳ 铸造交易发送: {tx_hash.hex()} 等待确认...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            status = getattr(receipt, 'status', 1)
            if status == 1:
                print("✅ 铸造成功")
                self.load_player_data()
            else:
                print("❌ 铸造交易失败")
        except Exception as err:
            print(f"铸造失败: {err}")

    def purchase_weapon(self, weapon):
        if not self.blockchain_available:
            print("⚠️ 离线模式无法购买武器")
            return
        try:
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
            status = getattr(receipt, 'status', 1)
            if status == 1:
                print("✅ 购买成功")
                self.load_player_data()
                self.load_market_weapons()
            else:
                print("❌ 购买交易失败")
        except Exception as err:
            print(f"购买失败: {err}")

    def list_weapon_for_sale(self, weapon):
        if not self.blockchain_available:
            print("⚠️ 离线模式无法上架武器")
            return
        base_price = 0.01 * (1 + weapon['rarity'].value * 0.5)
        price_wei = self.w3.to_wei(base_price, 'ether')
        try:
            tx = self.contract.functions.listWeaponForSale(weapon['id'], price_wei).build_transaction({
                'from': self.account,
                'gas': 250000,
                'gasPrice': self.w3.to_wei('2', 'gwei'),
                'nonce': self.w3.eth.get_transaction_count(self.account)
            })
            tx_hash = self.w3.eth.send_transaction(tx)
            print(f"⏳ 上架交易发送: {tx_hash.hex()} 等待确认...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            status = getattr(receipt, 'status', 1)
            if status == 1:
                print("✅ 上架成功")
                self.load_player_data()
                self.load_market_weapons()
            else:
                print("❌ 上架交易失败")
        except Exception as err:
            print(f"上架失败: {err}")


def main():
    try:
        print("🚀 开始初始化游戏...")
        game = BlockchainGame()
        print("✅ 游戏初始化完成，开始主循环...")

        clock = pygame.time.Clock()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_i:
                        game.toggle_inventory()
                    elif event.key == pygame.K_m:
                        game.toggle_market()
                    elif event.key == pygame.K_n:
                        game.mint_random_weapon()
                    elif event.key == pygame.K_r:
                        game.generate_grass()

                if game.game_state == "inventory":
                    game.handle_inventory_input(event)
                elif game.game_state == "marketplace":
                    game.handle_market_input(event)

            keys = pygame.key.get_pressed()
            if game.game_state == "playing" and keys[pygame.K_SPACE]:
                game.rotate_weapon()

            game.handle_player_movement()
            game.tick_auto_refresh()
            screen.fill(WHITE)
            game.draw(screen)
            pygame.display.flip()
            clock.tick(60)

    except Exception as e:
        print(f"❌ 游戏运行错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()
