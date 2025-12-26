# -*- coding: utf-8 -*-
"""
好友交易UI模块
"""
import pygame
from .config import WIDTH, HEIGHT, WHITE, BLACK, GRAY, BLUE, GREEN, RED, GOLD, PURPLE

# 主题颜色
THEME = {
    "primary": (52, 152, 219),
    "primary_light": (102, 187, 235),
    "secondary": (46, 204, 113),
    "accent": (155, 89, 182),
    "success": (46, 204, 113),
    "danger": (231, 76, 60),
    "warning": (241, 196, 15),
    "background": (236, 240, 241),
    "white": (255, 255, 255),
    "text": (44, 62, 80),
    "text_light": (127, 140, 141),
    "light_gray": (189, 195, 199),
    "mid_gray": (149, 165, 166),
    "dark_gray": (52, 73, 94),
    "input_bg": (250, 250, 250),
    "input_border": (189, 195, 199),
}


def draw_gradient_rect(surface, rect, color1, color2, vertical=True):
    """绘制渐变矩形"""
    if vertical:
        for i in range(rect.height):
            ratio = i / rect.height
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            pygame.draw.line(surface, (r, g, b),
                           (rect.x, rect.y + i),
                           (rect.x + rect.width, rect.y + i))


def draw_shadow_rect(surface, rect, color, offset=3):
    """绘制带阴影的矩形"""
    shadow_rect = rect.move(offset, offset)
    shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
    pygame.draw.rect(shadow_surf, (*THEME["dark_gray"], 30), (0, 0, shadow_rect.width, shadow_rect.height),
                    border_radius=12)
    surface.blit(shadow_surf, shadow_rect.topleft)
    pygame.draw.rect(surface, color, rect, border_radius=12)


