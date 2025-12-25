# -*- coding: utf-8 -*-
"""
UI绘制模块
"""
import pygame
from .config import WIDTH, HEIGHT
from .utils import load_chinese_font, load_emoji_font, render_text_with_emoji

# --- 现代主题颜色 ---
THEME = {
    "background": (240, 242, 248),      # 柔和的浅蓝灰色背景
    "text": (45, 52, 70),               # 深蓝灰色文字
    "primary": (79, 70, 229),           # 靛蓝色主色调
    "primary_light": (129, 120, 255),   # 亮靛蓝
    "secondary": (16, 185, 129),        # 翠绿色
    "secondary_light": (52, 211, 153),  # 亮绿色
    "accent": (251, 146, 60),           # 橙色强调色
    "accent_light": (255, 183, 77),     # 亮橙色
    "highlight": (254, 243, 199),       # 淡黄色高亮
    "danger": (239, 68, 68),            # 红色警告
    "danger_light": (252, 165, 165),    # 浅红色
    "success": (34, 197, 94),           # 成功绿
    "info": (59, 130, 246),             # 信息蓝
    "white": (255, 255, 255),
    "light_gray": (226, 232, 240),      # 浅灰
    "mid_gray": (148, 163, 184),        # 中灰
    "dark_gray": (71, 85, 105),         # 深灰
    "card_bg": (255, 255, 255),         # 卡片背景
    "card_shadow": (203, 213, 225),     # 卡片阴影
}

# --- 字体定义 ---
try:
    font_path = None # 使用默认路径
    title_font = load_chinese_font(48)
    header_font = load_chinese_font(32)
    default_font = load_chinese_font(20)
    small_font = load_chinese_font(16)
    icon_font = load_chinese_font(24)

    # --- Emoji字体 ---
    emoji_title_font = load_emoji_font(48)
    emoji_header_font = load_emoji_font(32)
    emoji_default_font = load_emoji_font(20)
    emoji_small_font = load_emoji_font(16)
except Exception as e:
    print(f"字体加载失败: {e}. Pygame将使用默认字体。")
    title_font = pygame.font.Font(None, 60)
    header_font = pygame.font.Font(None, 40)
    default_font = pygame.font.Font(None, 24)
    small_font = pygame.font.Font(None, 18)
    icon_font = pygame.font.Font(None, 30)
    emoji_title_font = emoji_header_font = emoji_default_font = emoji_small_font = None


def draw_gradient_rect(surface, rect, color1, color2, vertical=True):
    """绘制渐变矩形"""
    if vertical:
        for y in range(rect.height):
            ratio = y / rect.height
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            pygame.draw.line(surface, (r, g, b),
                           (rect.x, rect.y + y),
                           (rect.x + rect.width, rect.y + y))
    else:
        for x in range(rect.width):
            ratio = x / rect.width
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            pygame.draw.line(surface, (r, g, b),
                           (rect.x + x, rect.y),
                           (rect.x + x, rect.y + rect.height))

def draw_card_with_shadow(surface, rect, bg_color, border_color=None, border_width=0, border_radius=10):
    """绘制带阴影的卡片"""
    # 绘制阴影
    shadow_rect = rect.copy()
    shadow_rect.move_ip(4, 4)
    shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
    pygame.draw.rect(shadow_surf, (*THEME["card_shadow"], 100),
                    (0, 0, shadow_rect.width, shadow_rect.height),
                    border_radius=border_radius)
    surface.blit(shadow_surf, shadow_rect.topleft)

    # 绘制卡片
    pygame.draw.rect(surface, bg_color, rect, border_radius=border_radius)

    # 绘制边框
    if border_color and border_width > 0:
        pygame.draw.rect(surface, border_color, rect, border_width, border_radius=border_radius)


