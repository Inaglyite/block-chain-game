#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
武器系统测试脚本 - 展示所有可能的武器组合
"""

from src.weapon import WeaponManager
from src.enums import Rarity, WeaponType

def main():
    wm = WeaponManager()
    
    print("=" * 80)
    print("🎮 武器系统完整测试")
    print("=" * 80)
    
    # 1. 展示所有可能的武器名称组合
    print("\n📋 所有武器类型与稀有度组合:")
    print("-" * 80)
    
    for rarity in [Rarity.COMMON, Rarity.RARE, Rarity.EPIC, Rarity.LEGENDARY]:
        print(f"\n【{rarity.name}】")
        for weapon_type in [WeaponType.KNIFE, WeaponType.SWORD, WeaponType.AXE, WeaponType.SICKLE]:
            # 生成3个示例名称
            examples = [wm.generate_weapon_name(weapon_type, rarity) for _ in range(3)]
            stats_range = {
                Rarity.COMMON: "1.0x - 1.1x",
                Rarity.RARE: "1.2x - 1.4x",
                Rarity.EPIC: "1.5x - 1.8x",
                Rarity.LEGENDARY: "1.9x - 2.3x"
            }[rarity]
            print(f"  {weapon_type.value:4s}: {' / '.join(examples)} (伤害: {stats_range})")
    
    # 2. 测试概率分布
    print("\n\n📊 稀有度抽取概率测试 (1000次):")
    print("-" * 80)
    results = {}
    for _ in range(1000):
        r = wm.roll_weapon_rarity()
        results[r.name] = results.get(r.name, 0) + 1
    
    target_probs = {
        'COMMON': 55.0,
        'RARE': 30.0,
        'EPIC': 12.0,
        'LEGENDARY': 3.0
    }
    
    for rarity_name in ['COMMON', 'RARE', 'EPIC', 'LEGENDARY']:
        count = results.get(rarity_name, 0)
        percent = count / 10.0
        target = target_probs[rarity_name]
        diff = abs(percent - target)
        status = "✅" if diff < 3 else "⚠️"
        print(f"  {status} {rarity_name:10s}: {count:4d} 次 ({percent:5.1f}%) - 目标: {target:4.1f}%")
    
    # 3. 测试武器类型分布
    print("\n\n🎲 武器类型抽取测试 (400次):")
    print("-" * 80)
    type_results = {}
    for _ in range(400):
        wt = wm.roll_weapon_type()
        type_results[wt.value] = type_results.get(wt.value, 0) + 1
    
    for weapon_type in [WeaponType.KNIFE, WeaponType.SWORD, WeaponType.AXE, WeaponType.SICKLE]:
        count = type_results.get(weapon_type.value, 0)
        percent = count / 4.0
        status = "✅" if 20 <= percent <= 30 else "⚠️"
        print(f"  {status} {weapon_type.value}: {count:3d} 次 ({percent:5.1f}%)")
    
    # 4. 随机生成一批武器展示
    print("\n\n⚔️ 随机生成武器示例 (20个):")
    print("-" * 80)
    
    rarity_colors = {
        Rarity.COMMON: "⚪",
        Rarity.RARE: "🔵",
        Rarity.EPIC: "🟣",
        Rarity.LEGENDARY: "🟠"
    }
    
    for i in range(20):
        rarity = wm.roll_weapon_rarity()
        weapon_type = wm.roll_weapon_type()
        name = wm.generate_weapon_name(weapon_type, rarity)
        damage = wm.get_weapon_stats(rarity)
        color = rarity_colors[rarity]
        print(f"  {i+1:2d}. {color} {name:12s} | 类型: {weapon_type.value:4s} | 稀有度: {rarity.name:10s} | 伤害: x{damage/100:.2f}")
    
    print("\n" + "=" * 80)
    print("✅ 所有测试完成！")
    print("=" * 80)

if __name__ == "__main__":
    main()

