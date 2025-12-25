# -*- coding: utf-8 -*-
"""
箱子相关UI绘制
"""
import pygame
import os
from .config import WIDTH, HEIGHT, WHITE, BLACK, GRAY, BLUE, PURPLE, GOLD, GREEN
from .enums import Rarity
from .utils import get_condition_name, format_wear_value
class CaseUIRenderer:
    """箱子UI渲染器"""

    # 盗贼老人的对话列表
    THIEF_DIALOGUES = [
        "勇者，要不要买点箱子！里面可能会有稀世珍宝哦！",
        "箱子的来源？哈哈哈啊！这是老人的忠告——不该问的事情最好不要问出来，要不以后哪里给你弄箱子去？",
        "走一走瞧一瞧看一看啊！",
    ]

    # 字体缓存（类级别，只加载一次）
    _fonts_loaded = False
    _font = None
    _large_font = None
    _small_font = None

    @classmethod
    def _ensure_fonts_loaded(cls):
        """确保字体已加载（只加载一次）"""
        if not cls._fonts_loaded:
            from .utils import load_chinese_font
            cls._font = load_chinese_font(20)
            cls._large_font = load_chinese_font(32)
            cls._small_font = load_chinese_font(16)
            cls._fonts_loaded = True

    @staticmethod
    def draw_case_shop(surface, game):
        """绘制箱子商店 - 带盗贼老人NPC"""
        # 使用缓存的字体
        CaseUIRenderer._ensure_fonts_loaded()
        font = CaseUIRenderer._font
        large_font = CaseUIRenderer._large_font
        small_font = CaseUIRenderer._small_font

        # 背景 - 商店氛围
        surface.fill((245, 240, 230))
        # 绘制地面
        floor_rect = pygame.Rect(0, HEIGHT - 150, WIDTH, 150)
        # 左侧：盗贼老人NPC
        npc_x = 100
        npc_y = HEIGHT - 500  # 上移位置

        # 加载盗贼老人图片
        try:
            thief_image_path = os.path.join("箱子图片", "盗贼老人.png")
            thief_image = pygame.image.load(thief_image_path).convert_alpha()
            # 缩放到合适大小 - 缩小到0.3倍
            thief_scale = 0.3
            thief_width = int(thief_image.get_width() * thief_scale)
            thief_height = int(thief_image.get_height() * thief_scale)
            thief_image = pygame.transform.smoothscale(thief_image, (thief_width, thief_height))
            surface.blit(thief_image, (npc_x, npc_y))
            # NPC名称标签
            npc_name_bg = pygame.Rect(npc_x + thief_width // 2 - 50, npc_y - 30, 100, 25)
            pygame.draw.rect(surface, (50, 50, 50), npc_name_bg, border_radius=5)
            pygame.draw.rect(surface, GOLD, npc_name_bg, 2, border_radius=5)
            npc_name = small_font.render("盗贼老人", True, GOLD)
            name_x = npc_name_bg.centerx - npc_name.get_width() // 2
            surface.blit(npc_name, (name_x, npc_y - 27))
            # 对话文字 - 直接显示在老人头顶
            if not hasattr(game, 'thief_dialogue_index'):
                game.thief_dialogue_index = 0

            dialogue = CaseUIRenderer.THIEF_DIALOGUES[game.thief_dialogue_index]

            # 文字区域（在老人头顶上方）
            text_start_y = npc_y - 80  # 老人头顶上方80像素
            text_x = npc_x - 50  # 稍微左移一点居中
            max_line_width = 500

            # 分行显示对话
            words = []
            line = ""
            for char in dialogue:
                test_line = line + char
                test_surf = small_font.render(test_line, True, BLACK)
                if test_surf.get_width() > max_line_width:
                    words.append(line)
                    line = char
                else:
                    line = test_line
            if line:
                words.append(line)

            # 绘制带背景的对话文字
            line_height = 22
            total_height = len(words) * line_height + 10

            # 半透明背景
            text_bg_rect = pygame.Rect(text_x - 5, text_start_y - 5, max_line_width + 10, total_height)
            text_bg_surf = pygame.Surface((text_bg_rect.width, text_bg_rect.height), pygame.SRCALPHA)
            text_bg_surf.fill((255, 255, 255, 230))  # 白色半透明背景
            surface.blit(text_bg_surf, text_bg_rect.topleft)
            pygame.draw.rect(surface, GOLD, text_bg_rect, 2, border_radius=8)

            # 绘制对话文字
            current_y = text_start_y
            for line_text in words:
                line_surf = small_font.render(line_text, True, (80, 40, 20))  # 棕色文字
                surface.blit(line_surf, (text_x, current_y))
                current_y += line_height

            # 点击提示（在老人下方）
            click_hint = small_font.render("点击切换对话", True, GRAY)
            hint_x = npc_x + thief_width // 2 - click_hint.get_width() // 2
            surface.blit(click_hint, (hint_x, npc_y + thief_height + 5))

        except Exception as e:
            print(f"⚠️ 加载盗贼老人图片失败: {e}")
            # 备用：绘制简单的NPC占位符
            npc_rect = pygame.Rect(npc_x, npc_y, 120, 150)
            pygame.draw.rect(surface, (100, 100, 100), npc_rect, border_radius=10)
            npc_text = large_font.render("盗贼", True, WHITE)
            surface.blit(npc_text, (npc_x + 20, npc_y + 60))
        # 标题
        title = large_font.render("神秘箱子商店", True, (80, 40, 20))
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 20))
        # 显示金币
        coin_bg = pygame.Rect(WIDTH - 180, 15, 160, 40)
        pygame.draw.rect(surface, GOLD, coin_bg, border_radius=8)
        coins_text = font.render(f"💰 {game.coins} 金币", True, BLACK)
        surface.blit(coins_text, (coin_bg.x + 10, coin_bg.y + 10))
        if not game.all_cases:
            no_cases_text = font.render("暂无可用箱子", True, BLACK)
            surface.blit(no_cases_text, (WIDTH // 2 - no_cases_text.get_width() // 2, HEIGHT // 2))
            return
        # 右侧：箱子展示区（2x2网格）
        start_x = 580
        start_y = 100
        case_width = 280
        case_height = 260
        spacing_x = 320
        spacing_y = 280
        for i, case in enumerate(game.all_cases):
            row = i // 2
            col = i % 2
            x = start_x + col * spacing_x
            y = start_y + row * spacing_y
            # 选中高亮
            is_selected = i == game.case_shop_selection
            # 箱子卡片
            card_rect = pygame.Rect(x, y, case_width, case_height)
            # 背景色和边框
            if is_selected:
                bg_color = (255, 250, 220)
                border_color = GOLD
                border_width = 4
                # 发光效果
                glow_rect = card_rect.inflate(8, 8)
                glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (*GOLD, 80), (0, 0, glow_rect.width, glow_rect.height), border_radius=12)
                surface.blit(glow_surf, glow_rect.topleft)
            else:
                bg_color = (250, 245, 235)
                border_color = (150, 130, 100)
                border_width = 2
            pygame.draw.rect(surface, bg_color, card_rect, border_radius=10)
            pygame.draw.rect(surface, border_color, card_rect, border_width, border_radius=10)
            # 箱子图片
            if case['name'] in game.case_sprites:
                sprite = game.case_sprites[case['name']]
                # 放大箱子图片
                scale = 1.2
                scaled_sprite = pygame.transform.smoothscale(
                    sprite, 
                    (int(sprite.get_width() * scale), int(sprite.get_height() * scale))
                )
                sprite_rect = scaled_sprite.get_rect(center=(x + case_width // 2, y + 80))
                surface.blit(scaled_sprite, sprite_rect)
            # 箱子名称
            case_name_map = {
                "Knife Case": "刀箱子",
                "Sword Case": "剑箱子", 
                "Axe Case": "斧头箱子",
                "Sickle Case": "镰刀箱子"
            }
            display_name = case_name_map.get(case['name'], case['name'])
            name_text = font.render(display_name, True, (80, 40, 20))
            name_x = x + case_width // 2 - name_text.get_width() // 2
            surface.blit(name_text, (name_x, y + 165))
            # 价格标签
            price_bg = pygame.Rect(x + 50, y + 195, 180, 35)
            pygame.draw.rect(surface, GOLD, price_bg, border_radius=6)
            price_text = font.render(f"💰 {case['coin_price']} 金币", True, BLACK)
            price_x = price_bg.centerx - price_text.get_width() // 2
            surface.blit(price_text, (price_x, y + 202))
            # 库存显示
            inventory_count = game.case_inventory.get(case['id'], 0)
            inv_text = small_font.render(f"拥有: {inventory_count}", True, BLUE)
            inv_x = x + case_width // 2 - inv_text.get_width() // 2
            surface.blit(inv_text, (inv_x, y + 235))
        # 底部操作提示栏
        bottom_rect = pygame.Rect(0, HEIGHT - 60, WIDTH, 60)
        pygame.draw.rect(surface, (220, 200, 170), bottom_rect)
        pygame.draw.line(surface, (150, 130, 100), (0, HEIGHT - 60), (WIDTH, HEIGHT - 60), 2)
        hints_text = "方向键: 选择箱子  |  回车: 购买  |  B: 查看背包  |  ESC: 返回游戏"
        hints = small_font.render(hints_text, True, (80, 40, 20))
        surface.blit(hints, (WIDTH // 2 - hints.get_width() // 2, HEIGHT - 38))
    @staticmethod
    def draw_case_inventory(surface, game):
        """绘制箱子库存（背包）"""
        # 使用缓存的字体
        CaseUIRenderer._ensure_fonts_loaded()
        font = CaseUIRenderer._font
        large_font = CaseUIRenderer._large_font
        small_font = CaseUIRenderer._small_font

        # 背景
        surface.fill((240, 245, 250))
        # 标题
        title = large_font.render("🎒 我的箱子", True, BLACK)
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 30))
        # 提示
        hint = small_font.render("使用方向键选择，回车开箱，ESC返回", True, GRAY)
        surface.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 30))
        # 获取有库存的箱子
        owned_cases = []
        for case in game.all_cases:
            count = game.case_inventory.get(case['id'], 0)
            if count > 0:
                owned_cases.append((case, count))
        if not owned_cases:
            no_cases_text = font.render("你还没有任何箱子", True, BLACK)
            surface.blit(no_cases_text, (WIDTH // 2 - no_cases_text.get_width() // 2, HEIGHT // 2 - 20))
            hint2 = small_font.render("前往商店购买箱子", True, GRAY)
            surface.blit(hint2, (WIDTH // 2 - hint2.get_width() // 2, HEIGHT // 2 + 20))
            return
        # 绘制箱子列表
        start_y = 100
        case_height = 140
        spacing = 20
        for i, (case, count) in enumerate(owned_cases):
            y = start_y + i * (case_height + spacing)
            # 选中高亮
            is_selected = i == game.case_inventory_selection
            # 箱子卡片
            card_rect = pygame.Rect(150, y, 900, case_height)
            # 背景色
            bg_color = (255, 250, 200) if is_selected else WHITE
            pygame.draw.rect(surface, bg_color, card_rect, border_radius=10)
            pygame.draw.rect(surface, BLACK if is_selected else GRAY, card_rect, 3 if is_selected else 2, border_radius=10)
            # 箱子图片
            if case['name'] in game.case_sprites:
                sprite = game.case_sprites[case['name']]
                sprite_rect = sprite.get_rect(center=(200, y + case_height // 2))
                surface.blit(sprite, sprite_rect)
            # 箱子信息
            name_text = font.render(case['name'], True, BLACK)
            surface.blit(name_text, (280, y + 20))
            count_text = font.render(f"数量: {count}", True, BLUE)
            surface.blit(count_text, (280, y + 60))
            # 开箱按钮
            btn_rect = pygame.Rect(800, y + 45, 180, 50)
            pygame.draw.rect(surface, GREEN, btn_rect, border_radius=5)
            pygame.draw.rect(surface, BLACK, btn_rect, 2, border_radius=5)
            btn_text = font.render("打开箱子", True, BLACK)
            surface.blit(btn_text, (btn_rect.x + btn_rect.width // 2 - btn_text.get_width() // 2, btn_rect.y + 15))
    @staticmethod
    def draw_case_open_result(surface, game):
        """绘制开箱结果弹窗"""
        # 使用缓存的字体
        CaseUIRenderer._ensure_fonts_loaded()
        font = CaseUIRenderer._font
        large_font = CaseUIRenderer._large_font
        small_font = CaseUIRenderer._small_font

        if not game.opened_weapon:
            return
        # 半透明遮罩
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        # 中央面板
        panel_width = 600
        panel_height = 500
        panel_rect = pygame.Rect((WIDTH - panel_width) // 2, (HEIGHT - panel_height) // 2, panel_width, panel_height)
        pygame.draw.rect(surface, WHITE, panel_rect, border_radius=15)
        pygame.draw.rect(surface, GOLD, panel_rect, 4, border_radius=15)
        # 标题
        title = large_font.render("🎉 恭喜开箱！", True, GOLD)
        surface.blit(title, (panel_rect.x + panel_width // 2 - title.get_width() // 2, panel_rect.y + 30))
        weapon = game.opened_weapon
        # 武器图片（如果有）
        sprite = game.weapon_manager.get_weapon_sprite(weapon)
        if sprite:
            # 放大武器显示
            scaled_sprite = pygame.transform.scale(sprite, (int(sprite.get_width() * 2.5), int(sprite.get_height() * 2.5)))
            sprite_rect = scaled_sprite.get_rect(center=(panel_rect.x + panel_width // 2, panel_rect.y + 160))
            surface.blit(scaled_sprite, sprite_rect)
        # 武器名称
        name_text = font.render(weapon['name'], True, BLACK)
        surface.blit(name_text, (panel_rect.x + panel_width // 2 - name_text.get_width() // 2, panel_rect.y + 260))
        # 稀有度
        rarity_names = {
            Rarity.COMMON: "普通",
            Rarity.RARE: "稀有",
            Rarity.EPIC: "史诗",
            Rarity.LEGENDARY: "传说"
        }
        rarity_colors = {
            Rarity.COMMON: GRAY,
            Rarity.RARE: BLUE,
            Rarity.EPIC: PURPLE,
            Rarity.LEGENDARY: GOLD
        }
        rarity_name = rarity_names.get(weapon['rarity'], "未知")
        rarity_color = rarity_colors.get(weapon['rarity'], BLACK)
        rarity_text = font.render(f"稀有度: {rarity_name}", True, rarity_color)
        surface.blit(rarity_text, (panel_rect.x + panel_width // 2 - rarity_text.get_width() // 2, panel_rect.y + 300))
        # 伤害倍率
        damage_text = small_font.render(f"伤害倍率: {weapon['damage_multiplier']:.1f}x", True, BLACK)
        surface.blit(damage_text, (panel_rect.x + panel_width // 2 - damage_text.get_width() // 2, panel_rect.y + 335))
        # 磨损度
        if weapon.get('wear') is not None:
            wear_str = format_wear_value(weapon['wear'])
            condition_str = get_condition_name(weapon['wear'])
            wear_text = small_font.render(f"磨损度: {wear_str}", True, BLACK)
            surface.blit(wear_text, (panel_rect.x + panel_width // 2 - wear_text.get_width() // 2, panel_rect.y + 365))
            condition_text = small_font.render(f"品相: {condition_str}", True, BLUE)
            surface.blit(condition_text, (panel_rect.x + panel_width // 2 - condition_text.get_width() // 2, panel_rect.y + 395))
        # 关闭按钮
        btn_rect = pygame.Rect(panel_rect.x + panel_width // 2 - 80, panel_rect.y + panel_height - 70, 160, 45)
        pygame.draw.rect(surface, GREEN, btn_rect, border_radius=5)
        pygame.draw.rect(surface, BLACK, btn_rect, 2, border_radius=5)
        btn_text = font.render("确定", True, BLACK)
        surface.blit(btn_text, (btn_rect.x + btn_rect.width // 2 - btn_text.get_width() // 2, btn_rect.y + 12))
        # 提示
        hint_text = small_font.render("按任意键关闭", True, GRAY)
        surface.blit(hint_text, (panel_rect.x + panel_width // 2 - hint_text.get_width() // 2, panel_rect.y + panel_height - 20))
