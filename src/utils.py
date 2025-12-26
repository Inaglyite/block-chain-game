# -*- coding: utf-8 -*-
"""
工具函数
"""
import pygame
from .config import FONT_CANDIDATES

# 字体缓存，避免重复加载和打印
_font_cache = {}


def load_chinese_font(size: int):
    """
    加载中文字体
    
    Args:
        size: 字体大小
        
    Returns:
        pygame.font.Font: 字体对象
    """
    # 检查缓存
    if size in _font_cache:
        return _font_cache[size]

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
            font = pygame.font.Font(p, size)
            _font_cache[size] = font
            return font
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
                test_surface = fnt.render("测试中文", True, (0, 0, 0))
                if test_surface.get_width() > 0:
                    print(f"✅ 使用中文字体: {name} (size={size})")
                    _font_cache[size] = fnt
                    return fnt
            except Exception:
                continue
    print(f"⚠️ 未找到合适中文字体，回退默认字体 size={size}. 建议安装：fonts-wqy-microhei 或 fonts-noto-cjk")
    font = pygame.font.Font(None, size)
    _font_cache[size] = font
    return font

def load_emoji_font(size):
    """加载支持Emoji的字体"""
    # 尝试多个可能的emoji字体
    emoji_fonts = [
        'NotoColorEmoji',
        'Noto Color Emoji',
        'Segoe UI Emoji',
        'Apple Color Emoji',
        'Android Emoji',
        'EmojiOne Color',
    ]

    for font_name in emoji_fonts:
        try:
            font = pygame.font.SysFont(font_name, size)
            # 测试是否能渲染emoji
            test_surf = font.render("😀", True, (0, 0, 0))
            if test_surf and test_surf.get_width() > 0:
                print(f"✅ 使用Emoji字体: {font_name} (size={size})")
                return font
        except:
            continue

    print(f"⚠️ 未找到Emoji字体，将使用文本代替Emoji (size={size})")
    return None

def render_text_with_emoji(font, emoji_font, text, color, antialias=True):
    """
    渲染包含Emoji的文本。
    如果没有emoji字体，将emoji替换为文本表示。
    """
    # 如果没有emoji字体，替换emoji为文本
    if emoji_font is None:
        # 替换常见emoji为文本
        emoji_replacements = {
            '👤': '[玩家]',
            '🏆': '[分数]',
            '💰': '[金币]',
            '⚔️': '[武器]',
            '🌿': '[草]',
            '🎒': '[背包]',
            '🏪': '[市场]',
            '💎': '[ETH]',
            '🔄': '[刷新]',
            '✅': '[已连接]',
            '⚠️': '[警告]',
            '🎮': '[游戏]',
            '🥇': '[1]',
            '🥈': '[2]',
            '🥉': '[3]',
        }
        for emoji, replacement in emoji_replacements.items():
            text = text.replace(emoji, replacement)
        return font.render(text, antialias, color)

    # 检查文本中是否包含可能的Emoji字符
    has_emoji = any(ord(char) > 0x231A for char in text)

    if not has_emoji:
        return font.render(text, antialias, color)

    # 逐个字符渲染
    surfaces = []
    total_width = 0
    max_height = 0

    for char in text:
        try:
            # 检查字符的宽度
            char_width = font.size(char)[0]

            # 如果是高unicode字符（可能是emoji），尝试用emoji字体
            if ord(char) > 0x231A:
                try:
                    char_surf = emoji_font.render(char, antialias, color)
                    if char_surf.get_width() > 0:
                        surfaces.append(char_surf)
                        total_width += char_surf.get_width()
                        max_height = max(max_height, char_surf.get_height())
                        continue
                except:
                    pass

            # 使用主字体渲染
            if char_width > 0:
                char_surf = font.render(char, antialias, color)
                surfaces.append(char_surf)
                total_width += char_surf.get_width()
                max_height = max(max_height, char_surf.get_height())
            else:
                # 如果字符无法渲染，跳过
                continue

        except Exception as e:
            # 如果渲染失败，跳过这个字符
            print(f"⚠️ 无法渲染字符 '{char}': {e}")
            continue

    # 如果没有成功渲染任何字符，返回空surface
    if not surfaces or total_width == 0:
        return pygame.Surface((1, 1), pygame.SRCALPHA)

    # 将所有字符表面拼接成一个
    final_surface = pygame.Surface((total_width, max_height), pygame.SRCALPHA)
    current_x = 0
    for surf in surfaces:
        # 垂直居中对齐
        y_pos = (max_height - surf.get_height()) // 2
        final_surface.blit(surf, (current_x, y_pos))
        current_x += surf.get_width()

    return final_surface

def get_condition_name(condition_or_wear):
    """获取品相名称"""
    from .enums import Condition

    if condition_or_wear is None:
        return "未知"

    # 如果是Condition枚举
    if isinstance(condition_or_wear, Condition):
        names = {
            Condition.S: "S级（极佳）",
            Condition.A: "A级（优良）",
            Condition.B: "B级（良好）",
            Condition.C: "C级（普通）",
            Condition.D: "D级（磨损）",
            Condition.E: "E级（严重磨损）",
        }
        return names.get(condition_or_wear, "未知")

    # 如果是wear浮点数，计算品相
    if isinstance(condition_or_wear, (float, int)):
        wear = float(condition_or_wear)
        if wear < 0.05:
            grade = Condition.S
        elif wear < 0.15:
            grade = Condition.A
        elif wear < 0.30:
            grade = Condition.B
        elif wear < 0.50:
            grade = Condition.C
        elif wear < 0.75:
            grade = Condition.D
        else:
            grade = Condition.E

        names = {
            Condition.S: "S级（极佳）",
            Condition.A: "A级（优良）",
            Condition.B: "B级（良好）",
            Condition.C: "C级（普通）",
            Condition.D: "D级（磨损）",
            Condition.E: "E级（严重磨损）",
        }
        return f"{names[grade]} ({wear:.4f})"

    return "未知"

def format_wear_value(wear):
    """格式化磨损度数值显示"""
    if wear is None:
        return "N/A"
    return f"{float(wear):.4f}"
