# -*- coding: utf-8 -*-
"""
用户认证和好友系统UI渲染器
"""
import pygame
from .config import WIDTH, HEIGHT, WHITE, BLACK, GRAY, BLUE, GREEN, RED, GOLD, PURPLE

# 主题颜色 - 与游戏UI统一
THEME = {
    "primary": (52, 152, 219),      # 主色调蓝
    "primary_light": (102, 187, 235),
    "secondary": (46, 204, 113),     # 次要绿
    "accent": (155, 89, 182),        # 强调紫
    "success": (46, 204, 113),       # 成功绿
    "danger": (231, 76, 60),         # 危险红
    "warning": (241, 196, 15),       # 警告黄
    "background": (236, 240, 241),   # 背景灰
    "white": (255, 255, 255),
    "text": (44, 62, 80),            # 文字深灰
    "text_light": (127, 140, 141),   # 文字浅灰
    "light_gray": (189, 195, 199),
    "mid_gray": (149, 165, 166),
    "dark_gray": (52, 73, 94),
    "input_bg": (250, 250, 250),     # 输入框背景
    "input_border": (189, 195, 199), # 输入框边框
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
    else:
        for i in range(rect.width):
            ratio = i / rect.width
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            pygame.draw.line(surface, (r, g, b),
                           (rect.x + i, rect.y),
                           (rect.x + i, rect.y + rect.height))


def draw_shadow_rect(surface, rect, color, offset=3):
    """绘制带阴影的矩形"""
    shadow_rect = rect.move(offset, offset)
    shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
    pygame.draw.rect(shadow_surf, (*THEME["dark_gray"], 30), (0, 0, shadow_rect.width, shadow_rect.height),
                    border_radius=12)
    surface.blit(shadow_surf, shadow_rect.topleft)
    pygame.draw.rect(surface, color, rect, border_radius=12)


class AuthUIRenderer:
    """用户认证UI渲染器"""

    @staticmethod
    def draw_login_screen(surface, game):
        """绘制登录界面 - 现代化设计"""
        from .utils import load_chinese_font

        try:
            title_font = load_chinese_font(56)
            header_font = load_chinese_font(32)
            default_font = load_chinese_font(22)
            small_font = load_chinese_font(16)
        except Exception as e:
            print(f"❌ 加载字体失败: {e}")
            title_font = pygame.font.Font(None, 56)
            header_font = pygame.font.Font(None, 32)
            default_font = pygame.font.Font(None, 22)
            small_font = pygame.font.Font(None, 16)

        # 渐变背景
        bg_rect = pygame.Rect(0, 0, WIDTH, HEIGHT)
        draw_gradient_rect(surface, bg_rect, THEME["background"], THEME["white"], vertical=True)

        # 主标题
        title_y = 80
        title = title_font.render("欢迎回来", True, THEME["primary"])
        title_shadow = title_font.render("欢迎回来", True, THEME["light_gray"])
        surface.blit(title_shadow, (WIDTH // 2 - title.get_width() // 2 + 2, title_y + 2))
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, title_y))

        # 副标题
        subtitle = default_font.render("登录您的账户继续游戏", True, THEME["text_light"])
        surface.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, title_y + 70))

        # 输入框容器
        container_width = 500
        container_x = WIDTH // 2 - container_width // 2
        input_y = 220

        active_field = getattr(game, 'login_active_field', 'username')

        # 存储输入框位置供点击检测使用
        game.login_username_box = pygame.Rect(container_x, input_y, container_width, 65)
        game.login_password_box = pygame.Rect(container_x, input_y + 95, container_width, 65)

        # 用户名输入框
        username_box = game.login_username_box
        is_username_active = active_field == 'username'

        # 输入框背景
        if is_username_active:
            draw_shadow_rect(surface, username_box, THEME["white"], offset=4)
            border_color = THEME["primary"]
            border_width = 3
        else:
            pygame.draw.rect(surface, THEME["input_bg"], username_box, border_radius=12)
            border_color = THEME["input_border"]
            border_width = 2

        pygame.draw.rect(surface, border_color, username_box, border_width, border_radius=12)

        # 标签
        label_surf = small_font.render("用户名", True, THEME["text"])
        surface.blit(label_surf, (username_box.x + 20, username_box.y + 12))

        # 输入内容
        username_value = getattr(game, 'login_username', '')
        if username_value:
            input_surf = default_font.render(username_value, True, THEME["text"])
        else:
            input_surf = default_font.render("请输入用户名", True, THEME["text_light"])
        surface.blit(input_surf, (username_box.x + 20, username_box.y + 35))

        # 光标
        if is_username_active and pygame.time.get_ticks() % 1000 < 500:
            cursor_x = username_box.x + 20 + input_surf.get_width() + 2
            pygame.draw.line(surface, THEME["primary"],
                           (cursor_x, username_box.y + 38),
                           (cursor_x, username_box.y + 55), 2)

        # 密码输入框
        password_box = game.login_password_box
        is_password_active = active_field == 'password'

        if is_password_active:
            draw_shadow_rect(surface, password_box, THEME["white"], offset=4)
            border_color = THEME["primary"]
            border_width = 3
        else:
            pygame.draw.rect(surface, THEME["input_bg"], password_box, border_radius=12)
            border_color = THEME["input_border"]
            border_width = 2

        pygame.draw.rect(surface, border_color, password_box, border_width, border_radius=12)

        # 标签
        label_surf = small_font.render("密码", True, THEME["text"])
        surface.blit(label_surf, (password_box.x + 20, password_box.y + 12))

        # 输入内容
        password_value = getattr(game, 'login_password', '')
        if password_value:
            password_display = '●' * len(password_value)
            input_surf = default_font.render(password_display, True, THEME["text"])
        else:
            input_surf = default_font.render("请输入密码", True, THEME["text_light"])
        surface.blit(input_surf, (password_box.x + 20, password_box.y + 35))

        # 光标
        if is_password_active and pygame.time.get_ticks() % 1000 < 500:
            cursor_x = password_box.x + 20 + input_surf.get_width() + 2
            pygame.draw.line(surface, THEME["primary"],
                           (cursor_x, password_box.y + 38),
                           (cursor_x, password_box.y + 55), 2)

        # 按钮
        button_y = input_y + 190
        button_width = 240
        button_height = 55

        login_button = pygame.Rect(WIDTH // 2 - button_width - 10, button_y, button_width, button_height)
        register_button = pygame.Rect(WIDTH // 2 + 10, button_y, button_width, button_height)

        # 存储按钮位置
        game.login_login_button = login_button
        game.login_register_button = register_button

        # 登录按钮 - 渐变效果
        draw_shadow_rect(surface, login_button, THEME["success"], offset=3)
        pygame.draw.rect(surface, THEME["success"], login_button, border_radius=12)

        login_text = header_font.render("登录", True, THEME["white"])
        surface.blit(login_text, (login_button.centerx - login_text.get_width() // 2,
                                 login_button.centery - login_text.get_height() // 2))

        # 注册按钮
        pygame.draw.rect(surface, THEME["white"], register_button, border_radius=12)
        pygame.draw.rect(surface, THEME["primary"], register_button, 2, border_radius=12)

        register_text = header_font.render("注册", True, THEME["primary"])
        surface.blit(register_text, (register_button.centerx - register_text.get_width() // 2,
                                    register_button.centery - register_text.get_height() // 2))

        # 提示信息
        if hasattr(game, 'login_message') and game.login_message:
            msg_color = THEME["success"] if getattr(game, 'login_success', False) else THEME["danger"]
            msg_surf = default_font.render(game.login_message, True, msg_color)
            msg_bg = pygame.Rect(WIDTH // 2 - msg_surf.get_width() // 2 - 20, button_y + 80,
                                msg_surf.get_width() + 40, 40)
            pygame.draw.rect(surface, (*msg_color, 30), msg_bg, border_radius=8)
            surface.blit(msg_surf, (WIDTH // 2 - msg_surf.get_width() // 2, button_y + 90))

        # 底部操作提示
        hint_y = HEIGHT - 50
        hints = [
            ("↑↓", "切换", THEME["primary"]),
            ("TAB", "切换", THEME["accent"]),
            ("ENTER", "确认", THEME["success"]),
            ("ESC", "退出", THEME["danger"])
        ]

        total_width = sum([100 for _ in hints])
        start_x = WIDTH // 2 - total_width // 2

        for i, (key, action, color) in enumerate(hints):
            x = start_x + i * 120

            # 键位背景
            key_rect = pygame.Rect(x, hint_y, len(key) * 12 + 16, 30)
            pygame.draw.rect(surface, color, key_rect, border_radius=5)

            key_surf = small_font.render(key, True, THEME["white"])
            surface.blit(key_surf, (key_rect.x + 8, key_rect.y + 7))

            action_surf = small_font.render(action, True, THEME["text"])
            surface.blit(action_surf, (key_rect.right + 8, hint_y + 7))

    @staticmethod
    def draw_register_screen(surface, game):
        """绘制注册界面 - 现代化设计"""
        from .utils import load_chinese_font

        try:
            title_font = load_chinese_font(56)
            header_font = load_chinese_font(28)
            default_font = load_chinese_font(20)
            small_font = load_chinese_font(16)
        except Exception as e:
            title_font = pygame.font.Font(None, 56)
            header_font = pygame.font.Font(None, 28)
            default_font = pygame.font.Font(None, 20)
            small_font = pygame.font.Font(None, 16)

        # 渐变背景
        bg_rect = pygame.Rect(0, 0, WIDTH, HEIGHT)
        draw_gradient_rect(surface, bg_rect, THEME["background"], THEME["white"], vertical=True)

        # 主标题
        title_y = 50
        title = title_font.render("创建账户", True, THEME["primary"])
        title_shadow = title_font.render("创建账户", True, THEME["light_gray"])
        surface.blit(title_shadow, (WIDTH // 2 - title.get_width() // 2 + 2, title_y + 2))
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, title_y))

        # 副标题
        subtitle = default_font.render("填写信息开始您的游戏之旅", True, THEME["text_light"])
        surface.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, title_y + 65))

        # 输入框容器
        container_width = 520
        container_x = WIDTH // 2 - container_width // 2
        input_y = 160

        active_field = getattr(game, 'register_active_field', 'username')
        fields = [
            ('username', '用户名', '请输入用户名（至少3个字符）'),
            ('email', '邮箱', '请输入邮箱地址'),
            ('password', '密码', '请输入密码（至少6个字符）'),
            ('confirm_password', '确认密码', '请再次输入密码')
        ]

        box_height = 60
        box_spacing = 8

        # 存储所有输入框用于点击检测
        for i, (field_name, label, placeholder) in enumerate(fields):
            y = input_y + i * (box_height + box_spacing)
            box = pygame.Rect(container_x, y, container_width, box_height)
            setattr(game, f'register_{field_name}_box', box)

            is_active = active_field == field_name

            # 输入框背景和边框
            if is_active:
                draw_shadow_rect(surface, box, THEME["white"], offset=3)
                border_color = THEME["primary"]
                border_width = 3
            else:
                pygame.draw.rect(surface, THEME["input_bg"], box, border_radius=10)
                border_color = THEME["input_border"]
                border_width = 2

            pygame.draw.rect(surface, border_color, box, border_width, border_radius=10)

            # 标签
            label_surf = small_font.render(label, True, THEME["text"])
            surface.blit(label_surf, (box.x + 18, box.y + 10))

            # 输入内容
            value = getattr(game, f'register_{field_name}', '')
            if value:
                if 'password' in field_name:
                    display_text = '●' * len(value)
                else:
                    display_text = value
                input_surf = default_font.render(display_text, True, THEME["text"])
            else:
                input_surf = small_font.render(placeholder, True, THEME["text_light"])

            surface.blit(input_surf, (box.x + 18, box.y + 32))

            # 光标
            if is_active and pygame.time.get_ticks() % 1000 < 500 and value:
                cursor_x = box.x + 18 + input_surf.get_width() + 2
                pygame.draw.line(surface, THEME["primary"],
                               (cursor_x, box.y + 34),
                               (cursor_x, box.y + 50), 2)

        # 按钮
        button_y = input_y + len(fields) * (box_height + box_spacing) + 20
        button_width = 250
        button_height = 52

        confirm_button = pygame.Rect(WIDTH // 2 - button_width - 8, button_y, button_width, button_height)
        cancel_button = pygame.Rect(WIDTH // 2 + 8, button_y, button_width, button_height)

        # 存储按钮位置
        game.register_confirm_button = confirm_button
        game.register_cancel_button = cancel_button

        # 确认按钮
        draw_shadow_rect(surface, confirm_button, THEME["success"], offset=3)
        pygame.draw.rect(surface, THEME["success"], confirm_button, border_radius=10)

        confirm_text = header_font.render("注册", True, THEME["white"])
        surface.blit(confirm_text, (confirm_button.centerx - confirm_text.get_width() // 2,
                                   confirm_button.centery - confirm_text.get_height() // 2))

        # 取消按钮
        pygame.draw.rect(surface, THEME["white"], cancel_button, border_radius=10)
        pygame.draw.rect(surface, THEME["danger"], cancel_button, 2, border_radius=10)

        cancel_text = header_font.render("返回", True, THEME["danger"])
        surface.blit(cancel_text, (cancel_button.centerx - cancel_text.get_width() // 2,
                                  cancel_button.centery - cancel_text.get_height() // 2))

        # 提示信息
        if hasattr(game, 'register_message') and game.register_message:
            msg_color = THEME["success"] if getattr(game, 'register_success', False) else THEME["danger"]
            msg_surf = default_font.render(game.register_message, True, msg_color)
            msg_bg = pygame.Rect(WIDTH // 2 - msg_surf.get_width() // 2 - 20, button_y + 70,
                                msg_surf.get_width() + 40, 35)
            pygame.draw.rect(surface, (*msg_color, 30), msg_bg, border_radius=8)
            surface.blit(msg_surf, (WIDTH // 2 - msg_surf.get_width() // 2, button_y + 77))

        # 底部操作提示
        hint_y = HEIGHT - 45
        hints = [
            ("↑↓", "切换", THEME["primary"]),
            ("TAB", "下一项", THEME["accent"]),
            ("ENTER", "注册", THEME["success"]),
            ("ESC", "返回", THEME["danger"])
        ]

        total_width = sum([100 for _ in hints])
        start_x = WIDTH // 2 - total_width // 2

        for i, (key, action, color) in enumerate(hints):
            x = start_x + i * 120

            key_rect = pygame.Rect(x, hint_y, len(key) * 12 + 14, 28)
            pygame.draw.rect(surface, color, key_rect, border_radius=5)

            key_surf = small_font.render(key, True, THEME["white"])
            surface.blit(key_surf, (key_rect.x + 7, key_rect.y + 6))

            action_surf = small_font.render(action, True, THEME["text"])
            surface.blit(action_surf, (key_rect.right + 8, hint_y + 6))



class FriendUIRenderer:
    """好友系统UI渲染器"""

    @staticmethod
    def draw_friends_menu(surface, game):
        """绘制好友菜单 - 现代化设计"""
        from .utils import load_chinese_font

        try:
            title_font = load_chinese_font(48)
            header_font = load_chinese_font(28)
            default_font = load_chinese_font(20)
            small_font = load_chinese_font(16)
        except Exception as e:
            title_font = pygame.font.Font(None, 48)
            header_font = pygame.font.Font(None, 28)
            default_font = pygame.font.Font(None, 20)
            small_font = pygame.font.Font(None, 16)

        # 渐变背景
        bg_rect = pygame.Rect(0, 0, WIDTH, HEIGHT)
        draw_gradient_rect(surface, bg_rect, THEME["background"], THEME["white"], vertical=True)

        # 主标题
        title_y = 40
        title = title_font.render("好友系统", True, THEME["primary"])
        title_shadow = title_font.render("好友系统", True, THEME["light_gray"])
        surface.blit(title_shadow, (WIDTH // 2 - title.get_width() // 2 + 2, title_y + 2))
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, title_y))

        # 副标题
        subtitle = default_font.render("管理好友和交易", True, THEME["text_light"])
        surface.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, title_y + 58))

        # 现代化选项卡
        tabs = ["好友列表", "好友请求", "交易请求", "添加好友"]
        tab_width = (WIDTH - 80) // len(tabs)
        tab_height = 50
        tab_y = 130
        current_tab = getattr(game, 'friend_tab', 0)

        for i, tab in enumerate(tabs):
            x = 40 + i * tab_width
            tab_rect = pygame.Rect(x, tab_y, tab_width - 10, tab_height)

            if i == current_tab:
                # 激活状态
                draw_shadow_rect(surface, tab_rect, THEME["primary"], offset=3)
                pygame.draw.rect(surface, THEME["primary"], tab_rect, border_radius=10)
                text_color = THEME["white"]
            else:
                # 未激活状态
                pygame.draw.rect(surface, THEME["white"], tab_rect, border_radius=10)
                pygame.draw.rect(surface, THEME["input_border"], tab_rect, 2, border_radius=10)
                text_color = THEME["text"]

            tab_text = default_font.render(tab, True, text_color)
            surface.blit(tab_text, (tab_rect.centerx - tab_text.get_width() // 2,
                                   tab_rect.centery - tab_text.get_height() // 2))

        # 根据选项卡显示内容
        content_y = 200

        if current_tab == 0:  # 好友列表
            FriendUIRenderer._draw_friends_list(surface, game, content_y, header_font, default_font, small_font)
        elif current_tab == 1:  # 好友请求
            FriendUIRenderer._draw_friend_requests(surface, game, content_y, header_font, default_font, small_font)
        elif current_tab == 2:  # 交易请求
            FriendUIRenderer._draw_trade_requests(surface, game, content_y, header_font, default_font, small_font)
        elif current_tab == 3:  # 添加好友
            FriendUIRenderer._draw_add_friend(surface, game, content_y, header_font, default_font, small_font)

        # 底部操作提示
        hint_y = HEIGHT - 45
        hints = [
            ("←→", "切换标签", THEME["primary"]),
            ("↑↓", "选择", THEME["accent"]),
            ("ENTER", "确认", THEME["success"]),
            ("ESC", "返回", THEME["danger"])
        ]

        total_width = sum([100 for _ in hints])
        start_x = WIDTH // 2 - total_width // 2

        for i, (key, action, color) in enumerate(hints):
            x = start_x + i * 120

            key_rect = pygame.Rect(x, hint_y, len(key) * 12 + 14, 28)
            pygame.draw.rect(surface, color, key_rect, border_radius=5)

            key_surf = small_font.render(key, True, THEME["white"])
            surface.blit(key_surf, (key_rect.x + 7, key_rect.y + 6))

            action_surf = small_font.render(action, True, THEME["text"])
            surface.blit(action_surf, (key_rect.right + 8, hint_y + 6))

    @staticmethod
    def _draw_friends_list(surface, game, start_y, header_font, default_font, small_font):
        """绘制好友列表 - 现代化设计"""
        friends = game.user_manager.get_friends_list()

        if not friends:
            # 空状态提示
            empty_box = pygame.Rect(WIDTH // 2 - 200, start_y + 80, 400, 100)
            pygame.draw.rect(surface, THEME["white"], empty_box, border_radius=12)
            pygame.draw.rect(surface, THEME["input_border"], empty_box, 2, border_radius=12)

            no_friends = default_font.render("还没有好友", True, THEME["text_light"])
            tip = small_font.render("去\"添加好友\"标签页添加吧！", True, THEME["text_light"])
            surface.blit(no_friends, (WIDTH // 2 - no_friends.get_width() // 2, start_y + 110))
            surface.blit(tip, (WIDTH // 2 - tip.get_width() // 2, start_y + 140))
            return

        selection = getattr(game, 'friend_selection', 0)

        for i, friend in enumerate(friends[:6]):  # 显示最多6个
            y = start_y + i * 70

            # 好友卡片
            card_rect = pygame.Rect(60, y, WIDTH - 120, 60)

            # 选中背景
            if i == selection:
                draw_shadow_rect(surface, card_rect, THEME["white"], offset=3)
                pygame.draw.rect(surface, THEME["primary_light"], card_rect, border_radius=10)
                pygame.draw.rect(surface, THEME["primary"], card_rect, 3, border_radius=10)
                name_color = THEME["white"]
            else:
                pygame.draw.rect(surface, THEME["white"], card_rect, border_radius=10)
                pygame.draw.rect(surface, THEME["input_border"], card_rect, 2, border_radius=10)
                name_color = THEME["text"]

            # 好友图标
            icon_rect = pygame.Rect(card_rect.x + 15, card_rect.y + 15, 30, 30)
            pygame.draw.circle(surface, THEME["primary"] if i == selection else THEME["accent"],
                             (icon_rect.centerx, icon_rect.centery), 15)
            icon_text = small_font.render(friend[0].upper(), True, THEME["white"])
            surface.blit(icon_text, (icon_rect.centerx - icon_text.get_width() // 2,
                                    icon_rect.centery - icon_text.get_height() // 2))

            # 好友名称
            name_surf = default_font.render(friend, True, name_color)
            surface.blit(name_surf, (card_rect.x + 60, card_rect.y + 18))

            # 按钮
            btn_y = card_rect.y + 15
            trade_btn = pygame.Rect(WIDTH - 240, btn_y, 80, 30)
            remove_btn = pygame.Rect(WIDTH - 145, btn_y, 70, 30)

            # 交易按钮
            pygame.draw.rect(surface, THEME["success"], trade_btn, border_radius=6)
            trade_text = small_font.render("交易", True, THEME["white"])
            surface.blit(trade_text, (trade_btn.centerx - trade_text.get_width() // 2,
                                     trade_btn.centery - trade_text.get_height() // 2))

            # 删除按钮
            pygame.draw.rect(surface, THEME["white"], remove_btn, border_radius=6)
            pygame.draw.rect(surface, THEME["danger"], remove_btn, 2, border_radius=6)
            remove_text = small_font.render("删除", True, THEME["danger"])
            surface.blit(remove_text, (remove_btn.centerx - remove_text.get_width() // 2,
                                       remove_btn.centery - remove_text.get_height() // 2))

    @staticmethod
    def _draw_friend_requests(surface, game, start_y, header_font, default_font, small_font):
        """绘制好友请求 - 现代化设计"""
        requests = game.user_manager.get_friend_requests()

        if not requests:
            empty_box = pygame.Rect(WIDTH // 2 - 200, start_y + 80, 400, 100)
            pygame.draw.rect(surface, THEME["white"], empty_box, border_radius=12)
            pygame.draw.rect(surface, THEME["input_border"], empty_box, 2, border_radius=12)

            no_req = default_font.render("暂无好友请求", True, THEME["text_light"])
            surface.blit(no_req, (WIDTH // 2 - no_req.get_width() // 2, start_y + 120))
            return

        selection = getattr(game, 'friend_request_selection', 0)

        for i, requester in enumerate(requests[:6]):
            y = start_y + i * 75

            card_rect = pygame.Rect(60, y, WIDTH - 120, 65)

            if i == selection:
                draw_shadow_rect(surface, card_rect, THEME["white"], offset=3)
                pygame.draw.rect(surface, (220, 240, 255), card_rect, border_radius=10)
                pygame.draw.rect(surface, THEME["primary"], card_rect, 3, border_radius=10)
            else:
                pygame.draw.rect(surface, THEME["white"], card_rect, border_radius=10)
                pygame.draw.rect(surface, THEME["input_border"], card_rect, 2, border_radius=10)

            # 图标
            icon_rect = pygame.Rect(card_rect.x + 15, card_rect.y + 15, 35, 35)
            pygame.draw.circle(surface, THEME["warning"], (icon_rect.centerx, icon_rect.centery), 18)
            icon_text = default_font.render(requester[0].upper(), True, THEME["white"])
            surface.blit(icon_text, (icon_rect.centerx - icon_text.get_width() // 2,
                                    icon_rect.centery - icon_text.get_height() // 2))

            # 请求信息
            req_text = default_font.render(f"{requester}", True, THEME["text"])
            desc_text = small_font.render("请求添加你为好友", True, THEME["text_light"])
            surface.blit(req_text, (card_rect.x + 65, card_rect.y + 12))
            surface.blit(desc_text, (card_rect.x + 65, card_rect.y + 38))

            # 按钮
            btn_y = card_rect.y + 17
            accept_btn = pygame.Rect(WIDTH - 260, btn_y, 90, 32)
            reject_btn = pygame.Rect(WIDTH - 155, btn_y, 90, 32)

            pygame.draw.rect(surface, THEME["success"], accept_btn, border_radius=6)
            accept_text = small_font.render("接受", True, THEME["white"])
            surface.blit(accept_text, (accept_btn.centerx - accept_text.get_width() // 2,
                                       accept_btn.centery - accept_text.get_height() // 2))

            pygame.draw.rect(surface, THEME["white"], reject_btn, border_radius=6)
            pygame.draw.rect(surface, THEME["danger"], reject_btn, 2, border_radius=6)
            reject_text = small_font.render("拒绝", True, THEME["danger"])
            surface.blit(reject_text, (reject_btn.centerx - reject_text.get_width() // 2,
                                       reject_btn.centery - reject_text.get_height() // 2))

    @staticmethod
    def _draw_trade_requests(surface, game, start_y, header_font, default_font, small_font):
        """绘制交易请求 - 显示收到的交易请求（现代化设计）"""
        trades = game.user_manager.get_trade_requests()
        pending_trades = [t for t in trades if t['status'] == 'pending']

        if not pending_trades:
            empty_box = pygame.Rect(WIDTH // 2 - 200, start_y + 20, 400, 100)
            pygame.draw.rect(surface, THEME["white"], empty_box, border_radius=12)
            pygame.draw.rect(surface, THEME["input_border"], empty_box, 2, border_radius=12)

            no_trade = default_font.render("暂无收到的交易请求", True, THEME["text_light"])
            surface.blit(no_trade, (WIDTH // 2 - no_trade.get_width() // 2, start_y + 60))

            # 显示已发送的交易
            FriendUIRenderer._draw_sent_trade_offers(surface, game, start_y + 140, header_font, default_font, small_font)
            return

        selection = getattr(game, 'trade_request_selection', 0)

        # 标题
        subtitle = small_font.render("收到的交易请求", True, THEME["text_light"])
        surface.blit(subtitle, (60, start_y - 25))

        for i, trade in enumerate(pending_trades[:3]):  # 最多显示3个
            y = start_y + i * 95

            card_rect = pygame.Rect(60, y, WIDTH - 120, 85)

            if i == selection:
                draw_shadow_rect(surface, card_rect, THEME["white"], offset=3)
                pygame.draw.rect(surface, (220, 255, 220), card_rect, border_radius=10)
                pygame.draw.rect(surface, THEME["success"], card_rect, 3, border_radius=10)
            else:
                pygame.draw.rect(surface, THEME["white"], card_rect, border_radius=10)
                pygame.draw.rect(surface, THEME["input_border"], card_rect, 2, border_radius=10)

            # 图标
            icon_rect = pygame.Rect(card_rect.x + 15, card_rect.y + 20, 45, 45)
            pygame.draw.circle(surface, THEME["accent"], (icon_rect.centerx, icon_rect.centery), 23)
            icon_text = header_font.render("💎", True, THEME["white"])
            surface.blit(icon_text, (icon_rect.centerx - 10, icon_rect.centery - 12))

            # 交易信息
            from_text = default_font.render(f"来自: {trade['from_user']}", True, THEME["text"])
            weapon_text = small_font.render(f"武器 ID: {trade['weapon_id']}", True, THEME["text_light"])
            price_text = default_font.render(f"{trade['price_eth']:.4f} ETH", True, GOLD)

            surface.blit(from_text, (card_rect.x + 75, card_rect.y + 15))
            surface.blit(weapon_text, (card_rect.x + 75, card_rect.y + 40))
            surface.blit(price_text, (card_rect.x + 75, card_rect.y + 60))

            # 提示：点击ENTER查看详情
            if i == selection:
                view_hint = small_font.render("按ENTER查看详情", True, THEME["success"])
                surface.blit(view_hint, (card_rect.right - view_hint.get_width() - 15, card_rect.y + 30))

        # 显示已发送的交易
        sent_start_y = start_y + min(len(pending_trades), 3) * 95 + 30
        FriendUIRenderer._draw_sent_trade_offers(surface, game, sent_start_y, header_font, default_font, small_font)

    @staticmethod
    def _draw_sent_trade_offers(surface, game, start_y, header_font, default_font, small_font):
        """绘制已发送的交易报价"""
        # 标题
        subtitle = small_font.render("已发送的交易报价", True, THEME["text_light"])
        surface.blit(subtitle, (60, start_y - 25))

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
            empty_text = small_font.render("暂无发送的交易报价", True, THEME["text_light"])
            surface.blit(empty_text, (WIDTH // 2 - empty_text.get_width() // 2, start_y + 30))
            return

        # 显示列表（最多显示2个）
        for i, offer in enumerate(sent_offers[:2]):
            y = start_y + i * 75

            offer_rect = pygame.Rect(60, y, WIDTH - 120, 65)

            # 根据状态设置颜色
            status_colors = {
                'pending': THEME["warning"],
                'accepted': THEME["success"],
                'rejected': THEME["danger"],
                'completed': THEME["primary"]
            }
            border_color = status_colors.get(offer['status'], THEME["input_border"])

            pygame.draw.rect(surface, THEME["white"], offer_rect, border_radius=8)
            pygame.draw.rect(surface, border_color, offer_rect, 2, border_radius=8)

            # 图标
            icon_size = 35
            icon_rect = pygame.Rect(offer_rect.x + 12, offer_rect.y + 15, icon_size, icon_size)
            pygame.draw.circle(surface, border_color, (icon_rect.centerx, icon_rect.centery), icon_size // 2)
            icon_text = default_font.render("📤", True, THEME["white"])
            surface.blit(icon_text, (icon_rect.centerx - 8, icon_rect.centery - 8))

            # 接收方和武器信息
            to_text = default_font.render(f"发送给: {offer['to_user_display']}", True, THEME["text"])
            surface.blit(to_text, (offer_rect.x + 60, offer_rect.y + 10))

            weapon_price = small_font.render(f"武器 ID: {offer['weapon_id']} | {offer['price_eth']:.4f} ETH",
                                            True, THEME["text_light"])
            surface.blit(weapon_price, (offer_rect.x + 60, offer_rect.y + 35))

            # 状态
            status_map = {
                'pending': '⏳ 等待中',
                'accepted': '✅ 已接受',
                'rejected': '❌ 已拒绝',
                'completed': '✓ 已完成'
            }
            status_text = small_font.render(status_map.get(offer['status'], '未知'),
                                           True, border_color)
            surface.blit(status_text, (offer_rect.right - status_text.get_width() - 15, offer_rect.centery - 8))

    @staticmethod
    def _draw_add_friend(surface, game, start_y, header_font, default_font, small_font):
        """绘制添加好友界面 - 现代化设计"""
        # 搜索框
        search_width = 600
        search_box = pygame.Rect(WIDTH // 2 - search_width // 2, start_y, search_width, 50)

        # 搜索框样式
        pygame.draw.rect(surface, THEME["white"], search_box, border_radius=12)
        pygame.draw.rect(surface, THEME["primary"], search_box, 3, border_radius=12)

        # 搜索图标
        icon_text = default_font.render("🔍", True, THEME["primary"])
        surface.blit(icon_text, (search_box.x + 15, search_box.y + 12))

        search_label = small_font.render("搜索用户名或邮箱", True, THEME["text_light"])
        surface.blit(search_label, (search_box.x + 50, search_box.y - 25))

        search_text = getattr(game, 'friend_search_text', '')
        if search_text:
            search_surf = default_font.render(search_text, True, THEME["text"])
        else:
            search_surf = default_font.render("输入用户名或邮箱...", True, THEME["text_light"])
        surface.blit(search_surf, (search_box.x + 50, search_box.y + 13))

        # 光标
        if pygame.time.get_ticks() % 1000 < 500 and search_text:
            cursor_x = search_box.x + 50 + search_surf.get_width() + 2
            pygame.draw.line(surface, THEME["primary"],
                           (cursor_x, search_box.y + 15),
                           (cursor_x, search_box.y + 35), 2)

        # 操作反馈消息
        if hasattr(game, 'friend_add_message') and game.friend_add_message:
            msg_color = THEME["success"] if getattr(game, 'friend_add_success', False) else THEME["danger"]
            msg_surf = small_font.render(game.friend_add_message, True, msg_color)
            msg_bg = pygame.Rect(WIDTH // 2 - msg_surf.get_width() // 2 - 15, start_y + 60,
                                msg_surf.get_width() + 30, 30)
            pygame.draw.rect(surface, (*msg_color, 40), msg_bg, border_radius=8)
            surface.blit(msg_surf, (WIDTH // 2 - msg_surf.get_width() // 2, start_y + 65))

        # 搜索结果
        search_results = getattr(game, 'friend_search_results', [])
        selection = getattr(game, 'friend_add_selection', 0)

        if search_text and not search_results:
            # 无结果提示
            no_result_box = pygame.Rect(WIDTH // 2 - 150, start_y + 120, 300, 80)
            pygame.draw.rect(surface, THEME["white"], no_result_box, border_radius=12)
            pygame.draw.rect(surface, THEME["input_border"], no_result_box, 2, border_radius=12)

            no_result = default_font.render("未找到用户", True, THEME["text_light"])
            surface.blit(no_result, (WIDTH // 2 - no_result.get_width() // 2, start_y + 145))

        for i, user in enumerate(search_results[:5]):
            y = start_y + 110 + i * 75

            card_rect = pygame.Rect(60, y, WIDTH - 120, 65)

            # 选中状态高亮
            if i == selection:
                draw_shadow_rect(surface, card_rect, THEME["white"], offset=3)
                pygame.draw.rect(surface, (220, 255, 220), card_rect, border_radius=10)
                pygame.draw.rect(surface, THEME["success"], card_rect, 3, border_radius=10)
            else:
                pygame.draw.rect(surface, THEME["white"], card_rect, border_radius=10)
                pygame.draw.rect(surface, THEME["input_border"], card_rect, 2, border_radius=10)

            # 用户图标
            icon_rect = pygame.Rect(card_rect.x + 15, card_rect.y + 15, 35, 35)
            icon_color = THEME["success"] if i == selection else THEME["primary"]
            pygame.draw.circle(surface, icon_color, (icon_rect.centerx, icon_rect.centery), 18)
            icon_text = default_font.render(user['username'][0].upper(), True, THEME["white"])
            surface.blit(icon_text, (icon_rect.centerx - icon_text.get_width() // 2,
                                    icon_rect.centery - icon_text.get_height() // 2))

            # 用户信息
            user_text = default_font.render(user['username'], True, THEME["text"])
            level_text = small_font.render(f"等级 {user['level']}", True, THEME["text_light"])

            surface.blit(user_text, (card_rect.x + 65, card_rect.y + 12))
            surface.blit(level_text, (card_rect.x + 65, card_rect.y + 38))

            # 添加按钮
            add_btn = pygame.Rect(WIDTH - 220, y + 17, 110, 32)

            # 如果选中，按钮使用更鲜艳的颜色
            btn_color = THEME["success"] if i == selection else (100, 200, 100)
            pygame.draw.rect(surface, btn_color, add_btn, border_radius=6)

            add_text = small_font.render("添加好友", True, THEME["white"])
            surface.blit(add_text, (add_btn.centerx - add_text.get_width() // 2,
                                   add_btn.centery - add_text.get_height() // 2))