class TradeUIRenderer:
    """交易UI渲染器"""

    @staticmethod
    def draw_weapon_selection(surface, game):
        """绘制武器选择界面（类似背包）"""
        from .utils import load_chinese_font
        from .enums import Rarity

        try:
            title_font = load_chinese_font(40)
            header_font = load_chinese_font(28)
            default_font = load_chinese_font(20)
            small_font = load_chinese_font(16)
        except:
            title_font = pygame.font.Font(None, 40)
            header_font = pygame.font.Font(None, 28)
            default_font = pygame.font.Font(None, 20)
            small_font = pygame.font.Font(None, 16)

        # 半透明背景（覆盖在好友界面上）
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))

        # 主卡片
        card_width = 900
        card_height = 650
        card_rect = pygame.Rect(WIDTH // 2 - card_width // 2, HEIGHT // 2 - card_height // 2,
                                card_width, card_height)

        draw_shadow_rect(surface, card_rect, THEME["white"], offset=5)

        # 标题
        title = title_font.render(f"选择武器与 {game.trade_target_friend} 交易", True, THEME["primary"])
        surface.blit(title, (card_rect.centerx - title.get_width() // 2, card_rect.y + 20))

        # 获取可交易的武器（未上架的武器）
        tradeable_weapons = [w for w in game.weapons if not w.get('for_sale', False)]

        if not tradeable_weapons:
            # 空状态
            empty_text = default_font.render("没有可交易的武器", True, THEME["text_light"])
            surface.blit(empty_text, (card_rect.centerx - empty_text.get_width() // 2, card_rect.centery - 10))

            hint = small_font.render("按ESC返回", True, THEME["text_light"])
            surface.blit(hint, (card_rect.centerx - hint.get_width() // 2, card_rect.centery + 20))
            return

        # 武器列表
        start_y = card_rect.y + 80
        weapon_height = 80
        visible_count = 6
        selection = getattr(game, 'trade_weapon_selection', 0)

        for i in range(min(visible_count, len(tradeable_weapons))):
            if i >= len(tradeable_weapons):
                break

            weapon = tradeable_weapons[i]
            y = start_y + i * (weapon_height + 10)

            weapon_rect = pygame.Rect(card_rect.x + 30, y, card_width - 60, weapon_height)

            # 选中高亮
            if i == selection:
                pygame.draw.rect(surface, (220, 240, 255), weapon_rect, border_radius=10)
                pygame.draw.rect(surface, THEME["primary"], weapon_rect, 3, border_radius=10)
            else:
                pygame.draw.rect(surface, THEME["input_bg"], weapon_rect, border_radius=10)
                pygame.draw.rect(surface, THEME["input_border"], weapon_rect, 2, border_radius=10)

            # 武器贴图
            weapon_sprite = game.weapon_manager.get_weapon_sprite(weapon)
            if weapon_sprite:
                sprite_scaled = pygame.transform.scale(weapon_sprite, (60, 60))
                surface.blit(sprite_scaled, (weapon_rect.x + 15, weapon_rect.y + 10))

            # 武器信息
            name_text = header_font.render(weapon['name'], True, THEME["text"])
            surface.blit(name_text, (weapon_rect.x + 90, weapon_rect.y + 10))

            # 稀有度
            rarity_colors = {
                Rarity.COMMON: THEME["mid_gray"],
                Rarity.RARE: THEME["primary"],
                Rarity.EPIC: THEME["accent"],
                Rarity.LEGENDARY: GOLD
            }
            rarity_color = rarity_colors.get(weapon['rarity'], THEME["mid_gray"])
            rarity_text = small_font.render(weapon['rarity'].name, True, rarity_color)
            surface.blit(rarity_text, (weapon_rect.x + 90, weapon_rect.y + 40))

            # 伤害倍率
            damage_text = small_font.render(f"伤害: {weapon['damage_multiplier']:.1f}x", True, THEME["text_light"])
            surface.blit(damage_text, (weapon_rect.x + 200, weapon_rect.y + 40))

            # 磨损度
            wear = weapon.get('wear', 0.0)
            wear_text = small_font.render(f"磨损: {wear:.2%}", True, THEME["warning"] if wear > 0.5 else THEME["success"])
            surface.blit(wear_text, (weapon_rect.x + 350, weapon_rect.y + 40))

        # 底部提示
        hint_y = card_rect.y + card_height - 40
        hints = [
            ("↑↓", "选择", THEME["primary"]),
            ("ENTER", "查看详情", THEME["success"]),
            ("ESC", "返回", THEME["danger"])
        ]

        total_width = sum([120 for _ in hints])
        start_x = card_rect.centerx - total_width // 2

        for i, (key, action, color) in enumerate(hints):
            x = start_x + i * 130
            key_rect = pygame.Rect(x, hint_y, len(key) * 12 + 14, 28)
            pygame.draw.rect(surface, color, key_rect, border_radius=5)

            key_surf = small_font.render(key, True, THEME["white"])
            surface.blit(key_surf, (key_rect.x + 7, key_rect.y + 6))

            action_surf = small_font.render(action, True, THEME["text"])
            surface.blit(action_surf, (key_rect.right + 8, hint_y + 6))

    @staticmethod
    def draw_weapon_detail_for_trade(surface, game, weapon):
        """绘制武器详情（交易版）"""
        from .utils import load_chinese_font
        from .enums import Rarity

        try:
            title_font = load_chinese_font(36)
            header_font = load_chinese_font(28)
            default_font = load_chinese_font(20)
            small_font = load_chinese_font(16)
        except:
            title_font = pygame.font.Font(None, 36)
            header_font = pygame.font.Font(None, 28)
            default_font = pygame.font.Font(None, 20)
            small_font = pygame.font.Font(None, 16)

        # 半透明背景
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # 详情卡片
        card_width = 600
        card_height = 500
        card_rect = pygame.Rect(WIDTH // 2 - card_width // 2, HEIGHT // 2 - card_height // 2,
                                card_width, card_height)

        draw_shadow_rect(surface, card_rect, THEME["white"], offset=5)
        pygame.draw.rect(surface, THEME["white"], card_rect, border_radius=15)

        # 标题
        title = title_font.render("武器详情", True, THEME["primary"])
        surface.blit(title, (card_rect.centerx - title.get_width() // 2, card_rect.y + 20))

        # 武器贴图
        weapon_sprite = game.weapon_manager.get_weapon_sprite(weapon)
        if weapon_sprite:
            sprite_size = 120
            sprite_scaled = pygame.transform.scale(weapon_sprite, (sprite_size, sprite_size))
            sprite_x = card_rect.centerx - sprite_size // 2
            sprite_y = card_rect.y + 80

            # 贴图背景
            sprite_bg = pygame.Rect(sprite_x - 10, sprite_y - 10, sprite_size + 20, sprite_size + 20)
            pygame.draw.rect(surface, THEME["input_bg"], sprite_bg, border_radius=10)
            pygame.draw.rect(surface, THEME["input_border"], sprite_bg, 2, border_radius=10)

            surface.blit(sprite_scaled, (sprite_x, sprite_y))

        # 武器信息
        info_y = card_rect.y + 220

        # 名称
        name_text = header_font.render(weapon['name'], True, THEME["text"])
        surface.blit(name_text, (card_rect.centerx - name_text.get_width() // 2, info_y))

        # 稀有度
        rarity_colors = {
            Rarity.COMMON: THEME["mid_gray"],
            Rarity.RARE: THEME["primary"],
            Rarity.EPIC: THEME["accent"],
            Rarity.LEGENDARY: GOLD
        }
        rarity_color = rarity_colors.get(weapon['rarity'], THEME["mid_gray"])
        rarity_text = default_font.render(f"稀有度: {weapon['rarity'].name}", True, rarity_color)
        surface.blit(rarity_text, (card_rect.centerx - rarity_text.get_width() // 2, info_y + 40))

        # 伤害
        damage_text = default_font.render(f"伤害倍率: {weapon['damage_multiplier']:.1f}x", True, THEME["text"])
        surface.blit(damage_text, (card_rect.centerx - damage_text.get_width() // 2, info_y + 70))

        # 磨损度
        wear = weapon.get('wear', 0.0)
        wear_text = default_font.render(f"磨损度: {wear:.2%}", True, THEME["warning"] if wear > 0.5 else THEME["success"])
        surface.blit(wear_text, (card_rect.centerx - wear_text.get_width() // 2, info_y + 100))

        # 按钮
        button_y = card_rect.y + card_height - 80
        button_width = 200
        button_height = 50

        offer_btn = pygame.Rect(card_rect.centerx - button_width - 10, button_y, button_width, button_height)
        cancel_btn = pygame.Rect(card_rect.centerx + 10, button_y, button_width, button_height)

        # 存储按钮位置
        game.trade_offer_button = offer_btn
        game.trade_cancel_button = cancel_btn

        # 发起报价按钮
        pygame.draw.rect(surface, THEME["success"], offer_btn, border_radius=10)
        offer_text = header_font.render("发起报价", True, THEME["white"])
        surface.blit(offer_text, (offer_btn.centerx - offer_text.get_width() // 2,
                                  offer_btn.centery - offer_text.get_height() // 2))

        # 取消按钮
        pygame.draw.rect(surface, THEME["white"], cancel_btn, border_radius=10)
        pygame.draw.rect(surface, THEME["danger"], cancel_btn, 2, border_radius=10)
        cancel_text = header_font.render("取消", True, THEME["danger"])
        surface.blit(cancel_text, (cancel_btn.centerx - cancel_text.get_width() // 2,
                                   cancel_btn.centery - cancel_text.get_height() // 2))

        # 提示
        hint = small_font.render("ENTER: 发起报价  |  ESC: 取消", True, THEME["text_light"])
        surface.blit(hint, (card_rect.centerx - hint.get_width() // 2, button_y - 30))

    @staticmethod
    def draw_price_input(surface, game, weapon):
        """绘制价格输入界面"""
        from .utils import load_chinese_font

        try:
            title_font = load_chinese_font(36)
            header_font = load_chinese_font(28)
            default_font = load_chinese_font(20)
            small_font = load_chinese_font(16)
        except:
            title_font = pygame.font.Font(None, 36)
            header_font = pygame.font.Font(None, 28)
            default_font = pygame.font.Font(None, 20)
            small_font = pygame.font.Font(None, 16)

        # 半透明背景
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # 输入卡片
        card_width = 500
        card_height = 350
        card_rect = pygame.Rect(WIDTH // 2 - card_width // 2, HEIGHT // 2 - card_height // 2,
                                card_width, card_height)

        draw_shadow_rect(surface, card_rect, THEME["white"], offset=5)
        pygame.draw.rect(surface, THEME["white"], card_rect, border_radius=15)

        # 标题
        title = title_font.render("设置交易价格", True, THEME["primary"])
        surface.blit(title, (card_rect.centerx - title.get_width() // 2, card_rect.y + 30))

        # 武器名称
        weapon_text = default_font.render(f"武器: {weapon['name']}", True, THEME["text"])
        surface.blit(weapon_text, (card_rect.centerx - weapon_text.get_width() // 2, card_rect.y + 80))

        # 价格输入框
        input_box = pygame.Rect(card_rect.centerx - 200, card_rect.y + 130, 400, 50)
        pygame.draw.rect(surface, THEME["input_bg"], input_box, border_radius=10)
        pygame.draw.rect(surface, THEME["primary"], input_box, 3, border_radius=10)

        label = small_font.render("价格 (ETH):", True, THEME["text"])
        surface.blit(label, (input_box.x, input_box.y - 25))

        price_text = getattr(game, 'trade_price_input', '')
        if price_text:
            price_surf = header_font.render(price_text, True, THEME["text"])
        else:
            price_surf = default_font.render("输入价格...", True, THEME["text_light"])
        surface.blit(price_surf, (input_box.x + 15, input_box.y + 12))

        # 光标
        if pygame.time.get_ticks() % 1000 < 500 and price_text:
            cursor_x = input_box.x + 15 + price_surf.get_width() + 2
            pygame.draw.line(surface, THEME["primary"],
                           (cursor_x, input_box.y + 15),
                           (cursor_x, input_box.y + 35), 2)

        # 按钮
        button_y = card_rect.y + 230
        button_width = 180
        button_height = 50

        confirm_btn = pygame.Rect(card_rect.centerx - button_width - 10, button_y, button_width, button_height)
        cancel_btn = pygame.Rect(card_rect.centerx + 10, button_y, button_width, button_height)

        game.trade_price_confirm_button = confirm_btn
        game.trade_price_cancel_button = cancel_btn

        # 确认按钮
        pygame.draw.rect(surface, THEME["success"], confirm_btn, border_radius=10)
        confirm_text = header_font.render("确认", True, THEME["white"])
        surface.blit(confirm_text, (confirm_btn.centerx - confirm_text.get_width() // 2,
                                    confirm_btn.centery - confirm_text.get_height() // 2))

        # 取消按钮
        pygame.draw.rect(surface, THEME["white"], cancel_btn, border_radius=10)
        pygame.draw.rect(surface, THEME["danger"], cancel_btn, 2, border_radius=10)
        cancel_text = header_font.render("取消", True, THEME["danger"])
        surface.blit(cancel_text, (cancel_btn.centerx - cancel_text.get_width() // 2,
                                   cancel_btn.centery - cancel_text.get_height() // 2))

        # 错误提示
        if hasattr(game, 'trade_price_error') and game.trade_price_error:
            error_surf = small_font.render(game.trade_price_error, True, THEME["danger"])
            surface.blit(error_surf, (card_rect.centerx - error_surf.get_width() // 2, button_y - 30))

        # 提示
        hint = small_font.render("ENTER: 确认  |  ESC: 取消", True, THEME["text_light"])
        surface.blit(hint, (card_rect.centerx - hint.get_width() // 2, card_rect.y + card_height - 30))

    @staticmethod
    def draw_trade_request_detail(surface, game, trade_request):
        """绘制交易请求详情（接收方查看）"""
        from .utils import load_chinese_font
        from .enums import Rarity

        try:
            title_font = load_chinese_font(36)
            header_font = load_chinese_font(28)
            default_font = load_chinese_font(20)
            small_font = load_chinese_font(16)
        except:
            title_font = pygame.font.Font(None, 36)
            header_font = pygame.font.Font(None, 28)
            default_font = pygame.font.Font(None, 20)
            small_font = pygame.font.Font(None, 16)

        # 半透明背景
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # 详情卡片
        card_width = 650
        card_height = 600
        card_rect = pygame.Rect(WIDTH // 2 - card_width // 2, HEIGHT // 2 - card_height // 2,
                                card_width, card_height)

        draw_shadow_rect(surface, card_rect, THEME["white"], offset=5)
        pygame.draw.rect(surface, THEME["white"], card_rect, border_radius=15)

        # 标题
        title = title_font.render("交易请求详情", True, THEME["primary"])
        surface.blit(title, (card_rect.centerx - title.get_width() // 2, card_rect.y + 20))

        # 发起人信息
        from_text = default_font.render(f"来自: {trade_request['from_user']}", True, THEME["text"])
        surface.blit(from_text, (card_rect.centerx - from_text.get_width() // 2, card_rect.y + 70))

        # 获取武器信息
        weapon_id = trade_request['weapon_id']
        weapon = None
        for w in game.weapons:
            if w['id'] == weapon_id:
                weapon = w
                break

        if not weapon:
            # 可能在已上架列表中
            for w in game.listed_weapons:
                if w['id'] == weapon_id:
                    weapon = w
                    break

        if weapon:
            # 武器贴图
            weapon_sprite = game.weapon_manager.get_weapon_sprite(weapon)
            if weapon_sprite:
                sprite_size = 120
                sprite_scaled = pygame.transform.scale(weapon_sprite, (sprite_size, sprite_size))
                sprite_x = card_rect.centerx - sprite_size // 2
                sprite_y = card_rect.y + 120

                # 贴图背景
                sprite_bg = pygame.Rect(sprite_x - 10, sprite_y - 10, sprite_size + 20, sprite_size + 20)
                pygame.draw.rect(surface, THEME["input_bg"], sprite_bg, border_radius=10)
                pygame.draw.rect(surface, THEME["input_border"], sprite_bg, 2, border_radius=10)

                surface.blit(sprite_scaled, (sprite_x, sprite_y))

            # 武器信息
            info_y = card_rect.y + 260

            # 名称
            name_text = header_font.render(weapon['name'], True, THEME["text"])
            surface.blit(name_text, (card_rect.centerx - name_text.get_width() // 2, info_y))

            # 稀有度
            rarity_colors = {
                Rarity.COMMON: THEME["mid_gray"],
                Rarity.RARE: THEME["primary"],
                Rarity.EPIC: THEME["accent"],
                Rarity.LEGENDARY: GOLD
            }
            rarity_color = rarity_colors.get(weapon['rarity'], THEME["mid_gray"])
            rarity_text = default_font.render(f"稀有度: {weapon['rarity'].name}", True, rarity_color)
            surface.blit(rarity_text, (card_rect.centerx - rarity_text.get_width() // 2, info_y + 40))

            # 伤害
            damage_text = default_font.render(f"伤害倍率: {weapon['damage_multiplier']:.1f}x", True, THEME["text"])
            surface.blit(damage_text, (card_rect.centerx - damage_text.get_width() // 2, info_y + 70))

            # 磨损度
            wear = weapon.get('wear', 0.0)
            wear_text = default_font.render(f"磨损度: {wear:.2%}", True, THEME["warning"] if wear > 0.5 else THEME["success"])
            surface.blit(wear_text, (card_rect.centerx - wear_text.get_width() // 2, info_y + 100))
        else:
            # 武器不存在提示
            no_weapon = default_font.render("武器信息不可用", True, THEME["danger"])
            surface.blit(no_weapon, (card_rect.centerx - no_weapon.get_width() // 2, card_rect.centery))

        # 价格显示
        price_eth = trade_request['price_eth']
        price_bg = pygame.Rect(card_rect.centerx - 150, card_rect.y + 390, 300, 50)
        pygame.draw.rect(surface, THEME["warning"], price_bg, border_radius=10)

        price_text = header_font.render(f"{price_eth:.4f} ETH", True, THEME["white"])
        surface.blit(price_text, (card_rect.centerx - price_text.get_width() // 2, price_bg.y + 12))

        # 按钮
        button_y = card_rect.y + card_height - 80
        button_width = 200
        button_height = 50

        accept_btn = pygame.Rect(card_rect.centerx - button_width - 10, button_y, button_width, button_height)
        reject_btn = pygame.Rect(card_rect.centerx + 10, button_y, button_width, button_height)

        # 存储按钮位置
        game.trade_request_accept_button = accept_btn
        game.trade_request_reject_button = reject_btn

        # 接受按钮
        pygame.draw.rect(surface, THEME["success"], accept_btn, border_radius=10)
        accept_text = header_font.render("接受", True, THEME["white"])
        surface.blit(accept_text, (accept_btn.centerx - accept_text.get_width() // 2,
                                  accept_btn.centery - accept_text.get_height() // 2))

        # 拒绝按钮
        pygame.draw.rect(surface, THEME["white"], reject_btn, border_radius=10)
        pygame.draw.rect(surface, THEME["danger"], reject_btn, 2, border_radius=10)
        reject_text = header_font.render("拒绝", True, THEME["danger"])
        surface.blit(reject_text, (reject_btn.centerx - reject_text.get_width() // 2,
                                   reject_btn.centery - reject_text.get_height() // 2))

        # 提示
        hint = small_font.render("ENTER: 接受  |  DELETE/ESC: 拒绝", True, THEME["text_light"])
        surface.blit(hint, (card_rect.centerx - hint.get_width() // 2, button_y - 30))

    @staticmethod
    def draw_sent_trade_offers(surface, game):
        """绘制已发送的交易报价列表（在好友"交易申请"标签页）"""
        from .utils import load_chinese_font

        try:
            header_font = load_chinese_font(24)
            default_font = load_chinese_font(18)
            small_font = load_chinese_font(14)
        except:
            header_font = pygame.font.Font(None, 24)
            default_font = pygame.font.Font(None, 18)
            small_font = pygame.font.Font(None, 14)

        # 获取当前用户发送的所有交易请求
        all_users = game.user_manager.users
        sent_offers = []

        for username, user_data in all_users.items():
            if username == game.user_manager.current_user:
                continue

            trade_requests = user_data.get('trade_requests', [])
            for trade in trade_requests:
                if trade['from_user'] == game.user_manager.current_user:
                    sent_offers.append({
                        **trade,
                        'to_user_display': username
                    })

        if not sent_offers:
            empty_text = default_font.render("暂无发送的交易报价", True, THEME["text_light"])
            text_rect = empty_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            surface.blit(empty_text, text_rect)
            return

        # 显示列表
        start_y = 200
        item_height = 100

        for i, offer in enumerate(sent_offers[:5]):  # 最多显示5个
            y = start_y + i * (item_height + 10)

            offer_rect = pygame.Rect(100, y, WIDTH - 200, item_height)

            # 根据状态设置颜色
            status_colors = {
                'pending': THEME["warning"],
                'accepted': THEME["success"],
                'rejected': THEME["danger"],
                'completed': THEME["primary"]
            }
            border_color = status_colors.get(offer['status'], THEME["input_border"])

            pygame.draw.rect(surface, THEME["white"], offer_rect, border_radius=12)
            pygame.draw.rect(surface, border_color, offer_rect, 3, border_radius=12)

            # 接收方
            to_text = header_font.render(f"发送给: {offer['to_user_display']}", True, THEME["text"])
            surface.blit(to_text, (offer_rect.x + 20, offer_rect.y + 15))

            # 武器ID和价格
            weapon_id = offer['weapon_id']
            price = offer['price_eth']

            detail_text = default_font.render(f"武器 ID: {weapon_id} | 价格: {price:.4f} ETH", True, THEME["text_light"])
            surface.blit(detail_text, (offer_rect.x + 20, offer_rect.y + 45))

            # 状态
            status_map = {
                'pending': '等待中',
                'accepted': '已接受',
                'rejected': '已拒绝',
                'completed': '已完成'
            }
            status_text = small_font.render(f"状态: {status_map.get(offer['status'], '未知')}",
                                           True, border_color)
            surface.blit(status_text, (offer_rect.x + 20, offer_rect.y + 70))