class UIRenderer:
    """UI渲染器"""
    
    @staticmethod
    def draw_hud(surface, game, translucent: bool):
        """绘制HUD - 现代卡片式设计"""
        # 顶部面板 - 使用渐变背景
        if translucent:
            top_panel = pygame.Surface((WIDTH, 100), pygame.SRCALPHA)
            # 渐变背景
            for y in range(100):
                alpha = int(240 - y * 0.8)
                color = (*THEME["white"], alpha)
                pygame.draw.line(top_panel, color, (0, y), (WIDTH, y))
            surface.blit(top_panel, (0, 0))

        # 游戏标题 - 左侧
        title_text = "旋转除草"
        title = header_font.render(title_text, True, THEME["primary"])
        surface.blit(title, (25, 20))

        # 添加副标题
        subtitle = small_font.render("Weed Cutter", True, THEME["mid_gray"])
        surface.blit(subtitle, (25, 55))

        # 右上角信息卡片组
        card_x = WIDTH - 500
        card_y = 15
        card_spacing = 10

        # 玩家信息卡片
        if game.blockchain_manager.blockchain_available:
            player_info = f"玩家: {game.blockchain_manager.account[:6]}...{game.blockchain_manager.account[-4:]}"
            player_color = THEME["primary"]
        else:
            player_info = "离线模式"
            player_color = THEME["mid_gray"]

        player_surf = default_font.render(player_info, True, player_color)
        player_rect = pygame.Rect(card_x, card_y, player_surf.get_width() + 20, 30)

        # 半透明背景
        card_bg = pygame.Surface((player_rect.width, player_rect.height), pygame.SRCALPHA)
        card_bg.fill((*THEME["white"], 200))
        surface.blit(card_bg, player_rect.topleft)
        pygame.draw.rect(surface, THEME["primary_light"], player_rect, 1, border_radius=5)
        surface.blit(player_surf, (card_x + 10, card_y + 7))

        # 统计信息栏 - 第二行
        stats_y = card_y + 40
        stat_items = []

        # 分数
        score_text = f"分数: {game.score}"
        if game.pending_points > 0:
            score_text += f" (+{game.pending_points}*)"
        stat_items.append((score_text, THEME["text"], "🏆"))

        # 金币
        stat_items.append((f"金币: {game.coins}", THEME["accent"], "💰"))

        # 武器数
        stat_items.append((f"武器: {len(game.weapons)}", THEME["text"], "⚔️"))

        # 绘制统计卡片
        current_x = 200
        for text, color, icon in stat_items:
            # 创建文本（不使用emoji字体避免问题）
            icon_text = small_font.render(icon.replace("🏆", "[分]").replace("💰", "[币]").replace("⚔️", "[武]"), True, color)
            value_text = default_font.render(text.split(": ")[1] if ": " in text else text, True, color)
            label_text = small_font.render(text.split(": ")[0] if ": " in text else "", True, THEME["mid_gray"])

            # 卡片尺寸
            card_width = max(value_text.get_width(), label_text.get_width()) + 50
            card_height = 50
            stat_rect = pygame.Rect(current_x, stats_y, card_width, card_height)

            # 绘制卡片背景
            card_surf = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
            card_surf.fill((*THEME["white"], 220))
            surface.blit(card_surf, (current_x, stats_y))
            pygame.draw.rect(surface, THEME["light_gray"], stat_rect, 1, border_radius=8)

            # 绘制内容
            surface.blit(label_text, (current_x + 10, stats_y + 8))
            surface.blit(value_text, (current_x + 10, stats_y + 25))

            current_x += card_width + card_spacing

        # 提示信息
        if game.pending_points > 0:
            hint = small_font.render("*待上链", True, THEME["danger"])
            hint_rect = pygame.Rect(current_x, stats_y + 15, hint.get_width() + 15, 25)
            hint_surf = pygame.Surface((hint_rect.width, hint_rect.height), pygame.SRCALPHA)
            hint_surf.fill((*THEME["danger_light"], 150))
            surface.blit(hint_surf, hint_rect.topleft)
            pygame.draw.rect(surface, THEME["danger"], hint_rect, 1, border_radius=5)
            surface.blit(hint, (current_x + 8, stats_y + 18))

        # 站在草上的加成提示
        if game.standing_grass_id is not None:
            bonus_text = "命中加成 +10%"
            bonus_surf = small_font.render(bonus_text, True, THEME["success"])
            bonus_rect = pygame.Rect(WIDTH - 150, 65, bonus_surf.get_width() + 20, 25)
            bonus_bg = pygame.Surface((bonus_rect.width, bonus_rect.height), pygame.SRCALPHA)
            bonus_bg.fill((*THEME["secondary_light"], 180))
            surface.blit(bonus_bg, bonus_rect.topleft)
            pygame.draw.rect(surface, THEME["secondary"], bonus_rect, 1, border_radius=5)
            surface.blit(bonus_surf, (bonus_rect.x + 10, bonus_rect.y + 5))

        # 底部控制栏 - 使用渐变
        if translucent:
            bottom_panel = pygame.Surface((WIDTH, 35), pygame.SRCALPHA)
            for y in range(35):
                alpha = int(210 + y * 1.3)
                color = (*THEME["white"], min(alpha, 240))
                pygame.draw.line(bottom_panel, color, (0, y), (WIDTH, y))
            surface.blit(bottom_panel, (0, HEIGHT - 35))

        # 控制提示 - 更清晰的布局
        controls = [
            ("WASD/方向键", "移动"),
            ("空格", "攻击"),
            ("N", "铸造"),
            ("M", "市场"),
            ("I", "背包"),
            ("R", "重置"),
            ("ESC", "返回")
        ]

        controls_text = "  |  ".join([f"{key}: {action}" for key, action in controls])
        controls_surf = small_font.render(controls_text, True, THEME["dark_gray"])
        surface.blit(controls_surf, (WIDTH // 2 - controls_surf.get_width() // 2, HEIGHT - 25))

        # 错误/警告信息 - 醒目的提示卡片
        error_y = 110
        if not game.blockchain_manager.blockchain_available and game.blockchain_manager.offline_reason:
            warn_text = f"离线: {game.blockchain_manager.offline_reason}"
            warn_surf = default_font.render(warn_text, True, THEME["white"])
            warn_rect = pygame.Rect(20, error_y, warn_surf.get_width() + 30, 35)

            # 警告背景
            warn_bg = pygame.Surface((warn_rect.width, warn_rect.height), pygame.SRCALPHA)
            warn_bg.fill((*THEME["danger"], 200))
            surface.blit(warn_bg, warn_rect.topleft)
            pygame.draw.rect(surface, THEME["danger_light"], warn_rect, 2, border_radius=8)

            # 警告图标
            icon_text = default_font.render("!", True, THEME["white"])
            surface.blit(icon_text, (warn_rect.x + 10, warn_rect.y + 8))
            surface.blit(warn_surf, (warn_rect.x + 25, warn_rect.y + 8))
            error_y += 45

        if game.tile_map_error:
            map_warn_text = f"地图: {game.tile_map_error[:40]}..."
            map_warn_surf = small_font.render(map_warn_text, True, THEME["white"])
            map_warn_rect = pygame.Rect(20, error_y, map_warn_surf.get_width() + 25, 30)

            map_warn_bg = pygame.Surface((map_warn_rect.width, map_warn_rect.height), pygame.SRCALPHA)
            map_warn_bg.fill((*THEME["accent"], 200))
            surface.blit(map_warn_bg, map_warn_rect.topleft)
            pygame.draw.rect(surface, THEME["accent_light"], map_warn_rect, 1, border_radius=6)
            surface.blit(map_warn_surf, (map_warn_rect.x + 12, map_warn_rect.y + 8))

    @staticmethod
    def draw_inventory(surface, game):
        """绘制背包界面 - 现代网格卡片设计"""
        surface.fill(THEME["background"])

        # 渐变标题栏
        title_rect = pygame.Rect(0, 0, WIDTH, 100)
        draw_gradient_rect(surface, title_rect, THEME["primary"], THEME["primary_light"])

        # 标题
        title_text = "我的背包"
        title = title_font.render(title_text, True, THEME["white"])
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 30))

        if not game.weapons:
            empty_card = pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2 - 60, 400, 120)
            draw_card_with_shadow(surface, empty_card, THEME["card_bg"], THEME["light_gray"], 2, 15)

            icon_text = header_font.render("🎒", True, THEME["mid_gray"])
            empty_text = default_font.render("暂无武器", True, THEME["text"])
            hint_text = small_font.render("去市场或游戏中收集吧!", True, THEME["mid_gray"])

            surface.blit(icon_text, (WIDTH // 2 - icon_text.get_width() // 2, HEIGHT // 2 - 40))
            surface.blit(empty_text, (WIDTH // 2 - empty_text.get_width() // 2, HEIGHT // 2))
            surface.blit(hint_text, (WIDTH // 2 - hint_text.get_width() // 2, HEIGHT // 2 + 35))
        else:
            start_y = 120
            line_height = 90
            max_visible = 6
            offset = max(0, game.inventory_selection - max_visible + 1)

            for idx in range(offset, min(len(game.weapons), offset + max_visible)):
                weapon = game.weapons[idx]
                y = start_y + (idx - offset) * line_height

                card_rect = pygame.Rect(80, y, WIDTH - 160, line_height - 10)

                # 选中状态
                is_selected = idx == game.inventory_selection
                bg_color = THEME["highlight"] if is_selected else THEME["card_bg"]
                border_color = THEME["primary"] if is_selected else THEME["light_gray"]
                border_width = 3 if is_selected else 1

                # 绘制卡片
                draw_card_with_shadow(surface, card_rect, bg_color, border_color, border_width, 12)

                # 稀有度色条
                rarity_color = game.get_rarity_color(weapon['rarity'])
                rarity_bar = pygame.Rect(card_rect.x + 8, card_rect.y + 10, 6, card_rect.height - 20)
                pygame.draw.rect(surface, rarity_color, rarity_bar, border_radius=3)

                # 布局：从左到右分区
                # 区域1：武器图片 (左侧)
                sprite_x = card_rect.x + 30
                sprite = game.weapon_manager.get_weapon_sprite(weapon)
                if sprite:
                    # 缩放武器图片
                    scale_factor = 1.5
                    scaled_sprite = pygame.transform.scale(
                        sprite,
                        (int(sprite.get_width() * scale_factor), int(sprite.get_height() * scale_factor))
                    )
                    sprite_rect = scaled_sprite.get_rect(center=(sprite_x + 40, card_rect.centery))
                    surface.blit(scaled_sprite, sprite_rect)

                # 区域2：基本信息 (中左)
                info_x = sprite_x + 90
                info_y = card_rect.y + 15

                # ID
                id_text = small_font.render(f"#{weapon['id']:03d}", True, THEME["mid_gray"])
                surface.blit(id_text, (info_x, info_y))

                # 武器名称
                name_text = default_font.render(weapon['name'], True, rarity_color)
                surface.blit(name_text, (info_x, info_y + 25))

                # 区域3：属性信息 (中右)
                attr_x = info_x + 280
                attr_y = card_rect.y + 12

                # 稀有度标签
                rarity_names = {0: "普通", 1: "稀有", 2: "史诗", 3: "传说"}
                rarity_name = rarity_names.get(weapon['rarity'].value, "未知")
                rarity_badge = pygame.Rect(attr_x, attr_y, 70, 24)
                pygame.draw.rect(surface, rarity_color, rarity_badge, border_radius=5)
                rarity_text = small_font.render(rarity_name, True, THEME["white"])
                rarity_text_x = rarity_badge.centerx - rarity_text.get_width() // 2
                surface.blit(rarity_text, (rarity_text_x, rarity_badge.y + 5))

                # 伤害信息
                damage_text = small_font.render(f"伤害: {weapon['damage_multiplier']:.1f}x", True, THEME["text"])
                surface.blit(damage_text, (attr_x, attr_y + 30))

                # 磨损度信息
                if weapon.get('wear') is not None:
                    from .utils import get_condition_name
                    condition_str = get_condition_name(weapon['wear']).split('(')[0].strip()
                    wear_text = small_font.render(f"品相: {condition_str}", True, THEME["info"])
                    surface.blit(wear_text, (attr_x, attr_y + 50))

                # 区域4：状态标记 (右侧)
                status_x = card_rect.right - 100
                status_y = card_rect.centery - 12

                if idx == game.current_weapon_index:
                    equipped_badge = pygame.Rect(status_x, status_y, 80, 26)
                    pygame.draw.rect(surface, THEME["success"], equipped_badge, border_radius=6)
                    equipped_text = small_font.render("已装备", True, THEME["white"])
                    equipped_text_x = equipped_badge.centerx - equipped_text.get_width() // 2
                    surface.blit(equipped_text, (equipped_text_x, equipped_badge.y + 6))

        # 底部操作栏
        bottom_rect = pygame.Rect(0, HEIGHT - 80, WIDTH, 80)
        pygame.draw.rect(surface, THEME["white"], bottom_rect)
        pygame.draw.line(surface, THEME["light_gray"], (0, HEIGHT - 80), (WIDTH, HEIGHT - 80), 2)

        # 操作按钮提示
        hints = [
            ("↑↓", "选择", THEME["primary"]),
            ("Enter", "切换装备", THEME["secondary"]),
            ("L", "上架出售", THEME["accent"]),
            ("I/ESC", "返回", THEME["mid_gray"])
        ]

        hint_x = 150
        for key, action, color in hints:
            # 按键背景
            key_rect = pygame.Rect(hint_x, HEIGHT - 55, len(key) * 15 + 10, 30)
            pygame.draw.rect(surface, color, key_rect, border_radius=5)

            key_text = default_font.render(key, True, THEME["white"])
            surface.blit(key_text, (key_rect.x + 8, key_rect.y + 5))

            action_text = default_font.render(action, True, THEME["text"])
            surface.blit(action_text, (key_rect.right + 10, HEIGHT - 50))

            hint_x += key_rect.width + action_text.get_width() + 40

        # 上架输入框 - 现代对话框设计
        if game.listing_input_active:
            # 半透明遮罩
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            surface.blit(overlay, (0, 0))

            # 对话框
            dialog_rect = pygame.Rect(WIDTH // 2 - 250, HEIGHT // 2 - 80, 500, 160)
            draw_card_with_shadow(surface, dialog_rect, THEME["white"], THEME["primary"], 3, 20)

            # 标题
            title_text = header_font.render("设置价格", True, THEME["primary"])
            surface.blit(title_text, (dialog_rect.x + 30, dialog_rect.y + 25))

            # 输入框
            input_rect = pygame.Rect(dialog_rect.x + 30, dialog_rect.y + 70, 440, 45)
            pygame.draw.rect(surface, THEME["background"], input_rect, border_radius=8)
            pygame.draw.rect(surface, THEME["primary"], input_rect, 2, border_radius=8)

            prompt_text = f"{game.listing_input_text}_ ETH"
            prompt_surf = header_font.render(prompt_text, True, THEME["primary"])
            surface.blit(prompt_surf, (input_rect.x + 15, input_rect.y + 8))

            # 取消提示
            esc_hint = small_font.render("按 ESC 取消", True, THEME["mid_gray"])
            surface.blit(esc_hint, (dialog_rect.x + 30, dialog_rect.y + 125))

        # 反馈信息
        if game.inventory_feedback:
            feedback_rect = pygame.Rect(WIDTH // 2 - 200, HEIGHT - 120, 400, 40)
            feedback_bg = pygame.Surface((feedback_rect.width, feedback_rect.height), pygame.SRCALPHA)
            feedback_bg.fill((*THEME["success"], 200))
            surface.blit(feedback_bg, feedback_rect.topleft)
            pygame.draw.rect(surface, THEME["success"], feedback_rect, 2, border_radius=8)

            feedback_surf = default_font.render(game.inventory_feedback, True, THEME["white"])
            surface.blit(feedback_surf, (WIDTH // 2 - feedback_surf.get_width() // 2, HEIGHT - 110))

    @staticmethod
    def draw_marketplace(surface, game):
        """绘制市场界面 - 现代购物体验"""
        surface.fill(THEME["background"])

        # 渐变标题栏
        title_rect = pygame.Rect(0, 0, WIDTH, 100)
        draw_gradient_rect(surface, title_rect, THEME["secondary"], THEME["secondary_light"])

        title_text = "武器市场"
        title = title_font.render(title_text, True, THEME["white"])
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 30))

        if not game.market_weapons:
            # 空状态卡片
            empty_card = pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2 - 60, 400, 120)
            draw_card_with_shadow(surface, empty_card, THEME["card_bg"], THEME["light_gray"], 2, 15)

            icon_text = header_font.render("🏪", True, THEME["mid_gray"])
            empty_text = default_font.render("当前没有上架的武器", True, THEME["text"])
            hint_text = small_font.render("等待其他玩家上架或自己上架武器吧!", True, THEME["mid_gray"])

            surface.blit(icon_text, (WIDTH // 2 - icon_text.get_width() // 2, HEIGHT // 2 - 40))
            surface.blit(empty_text, (WIDTH // 2 - empty_text.get_width() // 2, HEIGHT // 2))
            surface.blit(hint_text, (WIDTH // 2 - hint_text.get_width() // 2, HEIGHT // 2 + 35))
        else:
            start_y = 120
            line_height = 95
            max_visible = 6
            offset = max(0, game.market_selection - max_visible + 1)
            
            for idx in range(offset, min(len(game.market_weapons), offset + max_visible)):
                weapon = game.market_weapons[idx]
                y = start_y + (idx - offset) * line_height

                card_rect = pygame.Rect(70, y, WIDTH - 140, line_height - 10)

                is_selected = idx == game.market_selection
                bg_color = THEME["highlight"] if is_selected else THEME["card_bg"]
                border_color = THEME["secondary"] if is_selected else THEME["light_gray"]
                border_width = 3 if is_selected else 1

                # 绘制卡片
                draw_card_with_shadow(surface, card_rect, bg_color, border_color, border_width, 15)

                # 稀有度色条
                rarity_color = game.get_rarity_color(weapon['rarity'])
                rarity_bar = pygame.Rect(card_rect.x + 10, card_rect.y + 12, 6, card_rect.height - 24)
                pygame.draw.rect(surface, rarity_color, rarity_bar, border_radius=3)

                # 布局：从左到右分区
                # 区域1：武器图片 (左侧)
                sprite_x = card_rect.x + 30
                sprite = game.weapon_manager.get_weapon_sprite(weapon)
                if sprite:
                    scale_factor = 1.5
                    scaled_sprite = pygame.transform.scale(
                        sprite,
                        (int(sprite.get_width() * scale_factor), int(sprite.get_height() * scale_factor))
                    )
                    sprite_rect = scaled_sprite.get_rect(center=(sprite_x + 40, card_rect.centery))
                    surface.blit(scaled_sprite, sprite_rect)

                # 区域2：基本信息 (中左)
                info_x = sprite_x + 90
                info_y = card_rect.y + 12

                # ID
                id_text = small_font.render(f"#{weapon['id']:03d}", True, THEME["mid_gray"])
                surface.blit(id_text, (info_x, info_y))

                # 武器名称
                name_text = default_font.render(weapon['name'], True, rarity_color)
                surface.blit(name_text, (info_x, info_y + 22))

                # 卖家信息
                owner_short = f"{weapon['owner'][:10]}..."
                owner_text = small_font.render(f"卖家: {owner_short}", True, THEME["mid_gray"])
                surface.blit(owner_text, (info_x, info_y + 50))

                # 区域3：属性标签 (中)
                attr_x = info_x + 280
                attr_y = card_rect.y + 15

                # 稀有度标签
                rarity_names = {0: "普通", 1: "稀有", 2: "史诗", 3: "传说"}
                rarity_name = rarity_names.get(weapon['rarity'].value, "未知")
                rarity_badge = pygame.Rect(attr_x, attr_y, 70, 24)
                pygame.draw.rect(surface, rarity_color, rarity_badge, border_radius=5)
                rarity_text = small_font.render(rarity_name, True, THEME["white"])
                rarity_text_x = rarity_badge.centerx - rarity_text.get_width() // 2
                surface.blit(rarity_text, (rarity_text_x, rarity_badge.y + 5))

                # 磨损度信息
                if weapon.get('wear') is not None:
                    from .utils import get_condition_name
                    condition_str = get_condition_name(weapon['wear']).split('(')[0].strip()
                    wear_text = small_font.render(condition_str, True, THEME["white"])
                    # 根据文字宽度调整标签宽度
                    wear_badge_width = max(70, wear_text.get_width() + 16)
                    wear_badge = pygame.Rect(attr_x, attr_y + 32, wear_badge_width, 24)
                    pygame.draw.rect(surface, THEME["info"], wear_badge, border_radius=5)
                    wear_text_x = wear_badge.centerx - wear_text.get_width() // 2
                    surface.blit(wear_text, (wear_text_x, wear_badge.y + 5))

                # 区域4：价格 (右侧)
                price_x = card_rect.right - 150
                price_y = card_rect.centery - 18

                if weapon.get('coin_price', 0) > 0:
                    price_text = f"{weapon['coin_price']} 金币"
                    price_color = THEME["accent"]
                else:
                    eth_price = game.blockchain_manager.w3.from_wei(weapon['price'], 'ether')
                    price_text = f"{eth_price:.4f} ETH"
                    price_color = THEME["primary"]

                price_badge = pygame.Rect(price_x, price_y, 130, 36)
                pygame.draw.rect(surface, price_color, price_badge, border_radius=8)
                price_surf = default_font.render(price_text, True, THEME["white"])
                price_surf_x = price_badge.centerx - price_surf.get_width() // 2
                surface.blit(price_surf, (price_surf_x, price_badge.y + 8))

        # 底部信息栏
        bottom_rect = pygame.Rect(0, HEIGHT - 90, WIDTH, 90)
        pygame.draw.rect(surface, THEME["white"], bottom_rect)
        pygame.draw.line(surface, THEME["light_gray"], (0, HEIGHT - 90), (WIDTH, HEIGHT - 90), 2)

        # 你的金币 - 突出显示
        coin_card = pygame.Rect(30, HEIGHT - 70, 200, 50)
        pygame.draw.rect(surface, THEME["accent_light"], coin_card, border_radius=10)

        coin_label = small_font.render("你的金币", True, THEME["text"])
        coin_value = header_font.render(str(game.coins), True, THEME["accent"])
        surface.blit(coin_label, (coin_card.x + 15, coin_card.y + 8))
        surface.blit(coin_value, (coin_card.x + 15, coin_card.y + 25))

        # 操作提示
        hints = [
            ("↑↓", "选择", THEME["secondary"]),
            ("Enter", "购买", THEME["primary"]),
            ("R", "刷新", THEME["accent"]),
            ("M/ESC", "返回", THEME["mid_gray"])
        ]

        hint_x = 300
        for key, action, color in hints:
            key_rect = pygame.Rect(hint_x, HEIGHT - 60, len(key) * 15 + 10, 30)
            pygame.draw.rect(surface, color, key_rect, border_radius=5)

            key_text = default_font.render(key, True, THEME["white"])
            surface.blit(key_text, (key_rect.x + 8, key_rect.y + 5))

            action_text = default_font.render(action, True, THEME["text"])
            surface.blit(action_text, (key_rect.right + 10, HEIGHT - 55))

            hint_x += key_rect.width + action_text.get_width() + 35

        # 刷新时间标签
        if game.market_last_refresh_ms:
            secs = max(0, (pygame.time.get_ticks() - game.market_last_refresh_ms) // 1000)
            refresh_text = f"更新于 {secs}秒前"
            refresh_surf = small_font.render(refresh_text, True, THEME["mid_gray"])
            refresh_rect = pygame.Rect(WIDTH - 180, HEIGHT - 60, 160, 30)
            pygame.draw.rect(surface, THEME["light_gray"], refresh_rect, border_radius=8)
            surface.blit(refresh_surf, (refresh_rect.x + 15, refresh_rect.y + 8))

    @staticmethod
    def draw_start_menu(surface, game, selection):
        """绘制开始菜单 - 现代欢迎页面"""
        # 渐变背景
        bg_rect = pygame.Rect(0, 0, WIDTH, HEIGHT)
        draw_gradient_rect(surface, bg_rect, THEME["background"], THEME["white"], vertical=True)

        # 游戏标题 - 大标题效果
        title_y = 100
        title = title_font.render("区块链除草游戏", True, THEME["primary"])
        title_shadow = title_font.render("区块链除草游戏", True, THEME["light_gray"])
        surface.blit(title_shadow, (WIDTH // 2 - title.get_width() // 2 + 3, title_y + 3))
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, title_y))

        # 英文副标题
        subtitle = header_font.render("Blockchain Weed Cutter", True, THEME["mid_gray"])
        surface.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, title_y + 60))

        # 装饰线
        line_y = title_y + 110
        pygame.draw.line(surface, THEME["primary_light"],
                        (WIDTH // 2 - 100, line_y),
                        (WIDTH // 2 + 100, line_y), 3)

        # 菜单选项 - 现代按钮设计
        menu_items = [
            ("个人中心", "查看你的资料和成就", THEME["primary"]),
            ("开始游戏", "进入游戏世界", THEME["secondary"]),
            ("排行榜", "查看全球玩家排名", THEME["accent"]),
            ("切换账户", "选择其他账户进行游戏", THEME["dark_gray"])
        ]
        start_y = 260
        button_height = 70
        button_spacing = 20

        for idx, (text, desc, color) in enumerate(menu_items):
            y = start_y + idx * (button_height + button_spacing)
            button_rect = pygame.Rect(WIDTH // 2 - 280, y, 560, button_height)

            is_selected = idx == selection

            if is_selected:
                # 选中状态 - 渐变按钮
                draw_gradient_rect(surface, button_rect, color,
                                 tuple(min(c + 40, 255) for c in color))
                text_color = THEME["white"]
                desc_color = THEME["white"]

                # 发光效果
                glow_rect = button_rect.inflate(6, 6)
                glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (*color, 50), (0, 0, glow_rect.width, glow_rect.height),
                               border_radius=15)
                surface.blit(glow_surf, glow_rect.topleft)
            else:
                # 未选中状态
                bg_color = THEME["white"]
                draw_card_with_shadow(surface, button_rect, bg_color, THEME["light_gray"], 1, 12)
                text_color = THEME["text"]
                desc_color = THEME["mid_gray"]

            # 绘制边框
            pygame.draw.rect(surface, color if is_selected else THEME["light_gray"],
                           button_rect, 2 if is_selected else 1, border_radius=12)

            # 文本内容 - 居中对齐
            text_surf = header_font.render(text, True, text_color)
            text_x = button_rect.centerx - text_surf.get_width() // 2
            text_y = button_rect.y + 18
            surface.blit(text_surf, (text_x, text_y))

            # 描述文字 - 居中，字体更小
            desc_surf = small_font.render(desc, True, desc_color)
            desc_x = button_rect.centerx - desc_surf.get_width() // 2
            surface.blit(desc_surf, (desc_x, text_y + 35))

            # 右侧箭头（选中时）
            if is_selected:
                arrow = header_font.render("→", True, text_color)
                surface.blit(arrow, (button_rect.right - 50, button_rect.y + 25))

        # 底部信息栏
        bottom_rect = pygame.Rect(0, HEIGHT - 80, WIDTH, 80)
        pygame.draw.rect(surface, THEME["white"], bottom_rect)
        pygame.draw.line(surface, THEME["light_gray"], (0, HEIGHT - 80), (WIDTH, HEIGHT - 80), 2)

        # 操作提示
        hints = [
            ("↑↓", "选择"),
            ("Enter", "确认"),
            ("ESC", "退出")
        ]

        hint_x = WIDTH // 2 - 150
        for key, action in hints:
            key_rect = pygame.Rect(hint_x, HEIGHT - 55, len(key) * 15 + 10, 30)
            pygame.draw.rect(surface, THEME["primary"], key_rect, border_radius=5)

            key_text = default_font.render(key, True, THEME["white"])
            surface.blit(key_text, (key_rect.x + 8, key_rect.y + 5))

            action_text = default_font.render(action, True, THEME["text"])
            surface.blit(action_text, (key_rect.right + 10, HEIGHT - 50))

            hint_x += key_rect.width + action_text.get_width() + 30

        # 区块链状态指示器
        status_rect = pygame.Rect(30, HEIGHT - 55, 200, 35)
        if game.blockchain_manager.blockchain_available:
            status_bg = THEME["success"]
            status_text = "已连接区块链"
            status_icon = "✓"
        else:
            status_bg = THEME["danger"]
            status_text = "离线模式"
            status_icon = "!"

        pygame.draw.rect(surface, status_bg, status_rect, border_radius=8)

        icon_surf = header_font.render(status_icon, True, THEME["white"])
        surface.blit(icon_surf, (status_rect.x + 12, status_rect.y + 5))

        status_surf = default_font.render(status_text, True, THEME["white"])
        surface.blit(status_surf, (status_rect.x + 40, status_rect.y + 8))

    @staticmethod
    def draw_profile(surface, game):
        """绘制个人中心 - 现代仪表盘设计"""
        # 渐变背景
        bg_rect = pygame.Rect(0, 0, WIDTH, HEIGHT)
        draw_gradient_rect(surface, bg_rect, THEME["background"], THEME["white"])

        # 标题栏
        title_rect = pygame.Rect(0, 0, WIDTH, 90)
        draw_gradient_rect(surface, title_rect, THEME["primary"], THEME["primary_light"])

        title = title_font.render("个人中心", True, THEME["white"])
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 25))

        # 主信息卡片
        main_card = pygame.Rect(WIDTH // 2 - 500, 120, 1000, 480)
        draw_card_with_shadow(surface, main_card, THEME["white"], THEME["light_gray"], 0, 20)

        # 头像区域（左侧）
        avatar_rect = pygame.Rect(main_card.x + 40, main_card.y + 40, 280, 400)
        pygame.draw.rect(surface, THEME["background"], avatar_rect, border_radius=15)
        pygame.draw.rect(surface, THEME["primary_light"], avatar_rect, 2, border_radius=15)

        # 玩家名称
        name_display = game.player_name if not game.profile_editing_name else f"{game.profile_name_input}_"
        name_surf = header_font.render(name_display, True, THEME["primary"])
        name_x = avatar_rect.x + (avatar_rect.width - name_surf.get_width()) // 2
        surface.blit(name_surf, (name_x, avatar_rect.y + 30))

        # 地址
        addr_short = f"{game.blockchain_manager.account[:10]}...{game.blockchain_manager.account[-6:]}"
        addr_surf = small_font.render(addr_short, True, THEME["mid_gray"])
        addr_x = avatar_rect.x + (avatar_rect.width - addr_surf.get_width()) // 2
        surface.blit(addr_surf, (addr_x, avatar_rect.y + 70))

        # 排名徽章
        rank_y = avatar_rect.y + 120
        if game.total_players > 0:
            rank_circle = pygame.Rect(avatar_rect.x + 90, rank_y, 100, 100)
            pygame.draw.circle(surface, THEME["accent"], rank_circle.center, 50)
            pygame.draw.circle(surface, THEME["accent_light"], rank_circle.center, 50, 3)

            rank_num = title_font.render(f"#{game.player_rank}", True, THEME["white"])
            rank_x = rank_circle.centerx - rank_num.get_width() // 2
            rank_y_text = rank_circle.centery - rank_num.get_height() // 2
            surface.blit(rank_num, (rank_x, rank_y_text))

            total_text = small_font.render(f"/ {game.total_players}", True, THEME["mid_gray"])
            total_x = avatar_rect.x + (avatar_rect.width - total_text.get_width()) // 2
            surface.blit(total_text, (total_x, rank_y + 110))

        # 统计卡片区域（右侧）
        stats_x = main_card.x + 360
        stats_y = main_card.y + 40

        # 统计数据
        stats_items = [
            ("金币", str(game.coins), THEME["accent"], "💰"),
            ("总分数", str(game.score), THEME["primary"], "🏆"),
            ("武器数量", str(len(game.weapons)), THEME["secondary"], "⚔️"),
        ]

        for i, (label, value, color, icon) in enumerate(stats_items):
            stat_card = pygame.Rect(stats_x + (i % 2) * 310,
                                   stats_y + (i // 2) * 120,
                                   280, 100)

            # 卡片背景
            pygame.draw.rect(surface, THEME["background"], stat_card, border_radius=12)
            pygame.draw.rect(surface, color, stat_card, 2, border_radius=12)

            # 图标背景
            icon_bg = pygame.Rect(stat_card.x + 15, stat_card.y + 15, 50, 50)
            pygame.draw.rect(surface, color, icon_bg, border_radius=10)

            # 图标（使用文本代替emoji）
            icon_text = header_font.render(icon.replace("💰", "$").replace("🏆", "★").replace("⚔️", "⚔"),
                                          True, THEME["white"])
            icon_x = icon_bg.centerx - icon_text.get_width() // 2
            icon_y = icon_bg.centery - icon_text.get_height() // 2
            surface.blit(icon_text, (icon_x, icon_y))

            # 标签和值
            label_surf = small_font.render(label, True, THEME["mid_gray"])
            surface.blit(label_surf, (stat_card.x + 80, stat_card.y + 20))

            value_surf = title_font.render(value, True, color)
            surface.blit(value_surf, (stat_card.x + 80, stat_card.y + 45))

        # 当前装备卡片
        weapon_card = pygame.Rect(stats_x, stats_y + 260, 600, 160)
        weapon = game.get_current_weapon()
        rarity_color = game.get_rarity_color(weapon['rarity'])

        draw_card_with_shadow(surface, weapon_card, THEME["background"], rarity_color, 3, 15)

        # 装备标题
        equip_label = default_font.render("当前装备", True, THEME["mid_gray"])
        surface.blit(equip_label, (weapon_card.x + 25, weapon_card.y + 15))

        # 武器图片（左侧）
        sprite = game.weapon_manager.get_weapon_sprite(weapon)
        if sprite:
            scale_factor = 2.0
            scaled_sprite = pygame.transform.scale(
                sprite,
                (int(sprite.get_width() * scale_factor), int(sprite.get_height() * scale_factor))
            )
            sprite_rect = scaled_sprite.get_rect(center=(weapon_card.x + 80, weapon_card.y + 95))
            surface.blit(scaled_sprite, sprite_rect)

        # 武器信息（右侧，避免重叠）
        info_x = weapon_card.x + 150

        # 武器名称
        weapon_name = default_font.render(weapon['name'], True, rarity_color)
        surface.blit(weapon_name, (info_x, weapon_card.y + 50))

        # 武器属性（换行显示）
        rarity_text = f"稀有度: {weapon['rarity'].name}"
        rarity_surf = small_font.render(rarity_text, True, THEME["text"])
        surface.blit(rarity_surf, (info_x, weapon_card.y + 80))

        damage_text = f"伤害倍率: x{weapon['damage_multiplier']:.1f}"
        damage_surf = small_font.render(damage_text, True, THEME["text"])
        surface.blit(damage_surf, (info_x, weapon_card.y + 105))

        # 稀有度指示条
        rarity_bar = pygame.Rect(weapon_card.right - 15, weapon_card.y + 15, 8, weapon_card.height - 30)
        pygame.draw.rect(surface, rarity_color, rarity_bar, border_radius=4)

        # 底部操作栏
        bottom_rect = pygame.Rect(0, HEIGHT - 80, WIDTH, 80)
        pygame.draw.rect(surface, THEME["white"], bottom_rect)
        pygame.draw.line(surface, THEME["light_gray"], (0, HEIGHT - 80), (WIDTH, HEIGHT - 80), 2)

        # 操作提示
        if game.profile_editing_name:
            hint_text = "输入名称后按 Enter 保存  |  ESC 取消"
            hint_color = THEME["primary"]
            hint_surf = default_font.render(hint_text, True, hint_color)
            surface.blit(hint_surf, (WIDTH // 2 - hint_surf.get_width() // 2, HEIGHT - 50))
        else:
            hints = [
                ("N", "修改名称", THEME["primary"]),
                ("I", "查看背包", THEME["secondary"]),
                ("ESC", "返回", THEME["mid_gray"])
            ]

            hint_x = WIDTH // 2 - 200
            for key, action, color in hints:
                key_rect = pygame.Rect(hint_x, HEIGHT - 55, len(key) * 15 + 10, 30)
                pygame.draw.rect(surface, color, key_rect, border_radius=5)

                key_text = default_font.render(key, True, THEME["white"])
                # 按键文字居中
                key_text_x = key_rect.centerx - key_text.get_width() // 2
                surface.blit(key_text, (key_text_x, key_rect.y + 5))

                action_text = default_font.render(action, True, THEME["text"])
                surface.blit(action_text, (key_rect.right + 10, HEIGHT - 50))

                hint_x += key_rect.width + action_text.get_width() + 35

    @staticmethod
    def draw_leaderboard(surface, game):
        """绘制排行榜 - 现代竞技榜设计"""
        # 渐变背景
        bg_rect = pygame.Rect(0, 0, WIDTH, HEIGHT)
        draw_gradient_rect(surface, bg_rect, THEME["background"], THEME["white"])

        # 标题栏
        title_rect = pygame.Rect(0, 0, WIDTH, 90)
        draw_gradient_rect(surface, title_rect, THEME["accent"], THEME["accent_light"])

        title = title_font.render("全球排行榜", True, THEME["white"])
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 25))

        # 表头卡片
        header_rect = pygame.Rect(60, 110, WIDTH - 120, 50)
        pygame.draw.rect(surface, THEME["white"], header_rect, border_radius=10)
        pygame.draw.line(surface, THEME["light_gray"], (60, 140), (WIDTH - 60, 140), 1)

        headers = ["排名", "玩家名称", "钱包地址", "总分"]
        col_x = [100, 280, 600, 950]
        for i, header in enumerate(headers):
            header_surf = default_font.render(header, True, THEME["dark_gray"])
            surface.blit(header_surf, (col_x[i], 122))

        # 排行榜内容
        start_y = 180
        line_height = 60
        max_visible = 9
        offset = max(0, game.leaderboard_selection - max_visible + 1)

        for idx in range(offset, min(len(game.leaderboard), offset + max_visible)):
            entry = game.leaderboard[idx]
            y = start_y + (idx - offset) * line_height

            is_current = entry['address'].lower() == game.blockchain_manager.account.lower()
            is_selected = idx == game.leaderboard_selection

            row_rect = pygame.Rect(60, y, WIDTH - 120, line_height - 8)

            # 背景色
            if is_selected:
                bg_color = THEME["highlight"]
                border_color = THEME["primary"]
                border_width = 3
            elif is_current:
                bg_color = (240, 250, 255)  # 浅蓝色
                border_color = THEME["secondary"]
                border_width = 2
            else:
                bg_color = THEME["white"]
                border_color = THEME["light_gray"]
                border_width = 1

            draw_card_with_shadow(surface, row_rect, bg_color, border_color, border_width, 10)

            # 排名显示
            rank = entry['rank']
            rank_x = col_x[0]

            if rank <= 3:
                # 前三名使用奖牌背景
                medal_colors = [
                    THEME["accent"],      # 金牌
                    (192, 192, 192),      # 银牌
                    (205, 127, 50)        # 铜牌
                ]
                medal_color = medal_colors[rank - 1]

                # 奖牌圆形背景
                medal_center = (rank_x + 20, y + line_height // 2 - 4)
                pygame.draw.circle(surface, medal_color, medal_center, 18)
                pygame.draw.circle(surface, THEME["white"], medal_center, 18, 2)

                # 排名数字
                rank_surf = header_font.render(str(rank), True, THEME["white"])
                rank_text_x = medal_center[0] - rank_surf.get_width() // 2
                rank_text_y = medal_center[1] - rank_surf.get_height() // 2
                surface.blit(rank_surf, (rank_text_x, rank_text_y))
            else:
                # 其他排名
                rank_surf = default_font.render(f"#{rank}", True, THEME["text"])
                surface.blit(rank_surf, (rank_x, y + 15))

            # 玩家名称
            name = entry['name'] if entry['name'] else f"玩家{entry['address'][-4:]}"
            name_surf = default_font.render(name, True, THEME["text"])
            # 垂直居中
            name_y = y + (line_height - name_surf.get_height()) // 2
            surface.blit(name_surf, (col_x[1], name_y))

            # 当前玩家标记
            if is_current:
                you_badge = pygame.Rect(col_x[1] + name_surf.get_width() + 10, name_y, 45, 22)
                pygame.draw.rect(surface, THEME["secondary"], you_badge, border_radius=4)
                you_text = small_font.render("YOU", True, THEME["white"])
                # 文字在徽章内居中
                you_text_x = you_badge.centerx - you_text.get_width() // 2
                you_text_y = you_badge.centery - you_text.get_height() // 2
                surface.blit(you_text, (you_text_x, you_text_y))

            # 地址
            addr = f"{entry['address'][:10]}...{entry['address'][-6:]}"
            addr_surf = small_font.render(addr, True, THEME["mid_gray"])
            # 垂直居中
            addr_y = y + (line_height - addr_surf.get_height()) // 2
            surface.blit(addr_surf, (col_x[2], addr_y))

            # 分数 - 突出显示
            score_text = str(entry['score'])
            score_surf = header_font.render(score_text, True, THEME["primary"])
            # 垂直居中
            score_y = y + (line_height - score_surf.get_height()) // 2
            surface.blit(score_surf, (col_x[3], score_y))

        # 底部信息栏
        bottom_rect = pygame.Rect(0, HEIGHT - 90, WIDTH, 90)
        pygame.draw.rect(surface, THEME["white"], bottom_rect)
        pygame.draw.line(surface, THEME["light_gray"], (0, HEIGHT - 90), (WIDTH, HEIGHT - 90), 2)

        # 你的排名卡片
        if game.player_rank > 0:
            your_rank_card = pygame.Rect(30, HEIGHT - 68, 280, 50)
            pygame.draw.rect(surface, THEME["secondary_light"], your_rank_card, border_radius=10)

            rank_label = small_font.render("你的排名", True, THEME["text"])
            surface.blit(rank_label, (your_rank_card.x + 15, your_rank_card.y + 8))

            rank_value = header_font.render(f"#{game.player_rank} / {game.total_players}", True, THEME["secondary"])
            surface.blit(rank_value, (your_rank_card.x + 15, your_rank_card.y + 25))

        # 操作提示
        hints = [
            ("↑↓", "滚动", THEME["accent"]),
            ("R", "刷新", THEME["primary"]),
            ("ESC", "返回", THEME["mid_gray"])
        ]

        hint_x = 400
        for key, action, color in hints:
            key_rect = pygame.Rect(hint_x, HEIGHT - 60, len(key) * 15 + 10, 30)
            pygame.draw.rect(surface, color, key_rect, border_radius=5)

            key_text = default_font.render(key, True, THEME["white"])
            surface.blit(key_text, (key_rect.x + 8, key_rect.y + 5))

            action_text = default_font.render(action, True, THEME["text"])
            surface.blit(action_text, (key_rect.right + 10, HEIGHT - 55))

            hint_x += key_rect.width + action_text.get_width() + 35

    @staticmethod
    def draw_account_select(surface, game):
        """绘制账户选择界面"""
        # 渐变背景
        bg_rect = pygame.Rect(0, 0, WIDTH, HEIGHT)
        draw_gradient_rect(surface, bg_rect, THEME["background"], THEME["white"], vertical=True)

        # 标题
        title_y = 60
        title = header_font.render("选择账户", True, THEME["primary"])
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, title_y))

        # 说明文字
        subtitle = small_font.render("选择一个账户进行游戏，用于测试市场交易功能", True, THEME["mid_gray"])
        surface.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, title_y + 45))

        # 当前账户信息
        current_account = game.blockchain_manager.account
        current_short = f"{current_account[:6]}...{current_account[-4:]}"
        current_text = default_font.render(f"当前账户: {current_short}", True, THEME["text"])
        current_rect = pygame.Rect(WIDTH // 2 - 200, title_y + 85, 400, 35)
        pygame.draw.rect(surface, THEME["success"], current_rect, border_radius=8)
        surface.blit(current_text, (current_rect.x + 15, current_rect.y + 8))

        # 账户列表
        accounts = game.all_accounts
        if not accounts:
            no_accounts = header_font.render("没有可用账户", True, THEME["danger"])
            surface.blit(no_accounts, (WIDTH // 2 - no_accounts.get_width() // 2, HEIGHT // 2))
            return

        start_y = 200
        item_height = 80
        item_spacing = 15
        visible_items = min(6, len(accounts))

        # 计算滚动偏移
        if len(accounts) > visible_items:
            scroll_offset = max(0, min(game.account_selection - visible_items // 2, len(accounts) - visible_items))
        else:
            scroll_offset = 0

        # 绘制账户列表
        for i in range(scroll_offset, min(scroll_offset + visible_items, len(accounts))):
            account = accounts[i]
            idx = i
            y = start_y + (i - scroll_offset) * (item_height + item_spacing)

            # 账户卡片
            card_rect = pygame.Rect(WIDTH // 2 - 350, y, 700, item_height)
            is_selected = idx == game.account_selection
            is_current = account == current_account

            if is_selected:
                # 选中状态
                draw_gradient_rect(surface, card_rect, THEME["primary"], THEME["primary_light"])
                text_color = THEME["white"]
                info_color = THEME["white"]

                # 发光效果
                glow_rect = card_rect.inflate(6, 6)
                glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (*THEME["primary"], 50), (0, 0, glow_rect.width, glow_rect.height),
                               border_radius=12)
                surface.blit(glow_surf, glow_rect.topleft)
            elif is_current:
                # 当前账户
                draw_card_with_shadow(surface, card_rect, THEME["success"], THEME["light_gray"], 1, 10)
                text_color = THEME["white"]
                info_color = THEME["white"]
                pygame.draw.rect(surface, THEME["success"], card_rect, 2, border_radius=10)
            else:
                # 普通状态
                draw_card_with_shadow(surface, card_rect, THEME["white"], THEME["card_shadow"], 1, 10)
                text_color = THEME["text"]
                info_color = THEME["mid_gray"]
                pygame.draw.rect(surface, THEME["light_gray"], card_rect, 1, border_radius=10)

            # 账户索引
            index_text = header_font.render(f"#{idx}", True, text_color)
            surface.blit(index_text, (card_rect.x + 20, card_rect.y + 15))

            # 账户地址
            short_addr = f"{account[:10]}...{account[-8:]}"
            addr_text = default_font.render(short_addr, True, text_color)
            surface.blit(addr_text, (card_rect.x + 100, card_rect.y + 15))

            # 获取账户余额和统计
            try:
                if game.blockchain_manager.blockchain_available:
                    w3 = game.blockchain_manager.w3
                    balance_wei = w3.eth.get_balance(account)
                    balance_eth = w3.from_wei(balance_wei, 'ether')
                    balance_text = f"余额: {balance_eth:.4f} ETH"

                    # 获取该账户的游戏统计
                    score, coins = game.blockchain_manager.load_player_stats(account)
                    stats_text = f"分数: {score} | 金币: {coins}"
                else:
                    balance_text = "离线模式"
                    stats_text = ""
            except:
                balance_text = "无法获取"
                stats_text = ""

            balance_surf = small_font.render(balance_text, True, info_color)
            surface.blit(balance_surf, (card_rect.x + 100, card_rect.y + 45))

            if stats_text:
                stats_surf = small_font.render(stats_text, True, info_color)
                surface.blit(stats_surf, (card_rect.x + 350, card_rect.y + 45))

            # 当前账户标记
            if is_current:
                badge_rect = pygame.Rect(card_rect.right - 80, card_rect.y + 10, 70, 25)
                pygame.draw.rect(surface, THEME["white"], badge_rect, border_radius=12)
                badge_text = small_font.render("当前", True, THEME["success"])
                surface.blit(badge_text, (badge_rect.x + 15, badge_rect.y + 4))

        # 滚动指示器
        if len(accounts) > visible_items:
            scroll_bar_x = WIDTH // 2 + 370
            scroll_bar_height = visible_items * (item_height + item_spacing) - item_spacing
            scroll_bar_rect = pygame.Rect(scroll_bar_x, start_y, 8, scroll_bar_height)
            pygame.draw.rect(surface, THEME["light_gray"], scroll_bar_rect, border_radius=4)

            # 滚动条滑块
            thumb_height = max(30, scroll_bar_height * visible_items / len(accounts))
            thumb_y = start_y + (scroll_bar_height - thumb_height) * scroll_offset / (len(accounts) - visible_items)
            thumb_rect = pygame.Rect(scroll_bar_x, thumb_y, 8, thumb_height)
            pygame.draw.rect(surface, THEME["primary"], thumb_rect, border_radius=4)

        # 底部操作栏背景
        bottom_rect = pygame.Rect(0, HEIGHT - 80, WIDTH, 80)
        pygame.draw.rect(surface, THEME["white"], bottom_rect)
        pygame.draw.line(surface, THEME["light_gray"], (0, HEIGHT - 80), (WIDTH, HEIGHT - 80), 2)

        # 操作提示
        hints_y = HEIGHT - 55
        hints = [
            ("↑↓", "选择", THEME["primary"]),
            ("Enter", "确认", THEME["secondary"]),
            ("ESC", "返回", THEME["mid_gray"])
        ]

        hint_x = WIDTH // 2 - 200
        for key, action, color in hints:
            key_rect = pygame.Rect(hint_x, hints_y, len(key) * 15 + 10, 30)
            pygame.draw.rect(surface, color, key_rect, border_radius=5)

            key_text = default_font.render(key, True, THEME["white"])
            surface.blit(key_text, (key_rect.x + 8, key_rect.y + 5))

            action_text = default_font.render(action, True, THEME["text"])
            surface.blit(action_text, (key_rect.right + 10, hints_y + 5))

            hint_x += key_rect.width + action_text.get_width() + 35

