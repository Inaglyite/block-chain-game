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


