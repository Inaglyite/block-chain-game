# -*- coding: utf-8 -*-
"""
武器相关逻辑
"""
import os
import pygame
import random
from .enums import Rarity, WeaponType
from .config import BASE_DIR


class WeaponManager:
    """武器管理器"""
    
    def __init__(self):
        self.weapon_sprite_cache = {}  # (type, level) -> surface (基础贴图缓存)
        self.weapon_with_wear_cache = {}  # (type, level, wear_int) -> surface (带磨损贴图缓存)
        self.weapon_anchor_cache = {}  # (type, rarity) -> (handle_x, handle_y)
    
    @staticmethod
    def roll_weapon_rarity() -> Rarity:
        """
        根据概率抽取武器稀有度
        概率分布:
        - 普通: 55%
        - 稀有: 30%
        - 史诗: 12%
        - 传说: 3%
        """
        rand = random.random()
        if rand < 0.55:
            return Rarity.COMMON
        elif rand < 0.85:  # 0.55 + 0.30
            return Rarity.RARE
        elif rand < 0.97:  # 0.85 + 0.12
            return Rarity.EPIC
        else:
            return Rarity.LEGENDARY

    @staticmethod
    def roll_weapon_type() -> WeaponType:
        """随机抽取武器类型，概率均等"""
        return random.choice(list(WeaponType))

    @staticmethod
    def generate_weapon_name(weapon_type: WeaponType, rarity: Rarity) -> str:
        """
        生成武器名称
        格式: [稀有度前缀] + [武器类型]
        """
        rarity_prefixes = {
            Rarity.COMMON: ["普通", "简易", "基础", "新手"],
            Rarity.RARE: ["稀有", "精良", "锋利", "优质"],
            Rarity.EPIC: ["史诗", "传承", "魔法", "符文"],
            Rarity.LEGENDARY: ["传说", "神话", "不朽", "至尊"]
        }

        weapon_suffixes = {
            WeaponType.KNIFE: ["除草刀", "割草刀", "弯刀", "小刀"],
            WeaponType.SWORD: ["除草剑", "长剑", "双刃剑", "宝剑"],
            WeaponType.AXE: ["除草斧", "战斧", "巨斧", "伐木斧"],
            WeaponType.SICKLE: ["除草镰", "镰刀", "收割镰", "月牙镰"]
        }

        prefix = random.choice(rarity_prefixes[rarity])
        suffix = random.choice(weapon_suffixes[weapon_type])

        return f"{prefix}{suffix}"

    @staticmethod
    def get_weapon_stats(rarity: Rarity) -> int:
        """
        获取武器伤害倍率（用于合约）
        返回值是百分比，如 100 表示 1.0 倍
        """
        damage_multipliers = {
            Rarity.COMMON: random.randint(100, 110),      # 1.0x - 1.1x
            Rarity.RARE: random.randint(120, 140),        # 1.2x - 1.4x
            Rarity.EPIC: random.randint(150, 180),        # 1.5x - 1.8x
            Rarity.LEGENDARY: random.randint(190, 230)    # 1.9x - 2.3x
        }
        return damage_multipliers[rarity]

    def detect_weapon_type(self, weapon_name: str) -> str:
        """检测武器类型（从名称推断）"""
        name = (weapon_name or "").lower()

        # 武器名称到类型的映射（来自智能合约配置）
        weapon_type_map = {
            # 刀类
            "starter knife": "刀",
            "sharp knife": "刀",
            "epic knife": "刀",
            "legendary knife": "刀",
            "starter cutter": "刀",

            # 剑类
            "basic sword": "剑",
            "golden blade": "剑",
            "epic sword": "剑",
            "legendary blade": "剑",

            # 斧头类
            "basic axe": "斧头",
            "battle axe": "斧头",
            "epic axe": "斧头",
            "legendary axe": "斧头",

            # 镰刀类
            "basic sickle": "镰刀",
            "steel sickle": "镰刀",
            "epic scythe": "镰刀",
            "legendary scythe": "镰刀",
            "sharp sickle": "镰刀",
        }

        # 先尝试精确匹配
        if name in weapon_type_map:
            return weapon_type_map[name]

        # 如果没有精确匹配，使用关键词判断
        if "axe" in name or "斧" in name:
            return "斧头"
        if "sickle" in name or "scythe" in name or "镰" in name:
            return "镰刀"
        if "sword" in name or "blade" in name or "剑" in name:
            return "剑"
        if "knife" in name or "cutter" in name or "刀" in name:
            return "刀"

        # 默认返回刀
        return "刀"
    
    def get_weapon_display_name(self, weapon_name: str, rarity: Rarity) -> str:
        """
        将武器名称转换为显示名称（向后兼容方法）
        现在武器名称已经在铸造时生成，这里直接返回
        """
        return weapon_name

    def get_weapon_sprite(self, weapon) -> pygame.Surface:
        """获取武器贴图，包含磨损度噪点效果（使用静态缓存）"""
        if not weapon:
            return None

        wtype = self.detect_weapon_type(weapon.get('original_name') or weapon.get('name'))
        level = weapon['rarity'].value + 1  # 1~4 级对应 COMMON~LEGENDARY
        wear = weapon.get('wear', 0)

        # 将wear转换为整数用于缓存key（保留4位小数精度）
        wear_int = int(wear * 10000) if wear else 0

        # 检查带磨损度的缓存
        cache_key = (wtype, level, wear_int)
        if cache_key in self.weapon_with_wear_cache:
            return self.weapon_with_wear_cache[cache_key].copy()

        # 获取基础贴图
        base_key = (wtype, level)
        if base_key not in self.weapon_sprite_cache:
            filename = f"{level}级.png"
            sprite_path = os.path.join(BASE_DIR, "武器图片", wtype, filename)
            if not os.path.exists(sprite_path):
                return None
            try:
                surf = pygame.image.load(sprite_path).convert_alpha()
                # 统一尺寸，匹配 weapon_length (60像素) 以对齐 hitbox
                target_h = 60
                scale = target_h / surf.get_height()
                target_w = max(16, int(surf.get_width() * scale))
                surf = pygame.transform.smoothscale(surf, (target_w, target_h))
                self.weapon_sprite_cache[base_key] = surf
            except Exception as err:
                print(f"⚠️ 武器图片加载失败 {sprite_path}: {err}")
                return None

        base_surf = self.weapon_sprite_cache[base_key]

        # 应用磨损度效果并缓存
        if wear and wear > 0.05:  # S级以上才添加噪点
            result_surf = self._apply_wear_effect(base_surf.copy(), wear)
        else:
            result_surf = base_surf.copy()

        # 缓存结果
        self.weapon_with_wear_cache[cache_key] = result_surf
        return result_surf.copy()

    def _apply_wear_effect(self, surface: pygame.Surface, wear: float) -> pygame.Surface:
        """
        对武器贴图应用磨损度噪点效果（使用固定种子保证一致性）
        wear: 0.0-1.0，值越大噪点越多
        """
        # 使用wear值作为随机种子，确保相同wear产生相同的噪点
        random.seed(int(wear * 100000))

        # 创建可修改的surface
        width, height = surface.get_size()

        try:
            # 根据磨损度计算噪点密度
            # wear: 0.05-1.0 映射到 noise_density: 0.01-0.15
            noise_density = min(0.15, max(0.01, (wear - 0.05) * 0.15))

            # 计算需要添加的噪点数量
            num_noise_pixels = int(width * height * noise_density)

            # 锁定surface以便修改像素
            pygame.surfarray.use_arraytype('numpy')  # 尝试使用numpy
            pixels = pygame.surfarray.pixels3d(surface)
            alpha = pygame.surfarray.pixels_alpha(surface)

            # 添加随机噪点
            darkening_factor = 0.5 + (wear * 0.3)  # 0.5-0.8之间

            for _ in range(num_noise_pixels):
                x = random.randint(0, width - 1)
                y = random.randint(0, height - 1)

                # 只在非透明区域添加噪点
                if alpha[x, y] > 50:
                    pixels[x, y] = (pixels[x, y] * darkening_factor).astype('uint8')

            # 稍微降低整体的alpha，让武器看起来有些褪色
            if wear > 0.5:  # D级以上才褪色
                fade_factor = max(0.85, 1.0 - (wear - 0.5) * 0.3)  # 最多降到85%
                alpha[:] = (alpha * fade_factor).astype('uint8')

            del pixels
            del alpha

        except Exception as err:
            # 如果numpy不可用，使用更简单的方法
            # print(f"⚠️ 应用磨损效果失败（使用简单模式）: {err}")

            # 简单模式：只降低整体亮度
            if wear > 0.3:
                # 创建半透明黑色遮罩
                overlay = pygame.Surface((width, height), pygame.SRCALPHA)
                darkness = int((wear - 0.3) * 100)  # 0-70之间
                overlay.fill((0, 0, 0, darkness))
                surface.blit(overlay, (0, 0))

        finally:
            # 恢复随机种子
            random.seed()

        return surface

    def get_weapon_anchor(self, weapon, sprite) -> tuple:
        """获取武器手柄锚点位置"""
        if not weapon or not sprite:
            return None
        wtype = self.detect_weapon_type(weapon.get('original_name') or weapon.get('name'))
        level = weapon['rarity'].value + 1
        key = (wtype, level)
        if key in self.weapon_anchor_cache:
            return self.weapon_anchor_cache[key]
        width, height = sprite.get_width(), sprite.get_height()
        
        # 根据武器类型设置手柄锚点位置（修正后）
        # 刀：手柄在左下角（原本刃在右上角，所以手柄在对角）
        if wtype == "刀":
            anchor = (width * 0.15, height * 0.85)
        # 剑和斧头：手柄在右上角（原本刃在左下角，所以手柄在对角）
        elif wtype in ["剑", "斧头"]:
            anchor = (width * 0.85, height * 0.15)
        # 镰刀：手柄在左上角（原本刃在右下角，所以手柄在对角）
        elif wtype == "镰刀":
            anchor = (width * 0.15, height * 0.15)
        # 默认：中心偏上
        else:
            anchor = (width / 2, height * 0.2)
        
        self.weapon_anchor_cache[key] = anchor
        return anchor
    
    def get_weapon_spin_profile(self, weapon) -> tuple:
        """获取武器旋转配置"""
        profiles = {
            Rarity.COMMON: (1.0, 1),
            Rarity.RARE: (1.3, 2),
            Rarity.EPIC: (1.8, 3),
            Rarity.LEGENDARY: (2.4, 4)
        }
        speed_mult, base_blades = profiles.get(weapon['rarity'], (1.0, 1))
        damage_bonus = max(0.0, weapon.get('damage_multiplier', 1.0) - 1.0)
        rotation_speed = 5 * (speed_mult + damage_bonus * 0.5)  # base_rotation_speed = 5
        blade_count = min(max(base_blades + int(damage_bonus * 1.5), 1), 6)
        return rotation_speed, blade_count

