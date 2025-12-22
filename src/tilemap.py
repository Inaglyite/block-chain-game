# -*- coding: utf-8 -*-
"""
地图相关类
"""
import os
import pygame
import pytmx
from pytmx.util_pygame import load_pygame
import random


class TileMap:
    """TMX地图加载器"""
    
    def __init__(self, tmx_path: str):
        if not os.path.exists(tmx_path):
            raise FileNotFoundError(f"未找到 TMX 地图: {tmx_path}")
        self.tmx_data = load_pygame(tmx_path)
        self.pixel_width = self.tmx_data.width * self.tmx_data.tilewidth
        self.pixel_height = self.tmx_data.height * self.tmx_data.tileheight
        self.surface = pygame.Surface((self.pixel_width, self.pixel_height), pygame.SRCALPHA).convert_alpha()
        self._render_layers()

    def _render_layers(self):
        """渲染所有图层到表面"""
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
        """绘制地图到目标表面"""
        target_surface.blit(self.surface, (0, 0), camera_rect)

    def sample_color(self, x: float, y: float):
        """获取指定位置的颜色"""
        if 0 <= x < self.pixel_width and 0 <= y < self.pixel_height:
            return self.surface.get_at((int(x), int(y)))
        return None

    def looks_like_grass(self, x: float, y: float) -> bool:
        """检查指定位置是否看起来像草地"""
        color = self.sample_color(x, y)
        if color is None or color.a == 0:
            return False
        return color.g > color.r + 10 and color.g > color.b + 10


class ProceduralTileMap:
    """程序化生成的地图"""
    
    def __init__(self, width: int, height: int, tile_size: int = 32):
        self.pixel_width = width
        self.pixel_height = height
        self.tilewidth = tile_size
        self.tileheight = tile_size
        self.surface = pygame.Surface((self.pixel_width, self.pixel_height), pygame.SRCALPHA).convert_alpha()
        self._generate_pattern()

    def _generate_pattern(self):
        """生成随机地形图案"""
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
        """绘制地图到目标表面"""
        target_surface.blit(self.surface, (0, 0), camera_rect)

    def sample_color(self, x: float, y: float):
        """获取指定位置的颜色"""
        if 0 <= x < self.pixel_width and 0 <= y < self.pixel_height:
            return self.surface.get_at((int(x), int(y)))
        return None

    def looks_like_grass(self, x: float, y: float) -> bool:
        """检查指定位置是否看起来像草地"""
        color = self.sample_color(x, y)
        if color is None or color.a == 0:
            return False
        return color.g > color.r + 10 and color.g > color.b + 10

