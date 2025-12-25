# -*- coding: utf-8 -*-
"""
枚举类型定义
"""
from enum import Enum


class Rarity(Enum):
    """武器稀有度"""
    COMMON = 0
    RARE = 1
    EPIC = 2
    LEGENDARY = 3


class WeaponType(Enum):
    """武器类型"""
    KNIFE = "刀"
    SWORD = "剑"
    AXE = "斧头"
    SICKLE = "镰刀"


class Condition(Enum):
    """武器品相等级"""
    S = 0  # S级 / 极佳（像全新）
    A = 1  # A级 / 优良
    B = 2  # B级 / 良好
    C = 3  # C级 / 普通
    D = 4  # D级 / 磨损
    E = 5  # E级 / 严重磨损
