# -*- coding: utf-8 -*-
"""
游戏配置和常量
"""
import os
import pygame

# 初始化pygame
pygame.init()

# 屏幕设置
WIDTH, HEIGHT = 1200, 800

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

# 文件路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_TMX_PATH = os.path.join(BASE_DIR, "kenney_roguelike-rpg-pack", "Map", "sample_map.tmx")

# 字体候选列表
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

