#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
区块链除草游戏 - 主入口文件
"""
import argparse
import os
import sys
import pygame
import logging

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import WIDTH, HEIGHT, WHITE
from src.game import BlockchainGame

# 配置日志
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(message)s")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="区块链旋转除草小游戏")
    parser.add_argument(
        "--account-index",
        type=int,
        default=int(os.getenv("PLAYER_ACCOUNT_INDEX", 0)),
        help="Hardhat 账户索引 (默认 0，可用 PLAYER_ACCOUNT_INDEX 环境变量覆盖)"
    )
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    try:
        print("🚀 开始初始化游戏...")
        
        # 创建游戏窗口
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("区块链旋转除草NFT游戏")
        
        # 显示加载画面
        screen.fill(WHITE)
        font = pygame.font.Font(None, 48)
        loading_text = font.render("Loading...", True, (0, 0, 0))
        screen.blit(loading_text, (WIDTH // 2 - loading_text.get_width() // 2, HEIGHT // 2 - 20))
        pygame.display.flip()

        # 创建游戏实例
        game = BlockchainGame(account_index=args.account_index)
        print("✅ 游戏初始化完成，开始主循环...")

        clock = pygame.time.Clock()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                # 处理开箱结果弹窗（最高优先级）
                if game.show_case_open_result:
                    if event.type == pygame.KEYDOWN:
                        game.close_case_result()
                    continue

                # 处理购买确认窗口（次高优先级）
                if game.game_state == "marketplace" and game.purchase_confirm_active:
                    if event.type == pygame.KEYDOWN:
                        game.handle_purchase_confirm_event(event)
                    continue

                # 处理背包详情窗口（次高优先级）
                if game.game_state == "inventory" and game.inventory_detail_active:
                    if event.type == pygame.KEYDOWN:
                        game.handle_inventory_detail_event(event)
                    continue

                # 处理鼠标点击事件（用于箱子商店NPC交互和好友系统）
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if game.game_state == "case_shop":
                        game.handle_case_shop_input(event)
                        continue
                    elif game.game_state == "friends":
                        game.handle_friends_input(event)
                        continue

                elif event.type == pygame.KEYDOWN:
                    # 游戏中的快捷键
                    if game.game_state == "playing":
                        if event.key == pygame.K_i:
                            game.toggle_inventory()
                        elif event.key == pygame.K_m:
                            game.toggle_market()
                        elif event.key == pygame.K_r:
                            game.generate_grass()
                        elif event.key == pygame.K_c:
                            # 打开箱子商店
                            game.load_case_data()
                            game.game_state = "case_shop"
                            game.case_shop_selection = 0
                        elif event.key == pygame.K_ESCAPE:
                            # 从游戏返回开始菜单
                            game.game_state = "start_menu"
                            continue  # 跳过此事件的后续处理，避免菜单立即接收到ESC
                elif event.type == pygame.TEXTINPUT:
                    if game.game_state == "inventory":
                        # 文本输入处理在handle_listing_price_event中
                        pass
                    continue

                # 根据游戏状态分发输入处理
                if game.game_state == "login":
                    result = game.handle_login_input(event)
                    if result == "quit":
                        running = False
                elif game.game_state == "register":
                    game.handle_register_input(event)
                elif game.game_state == "friends":
                    game.handle_friends_input(event)
                elif game.game_state == "start_menu":
                    result = game.handle_start_menu_input(event)
                    if result == "quit":
                        running = False
                elif game.game_state == "profile":
                    game.handle_profile_input(event)
                elif game.game_state == "leaderboard":
                    game.handle_leaderboard_input(event)
                elif game.game_state == "account_select":
                    game.handle_account_select_input(event)
                elif game.game_state == "inventory":
                    game.handle_inventory_input(event)
                elif game.game_state == "marketplace":
                    game.handle_market_input(event)
                elif game.game_state == "case_shop":
                    game.handle_case_shop_input(event)
                elif game.game_state == "case_inventory":
                    game.handle_case_inventory_input(event)

            keys = pygame.key.get_pressed()
            if game.game_state == "playing" and keys[pygame.K_SPACE]:
                game.rotate_weapon()

            game.handle_player_movement()
            game.tick_auto_refresh()
            screen.fill(WHITE)
            game.draw(screen)
            pygame.display.flip()
            clock.tick(60)

    except Exception as e:
        print(f"❌ 游戏运行错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()

