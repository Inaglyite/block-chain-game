# -*- coding: utf-8 -*-
"""
主游戏类 - 从原game.py重构而来
"""
import pygame
import random
import math
from .config import WIDTH, HEIGHT, WHITE, GREEN, LIGHT_GREEN, BLACK, BROWN, RED, GOLD, GRAY, BLUE, PURPLE, DEFAULT_TMX_PATH
from .enums import Rarity, WeaponType
from .tilemap import TileMap, ProceduralTileMap
from .weapon import WeaponManager
from .blockchain import BlockchainManager
from .ui import UIRenderer


class BlockchainGame:
    """区块链除草游戏主类"""
    
    def __init__(self, account_index: int = 0):
        # 区块链管理器
        self.blockchain_manager = BlockchainManager(account_index)
        self.blockchain_manager.setup()
        
        # 武器管理器
        self.weapon_manager = WeaponManager()
        
        # 游戏数据
        self.weapons = []
        self.listed_weapons = []
        self.current_weapon_index = 0
        self.score = 0
        self.coins = 0
        self.grass_patches = []
        self.angle = 0
        self.base_rotation_speed = 5
        self.rotation_speed = self.base_rotation_speed
        self.current_blade_count = 1
        self.current_weapon_thickness = 8
        
        # 游戏状态
        self.game_state = "start_menu"  # 改为从开始菜单开始
        self.inventory_selection = 0
        self.market_selection = 0
        self.market_weapons = []
        self.market_last_refresh_ms = 0
        self.market_refresh_interval_ms = 3000
        self.pending_points = 0
        self.last_flush_ms = 0
        self.flush_interval_ms = 3000
        self.last_refresh_block = 0
        
        # 箱子相关
        self.case_shop_selection = 0
        self.case_inventory = {}  # case_id => amount
        self.case_inventory_selection = 0
        self.all_cases = []  # 所有可用的箱子
        self.show_case_open_result = False
        self.opened_weapon = None  # 开箱获得的武器

        # 箱子图片缓存
        self.case_sprites = {}  # case_name => surface

        # 玩家信息
        self.player_name = ""
        self.player_rank = 0
        self.total_players = 0

        # 排行榜
        self.leaderboard = []
        self.leaderboard_selection = 0

        # 个人中心
        self.profile_editing_name = False
        self.profile_name_input = ""

        # 开始菜单
        self.menu_selection = 0  # 0=个人中心, 1=开始游戏, 2=排行榜, 3=切换账户

        # 账户选择
        self.account_selection = 0
        self.all_accounts = []

        # 玩家属性
        self.player_x = 0
        self.player_y = 0
        self.player_speed = 6
        self.player_radius = 4
        self.weapon_length = 60
        self.grass_patch_size = 14
        self.standing_grass_id = None
        
        # 地图
        self.tile_map_error = None
        try:
            self.tile_map = TileMap(DEFAULT_TMX_PATH)
        except Exception as err:
            self.tile_map_error = str(err)
            print(f"⚠️ 无法加载 TMX 地图，使用内置程序化地图: {err}")
            fallback_size = 1600
            self.tile_map = ProceduralTileMap(fallback_size, fallback_size)
        
        self.world_bounds = pygame.Rect(0, 0, self.tile_map.pixel_width, self.tile_map.pixel_height)
        self.camera_zoom = 2
        self._update_camera_surface()
        
        self.player_x = self.world_bounds.width // 2
        self.player_y = self.world_bounds.height // 2
        self.update_camera()
        
        # UI
        self.input_cooldown_ms = 200
        self.last_state_toggle = 0
        self.listing_input_active = False
        self.listing_input_text = ""
        self.inventory_feedback = ""
        
        # 加载数据
        self.load_player_data()
        self.generate_grass()
        self.load_market_weapons()
        self.load_case_data()

        print("游戏初始化完成!")
    
    def set_game_state(self, state):
        """设置游戏状态"""
        self.game_state = state
        self.last_state_toggle = pygame.time.get_ticks()
    
    def toggle_inventory(self):
        """切换背包界面"""
        now = pygame.time.get_ticks()
        if now - self.last_state_toggle < self.input_cooldown_ms:
            return
        if self.game_state == "inventory":
            self.set_game_state("playing")
        else:
            self.inventory_selection = 0
            self.set_game_state("inventory")
    
    def toggle_market(self):
        """切换市场界面"""
        now = pygame.time.get_ticks()
        if now - self.last_state_toggle < self.input_cooldown_ms:
            return
        if self.game_state == "marketplace":
            self.set_game_state("playing")
        else:
            self.market_selection = 0
            self.load_market_weapons()
            self.set_game_state("marketplace")
    
    def get_current_weapon(self):
        """获取当前武器"""
        if not self.weapons:
            return {
                'id': -1,
                'name': "新手除草刀",
                'original_name': "Starter Cutter",
                'rarity': Rarity.COMMON,
                'damage_multiplier': 1.0,
                'owner': self.blockchain_manager.account,
                'price': 0,
                'for_sale': False
            }
        self.current_weapon_index %= len(self.weapons)
        return self.weapons[self.current_weapon_index]
    
    def get_rarity_color(self, rarity: Rarity):
        """获取稀有度颜色"""
        palette = {
            Rarity.COMMON: GRAY,
            Rarity.RARE: BLUE,
            Rarity.EPIC: PURPLE,
            Rarity.LEGENDARY: GOLD
        }
        return palette.get(rarity, GRAY)
    
    def format_price_display(self, price_wei):
        """格式化价格显示"""
        if price_wei is None:
            return "未知"
        if self.blockchain_manager.blockchain_available and self.blockchain_manager.w3:
            try:
                eth_value = self.blockchain_manager.w3.from_wei(price_wei, 'ether')
                return f"{eth_value:.4f} ETH"
            except Exception:
                pass
        return f"{price_wei} Wei"
    
    def update_weapon_profile(self, weapon):
        """更新武器配置"""
        if not weapon:
            self.rotation_speed = self.base_rotation_speed
            self.current_blade_count = 1
            self.current_weapon_thickness = 8
            return
        rotation_speed, blade_count = self.weapon_manager.get_weapon_spin_profile(weapon)
        self.rotation_speed = max(2, rotation_speed)
        self.current_blade_count = max(1, blade_count)
        base_thickness = 6 + (weapon.get('damage_multiplier', 1.0) - 1.0) * 6
        rarity_bonus = weapon['rarity'].value * 2
        self.current_weapon_thickness = int(max(6, base_thickness + rarity_bonus))
    
    def load_player_data(self):
        """加载玩家数据"""
        if not self.blockchain_manager.blockchain_available:
            self.score = 0
            self.coins = 0
            self.weapons = []
            self.listed_weapons = []
            self.update_weapon_profile(None)
            return
        
        self.score, self.coins = self.blockchain_manager.load_player_stats(self.blockchain_manager.account)
        self.weapons, self.listed_weapons = self.blockchain_manager.load_player_weapons(
            self.blockchain_manager.account,
            self.weapon_manager.get_weapon_display_name
        )
        
        if self.weapons:
            self.current_weapon_index = min(self.current_weapon_index, len(self.weapons) - 1)
        else:
            self.current_weapon_index = 0
        self.update_weapon_profile(self.get_current_weapon())

        # 加载玩家名称和排名
        self.player_name = self.blockchain_manager.get_player_name(self.blockchain_manager.account)
        self.player_rank, self.total_players = self.blockchain_manager.get_player_rank(self.blockchain_manager.account)

        # 加载所有可用账户
        self.all_accounts = self.blockchain_manager.get_all_accounts()
        self.account_selection = self.blockchain_manager.account_index

    def load_market_weapons(self):
        """加载市场武器"""
        self.market_weapons = self.blockchain_manager.load_market_weapons(
            self.weapon_manager.get_weapon_display_name
        )
        self.market_last_refresh_ms = pygame.time.get_ticks()
    
    def load_case_data(self):
        """加载箱子数据"""
        self.all_cases = self.blockchain_manager.get_all_cases()
        self.case_inventory = self.blockchain_manager.get_user_case_inventory(
            self.blockchain_manager.account
        )
        self._load_case_sprites()

    def _load_case_sprites(self):
        """加载箱子贴图"""
        import os
        case_name_map = {
            "Knife Case": "刀箱子",
            "Sword Case": "剑箱子",
            "Axe Case": "斧头箱子",
            "Sickle Case": "镰刀箱子"
        }

        for case in self.all_cases:
            case_name = case['name']
            if case_name in case_name_map:
                filename = f"{case_name_map[case_name]}.png"
                sprite_path = os.path.join("箱子图片", filename)
                try:
                    surf = pygame.image.load(sprite_path).convert_alpha()
                    # 统一缩放到合适大小
                    target_size = (80, 80)
                    surf = pygame.transform.smoothscale(surf, target_size)
                    self.case_sprites[case_name] = surf
                except Exception as err:
                    print(f"⚠️ 箱子图片加载失败 {sprite_path}: {err}")

    def load_leaderboard(self):
        """加载排行榜"""
        self.leaderboard = self.blockchain_manager.get_leaderboard(20)
        self.player_rank, self.total_players = self.blockchain_manager.get_player_rank(
            self.blockchain_manager.account
        )

    def maybe_flush_points(self):
        """尝试将积分上链"""
        now = pygame.time.get_ticks()
        if self.pending_points >= 50 or (self.pending_points > 0 and (now - self.last_flush_ms) >= self.flush_interval_ms):
            to_flush = self.pending_points
            self.pending_points = 0
            self.last_flush_ms = now
            if self.blockchain_manager.record_score(self.blockchain_manager.account, to_flush):
                self.score, self.coins = self.blockchain_manager.load_player_stats(self.blockchain_manager.account)
    
    def _update_camera_surface(self):
        """更新相机表面"""
        camera_w = max(240, int(WIDTH / self.camera_zoom))
        camera_h = max(180, int(HEIGHT / self.camera_zoom))
        self.camera_rect = pygame.Rect(0, 0, camera_w, camera_h)
        self.scene_surface = pygame.Surface((camera_w, camera_h), pygame.SRCALPHA).convert_alpha()
    
    def update_camera(self):
        """更新相机位置"""
        self.camera_rect.center = (int(self.player_x), int(self.player_y))
        self.camera_rect.clamp_ip(self.world_bounds)
    
    def world_point_to_screen(self, x: float, y: float):
        """世界坐标转屏幕坐标"""
        return int(x - self.camera_rect.left), int(y - self.camera_rect.top)
    
    def world_rect_to_screen(self, rect: pygame.Rect):
        """世界矩形转屏幕矩形"""
        return pygame.Rect(
            rect.x - self.camera_rect.left,
            rect.y - self.camera_rect.top,
            rect.width,
            rect.height
        )
    
    def generate_grass(self):
        """生成草地"""
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
        """生成默认草地网格"""
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
    
    def update_player_on_grass(self):
        """更新玩家是否站在草地上"""
        self.standing_grass_id = None
        for idx, grass in enumerate(self.grass_patches):
            inside = grass['rect'].collidepoint(int(self.player_x), int(self.player_y))
            grass['player_on'] = inside
            if inside:
                self.standing_grass_id = idx
    
    def handle_player_movement(self):
        """处理玩家移动"""
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
    
    def _blade_hits_rect(self, dir_x, dir_y, rect):
        """检测刀片是否击中矩形"""
        samples = max(6, int(self.weapon_length / 8))
        half_thickness = self.current_weapon_thickness / 2
        for i in range(samples + 1):
            t = i / samples
            px = self.player_x + dir_x * self.weapon_length * t
            py = self.player_y + dir_y * self.weapon_length * t
            hit_rect = pygame.Rect(px - half_thickness, py - half_thickness,
                                   self.current_weapon_thickness, self.current_weapon_thickness)
            if rect.colliderect(hit_rect):
                return True
        return False
    
    def rotate_weapon(self):
        """旋转武器并检测碰撞"""
        if self.game_state != "playing":
            return
        weapon = self.get_current_weapon()
        self.update_weapon_profile(weapon)
        self.angle = (self.angle + self.rotation_speed) % 360

        multiplier = weapon['damage_multiplier'] if weapon else 1.0
        damage = 8 * multiplier
        points_earned = 0
        
        # 检测所有刀片的碰撞
        angle_offset = 360 / self.current_blade_count
        hit_grass = set()

        for blade_idx in range(self.current_blade_count):
            blade_angle = self.angle + (blade_idx * angle_offset)
            actual_weapon_angle = blade_angle + 90
            radians_angle = math.radians(actual_weapon_angle)
            dir_x = math.cos(radians_angle)
            dir_y = math.sin(radians_angle)

            for idx, grass in enumerate(self.grass_patches):
                if idx not in hit_grass and self._blade_hits_rect(dir_x, dir_y, grass['rect']):
                    hit_grass.add(idx)

        # 处理被击中的草块
        for idx in sorted(hit_grass, reverse=True):
            grass = self.grass_patches[idx]
            grass['health'] -= damage
            if grass['health'] <= 0:
                self.grass_patches.pop(idx)
                points_earned += 10

        if points_earned > 0:
            self.pending_points += points_earned
            self.score += points_earned
        self.maybe_flush_points()
    
    def draw_game(self, surface):
        """绘制游戏场景"""
        self.scene_surface.fill((0, 0, 0, 0))
        if self.tile_map:
            self.tile_map.draw(self.scene_surface, self.camera_rect)
        
        # 绘制草地
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
        
        # 绘制玩家
        player_pos = self.world_point_to_screen(self.player_x, self.player_y)
        pygame.draw.circle(self.scene_surface, (80, 80, 200), player_pos, self.player_radius)
        pygame.draw.circle(self.scene_surface, (255, 255, 255), player_pos, max(2, self.player_radius - 8))
        
        # 绘制武器
        weapon = self.get_current_weapon()
        if weapon:
            sprite = self.weapon_manager.get_weapon_sprite(weapon)
            angle_offset = 360 / self.current_blade_count
            
            for blade_idx in range(self.current_blade_count):
                blade_angle = self.angle + (blade_idx * angle_offset)
                radians_angle = math.radians(blade_angle)

                tip_x = self.player_x + self.weapon_length * math.cos(radians_angle)
                tip_y = self.player_y + self.weapon_length * math.sin(radians_angle)
                weapon_tip = self.world_point_to_screen(tip_x, tip_y)

                if sprite:
                    anchor = self.weapon_manager.get_weapon_anchor(weapon, sprite)
                    if not anchor:
                        anchor = (sprite.get_width() / 2, sprite.get_height() / 2)
                    
                    display_angle = blade_angle - 90
                    rotated = pygame.transform.rotate(sprite, -display_angle)
                    
                    # 计算旋转后锚点位置
                    anchor_offset_x = anchor[0] - sprite.get_width() / 2
                    anchor_offset_y = anchor[1] - sprite.get_height() / 2
                    
                    radians_display = math.radians(display_angle)
                    cos_a = math.cos(radians_display)
                    sin_a = math.sin(radians_display)
                    rotated_anchor_x = anchor_offset_x * cos_a - anchor_offset_y * sin_a
                    rotated_anchor_y = anchor_offset_x * sin_a + anchor_offset_y * cos_a
                    
                    rotated_center_x = self.player_x + rotated_anchor_x
                    rotated_center_y = self.player_y + rotated_anchor_y
                    rotated_center_screen = self.world_point_to_screen(rotated_center_x, rotated_center_y)
                    
                    rect = rotated.get_rect(center=rotated_center_screen)
                    self.scene_surface.blit(rotated, rect)
                else:
                    pygame.draw.line(
                        self.scene_surface,
                        self.get_rarity_color(weapon['rarity']),
                        player_pos,
                        weapon_tip,
                        self.current_weapon_thickness
                    )
            
            pygame.draw.circle(self.scene_surface, BROWN, player_pos, max(6, self.player_radius // 2))
        
        # 缩放并绘制到屏幕
        if self.scene_surface.get_size() != (WIDTH, HEIGHT):
            scaled = pygame.transform.smoothscale(self.scene_surface, (WIDTH, HEIGHT))
            surface.blit(scaled, (0, 0))
        else:
            surface.blit(self.scene_surface, (0, 0))
    
    def draw(self, surface):
        """绘制游戏"""
        if self.game_state == "start_menu":
            UIRenderer.draw_start_menu(surface, self, getattr(self, 'menu_selection', 0))
        elif self.game_state == "profile":
            UIRenderer.draw_profile(surface, self)
        elif self.game_state == "leaderboard":
            UIRenderer.draw_leaderboard(surface, self)
        elif self.game_state == "account_select":
            UIRenderer.draw_account_select(surface, self)
        elif self.game_state == "playing":
            self.draw_game(surface)
            UIRenderer.draw_hud(surface, self, translucent=True)
        elif self.game_state == "marketplace":
            surface.fill(WHITE)
            UIRenderer.draw_marketplace(surface, self)
            UIRenderer.draw_hud(surface, self, translucent=False)
        elif self.game_state == "inventory":
            surface.fill(WHITE)
            UIRenderer.draw_inventory(surface, self)
            UIRenderer.draw_hud(surface, self, translucent=False)
        elif self.game_state == "case_shop":
            from .case_ui import CaseUIRenderer
            CaseUIRenderer.draw_case_shop(surface, self)
        elif self.game_state == "case_inventory":
            from .case_ui import CaseUIRenderer
            CaseUIRenderer.draw_case_inventory(surface, self)

        # 开箱结果弹窗（覆盖在所有界面之上）
        if self.show_case_open_result:
            from .case_ui import CaseUIRenderer
            CaseUIRenderer.draw_case_open_result(surface, self)

    def tick_auto_refresh(self):
        """自动刷新区块链数据"""
        if not self.blockchain_manager.blockchain_available or not self.blockchain_manager.w3:
            return
        now = pygame.time.get_ticks()
        if now - getattr(self, 'last_auto_refresh_ms', 0) < 500:
            return
        self.last_auto_refresh_ms = now
        try:
            current_block = self.blockchain_manager.w3.eth.block_number
        except Exception:
            return
        if current_block != self.last_refresh_block:
            self.last_refresh_block = current_block
            self.load_player_data()
            if self.game_state == "marketplace":
                self.load_market_weapons()
        if self.game_state == "marketplace" and now - self.market_last_refresh_ms >= self.market_refresh_interval_ms:
            self.load_market_weapons()
    
    def mint_random_weapon(self):
        """铸造随机武器"""
        if not self.blockchain_manager.blockchain_available:
            print("⚠️ 离线模式无法铸造武器")
            return
        required_coins = 20
        if self.coins < required_coins:
            print(f"金币不足，需 {required_coins}，当前 {self.coins}")
            return
        
        # 使用 WeaponManager 的随机生成系统
        rarity = self.weapon_manager.roll_weapon_rarity()
        weapon_type = self.weapon_manager.roll_weapon_type()
        name = self.weapon_manager.generate_weapon_name(weapon_type, rarity)
        damage_multiplier = self.weapon_manager.get_weapon_stats(rarity)

        print(f"🎲 铸造武器: {name} (稀有度: {rarity.name}, 伤害: x{damage_multiplier/100:.2f})")

        if self.blockchain_manager.mint_weapon(self.blockchain_manager.account, name, rarity.value, damage_multiplier):
            self.load_player_data()
            print(f"✅ 成功铸造 {name}！")

    def purchase_weapon(self, weapon):
        """购买武器"""
        if weapon['owner'].lower() == self.blockchain_manager.account.lower():
            print("⚠️ 这是你自己的武器，不能购买")
            return

        # 优先使用金币购买（如果设置了金币价格）
        if weapon.get('coin_price', 0) > 0:
            if self.coins >= weapon['coin_price']:
                print(f"💰 使用 {weapon['coin_price']} 金币购买武器...")
                if self.blockchain_manager.purchase_weapon_with_coins(
                    self.blockchain_manager.account,
                    weapon['id'],
                    weapon['coin_price']
                ):
                    self.load_player_data()
                    self.load_market_weapons()
            else:
                print(f"⚠️ 金币不足！需要 {weapon['coin_price']} 金币，当前 {self.coins} 金币")
        elif weapon.get('price', 0) > 0:
            # 使用ETH购买
            if self.blockchain_manager.purchase_weapon(
                self.blockchain_manager.account,
                weapon['id'],
                weapon['price']
            ):
                self.load_player_data()
                self.load_market_weapons()
        else:
            print("⚠️ 武器未设置价格")

    def _stop_listing_input(self):
        """停止价格输入"""
        if self.listing_input_active:
            pygame.key.stop_text_input()
        self.listing_input_active = False
        self.listing_input_text = ""
    
    def start_listing_current_weapon(self):
        """开始上架当前武器"""
        if not self.weapons:
            self.inventory_feedback = "⚠️ 当前没有武器可上架"
            return
        pygame.key.start_text_input()
        self.listing_input_active = True
        self.listing_input_text = ""
        weapon = self.weapons[self.inventory_selection]
        self.inventory_feedback = f"🎯 上架 #{weapon['id']:02d} {weapon['name']} - 输入价格 (ETH) 然后回车，上限 6 位小数"
    
    def handle_listing_price_event(self, event):
        """处理上架价格输入事件"""
        if event.key == pygame.K_ESCAPE:
            self._stop_listing_input()
            self.inventory_feedback = "⚖️ 已取消上架"
            return
        if event.key == pygame.K_BACKSPACE:
            self.listing_input_text = self.listing_input_text[:-1]
            return
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if not self.listing_input_text:
                self.inventory_feedback = "⚠️ 请输入有效价格"
                return
            try:
                price = float(self.listing_input_text)
                if price <= 0:
                    raise ValueError("非正价格")
                price_wei = self.blockchain_manager.w3.to_wei(round(price, 6), 'ether') if self.blockchain_manager.blockchain_available and self.blockchain_manager.w3 else None
                weapon = self.weapons[self.inventory_selection]
                if self.blockchain_manager.list_weapon_for_sale(self.blockchain_manager.account, weapon['id'], price_wei):
                    self.load_player_data()
                    self.load_market_weapons()
                    display_price = self.format_price_display(price_wei)
                    self.inventory_feedback = f"✅ 已将武器 #{weapon['id']:02d} 上架，价格 {display_price}"
                else:
                    self.inventory_feedback = "❌ 上架失败"
            except Exception as err:
                self.inventory_feedback = f"❌ 价格解析失败: {err}"
            finally:
                self._stop_listing_input()
            return
        if event.unicode and event.unicode in "0123456789.":
            if event.unicode == '.' and '.' in self.listing_input_text:
                return
            self.listing_input_text += event.unicode
    
    def handle_inventory_input(self, event):
        """处理背包输入"""
        if not self.weapons:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_i:
                self.toggle_inventory()
            return
        if event.type == pygame.KEYDOWN:
            if self.listing_input_active:
                self.handle_listing_price_event(event)
                return
            if event.key == pygame.K_UP:
                self.inventory_selection = max(0, self.inventory_selection - 1)
            elif event.key == pygame.K_DOWN:
                self.inventory_selection = min(len(self.weapons) - 1, self.inventory_selection + 1)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.current_weapon_index = self.inventory_selection
                self.update_weapon_profile(self.get_current_weapon())
            elif event.key == pygame.K_i:
                self.toggle_inventory()
            elif event.key == pygame.K_l:
                self.start_listing_current_weapon()
    
    def handle_market_input(self, event):
        """处理市场输入"""
        if not self.market_weapons:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                self.toggle_market()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.load_market_weapons()
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.market_selection = max(0, self.market_selection - 1)
            elif event.key == pygame.K_DOWN:
                self.market_selection = min(len(self.market_weapons) - 1, self.market_selection + 1)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                weapon = self.market_weapons[self.market_selection]
                self.purchase_weapon(weapon)
            elif event.key == pygame.K_r:
                self.load_market_weapons()
            elif event.key == pygame.K_m:
                self.toggle_market()

    def handle_start_menu_input(self, event):
        """处理开始菜单输入"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.menu_selection = max(0, self.menu_selection - 1)
            elif event.key == pygame.K_DOWN:
                self.menu_selection = min(3, self.menu_selection + 1)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.menu_selection == 0:  # 个人中心
                    self.game_state = "profile"
                elif self.menu_selection == 1:  # 开始游戏
                    self.game_state = "playing"
                elif self.menu_selection == 2:  # 排行榜
                    self.load_leaderboard()
                    self.game_state = "leaderboard"
                elif self.menu_selection == 3:  # 切换账户
                    if self.blockchain_manager.blockchain_available and self.all_accounts:
                        self.game_state = "account_select"
                    else:
                        print("⚠️ 区块链未连接或没有可用账户")
            elif event.key == pygame.K_ESCAPE:
                return "quit"
        return None

    def handle_profile_input(self, event):
        """处理个人中心输入"""
        if event.type == pygame.KEYDOWN:
            if self.profile_editing_name:
                # 正在编辑名称
                if event.key == pygame.K_RETURN:
                    # 保存名称
                    if self.profile_name_input.strip():
                        if self.blockchain_manager.set_player_name(
                            self.blockchain_manager.account,
                            self.profile_name_input.strip()
                        ):
                            self.player_name = self.profile_name_input.strip()
                            print(f"✅ 名称设置为: {self.player_name}")
                    self.profile_editing_name = False
                    self.profile_name_input = ""
                elif event.key == pygame.K_ESCAPE:
                    self.profile_editing_name = False
                    self.profile_name_input = ""
                elif event.key == pygame.K_BACKSPACE:
                    self.profile_name_input = self.profile_name_input[:-1]
                elif event.unicode and len(self.profile_name_input) < 20:
                    # 只接受字母数字和部分符号
                    if event.unicode.isalnum() or event.unicode in " -_":
                        self.profile_name_input += event.unicode
            else:
                # 未在编辑状态
                if event.key == pygame.K_n:
                    # 开始编辑名称
                    self.profile_editing_name = True
                    self.profile_name_input = self.player_name
                elif event.key == pygame.K_i:
                    # 打开背包
                    self.toggle_inventory()
                elif event.key == pygame.K_ESCAPE:
                    self.game_state = "start_menu"

    def handle_leaderboard_input(self, event):
        """处理排行榜输入"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.leaderboard_selection = max(0, self.leaderboard_selection - 1)
            elif event.key == pygame.K_DOWN:
                self.leaderboard_selection = min(len(self.leaderboard) - 1, self.leaderboard_selection + 1)
            elif event.key == pygame.K_r:
                # 刷新排行榜
                self.load_leaderboard()
            elif event.key == pygame.K_ESCAPE:
                self.game_state = "start_menu"

    def handle_account_select_input(self, event):
        """处理账户选择输入"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.account_selection = max(0, self.account_selection - 1)
            elif event.key == pygame.K_DOWN:
                self.account_selection = min(len(self.all_accounts) - 1, self.account_selection + 1)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                # 切换账户
                if self.blockchain_manager.switch_account(self.account_selection):
                    # 重新加载玩家数据
                    self.load_player_data()
                    self.game_state = "start_menu"
                    print(f"✅ 已切换到账户 {self.account_selection}")
            elif event.key == pygame.K_ESCAPE:
                self.game_state = "start_menu"

    def handle_case_shop_input(self, event):
        """处理箱子商店输入"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 检测点击盗贼老人（切换对话）
            from .config import HEIGHT
            mouse_pos = event.pos
            # 匹配case_ui.py中的NPC位置和大小（缩放0.3倍后）
            npc_x = 100
            npc_y = HEIGHT - 500
            # 假设原始图片约400x500，缩放0.3倍后约120x150
            npc_width = 120
            npc_height = 150
            npc_rect = pygame.Rect(npc_x, npc_y, npc_width, npc_height)

            if npc_rect.collidepoint(mouse_pos):
                # 切换到下一条对话
                if not hasattr(self, 'thief_dialogue_index'):
                    self.thief_dialogue_index = 0
                self.thief_dialogue_index = (self.thief_dialogue_index + 1) % 3
                return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.case_shop_selection = max(0, self.case_shop_selection - 2)
            elif event.key == pygame.K_DOWN:
                self.case_shop_selection = min(len(self.all_cases) - 1, self.case_shop_selection + 2)
            elif event.key == pygame.K_LEFT:
                if self.case_shop_selection % 2 == 1:
                    self.case_shop_selection -= 1
            elif event.key == pygame.K_RIGHT:
                if self.case_shop_selection % 2 == 0 and self.case_shop_selection < len(self.all_cases) - 1:
                    self.case_shop_selection += 1
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                # 购买箱子
                if self.case_shop_selection < len(self.all_cases):
                    case = self.all_cases[self.case_shop_selection]
                    if self.coins >= case['coin_price']:
                        if self.blockchain_manager.purchase_case(
                            self.blockchain_manager.account,
                            case['id'],
                            1
                        ):
                            print(f"✅ 购买 {case['name']} 成功！")
                            # 刷新数据
                            self.load_player_data()
                            self.load_case_data()
                    else:
                        print(f"⚠️ 金币不足！需要 {case['coin_price']} 金币")
            elif event.key == pygame.K_b:
                # 查看背包
                self.game_state = "case_inventory"
                self.case_inventory_selection = 0
            elif event.key == pygame.K_ESCAPE:
                self.game_state = "playing"

    def handle_case_inventory_input(self, event):
        """处理箱子库存输入"""
        # 获取有库存的箱子
        owned_cases = []
        for case in self.all_cases:
            count = self.case_inventory.get(case['id'], 0)
            if count > 0:
                owned_cases.append((case, count))

        if not owned_cases:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.game_state = "case_shop"
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.case_inventory_selection = max(0, self.case_inventory_selection - 1)
            elif event.key == pygame.K_DOWN:
                self.case_inventory_selection = min(len(owned_cases) - 1, self.case_inventory_selection + 1)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                # 开箱
                if self.case_inventory_selection < len(owned_cases):
                    case, count = owned_cases[self.case_inventory_selection]
                    self.open_case(case)
            elif event.key == pygame.K_ESCAPE:
                self.game_state = "case_shop"

    def open_case(self, case):
        """开启箱子"""
        print(f"🎁 正在开启 {case['name']}...")

        if self.blockchain_manager.open_case_from_inventory(
            self.blockchain_manager.account,
            case['id']
        ):
            # 刷新数据
            self.load_player_data()
            self.load_case_data()

            # 获取最新的武器（应该是刚开出来的）
            if self.weapons:
                self.opened_weapon = self.weapons[-1]
                self.show_case_open_result = True
                print(f"🎉 恭喜获得：{self.opened_weapon['name']}！")
        else:
            print("❌ 开箱失败")

    def close_case_result(self):
        """关闭开箱结果"""
        self.show_case_open_result = False
        self.opened_weapon = None
