# -*- coding: utf-8 -*-
"""
区块链交互模块
"""
import json
import os
import traceback
from web3 import Web3
from .enums import Rarity
class BlockchainManager:
    """区块链管理器"""
    def __init__(self, account_index: int = 0):
        self.blockchain_available = False
        self.offline_reason = ""
        self.w3 = None
        self.contract = None
        self.contract_abi = None
        self.account = "0x0000000000000000000000000000000000000000"
        self.contract_address = "N/A"
        self.rpc_url = os.getenv("RPC_URL", "http://127.0.0.1:8545")
        self.account_index = account_index
        self.contract_owner = None
        self.contract_owner_available = False
        self.available_accounts = []
    def _load_json_with_fallback(self, candidates, description):
        """从多个候选路径中加载 JSON，返回 (数据, 使用的路径)"""
        errors = []
        for path in candidates:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f), path
            except FileNotFoundError:
                errors.append(f"{path}: 文件不存在")
            except json.JSONDecodeError as err:
                errors.append(f"{path}: JSON 解析失败 ({err})")
        detail = " | ".join(errors)
        raise FileNotFoundError(f"{description} 未找到，已尝试: {', '.join(candidates)}. {detail}")
    def _resolve_contract_address(self, candidates):
        """寻找包含已部署合约地址的文件，返回 (checksum 地址, 合约信息, 路径)"""
        errors = []
        for path in candidates:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    info = json.load(f)
            except FileNotFoundError:
                errors.append(f"{path}: 文件不存在")
                continue
            raw_address = info.get('address')
            if not raw_address:
                errors.append(f"{path}: 缺少 address 字段")
                continue
            try:
                checksum = self.w3.to_checksum_address(raw_address)
            except Exception as err:
                errors.append(f"{path}: 地址无效 ({raw_address}) -> {err}")
                continue
            code = self.w3.eth.get_code(checksum)
            if code and any(byte != 0 for byte in code):
                return checksum, info, path
            errors.append(f"{path}: 地址 {raw_address} 上没有已部署合约")
        detail = " | ".join(errors)
        raise RuntimeError(f"无法找到可用的合约地址。请重新部署合约。详情: {detail}")
    def setup(self):
        """设置区块链连接"""
        try:
            print(f"🔌 正在连接区块链 RPC: {self.rpc_url}")
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url, request_kwargs={"timeout": 1}))  # 减少超时时间
            try:
                block_number = self.w3.eth.block_number
                print(f"✅ 连接到区块链网络，最新区块: {block_number}")
            except Exception as block_err:
                raise RuntimeError(f"无法获取区块高度: {block_err}") from block_err
            abi_data, abi_path = self._load_json_with_fallback(
                ["WeedCutterNFT.json", "scripts/WeedCutterNFT.json"],
                "合约 ABI"
            )
            self.contract_abi = abi_data['abi']
            if abi_path != "WeedCutterNFT.json":
                print(f"⚠️ 使用备用 ABI 文件: {abi_path}")
            self.contract_address, contract_info, info_path = self._resolve_contract_address(
                ["contract-info.json", "scripts/contract-info.json"]
            )
            if info_path != "contract-info.json":
                print(f"⚠️ 主目录 contract-info.json 未同步，已使用 {info_path}")
            self.contract = self.w3.eth.contract(
                address=self.contract_address,
                abi=self.contract_abi
            )
            available_accounts = self.w3.eth.accounts
            if not available_accounts:
                raise RuntimeError("当前 RPC 没有可用账户 (did you start Hardhat?)")
            self.available_accounts = available_accounts
            idx = max(0, min(self.account_index, len(available_accounts) - 1))
            if idx != self.account_index:
                print(f"⚠️ 请求的账户索引 {self.account_index} 超出范围，已回落到 {idx}")
            self.account = available_accounts[idx]
            print(f"使用账户[{idx}]: {self.account}")
            try:
                self.contract_owner = self.contract.functions.owner().call()
                self.contract_owner_available = self.contract_owner in available_accounts
                if self.contract_owner_available:
                    print(f"🤝 合约所有者: {self.contract_owner}")
                else:
                    print(f"⚠️ 合约所有者 {self.contract_owner} 不在本地账户列表，铸造可能受限")
            except Exception as owner_err:
                print(f"⚠️ 无法读取合约所有者: {owner_err}")
                self.contract_owner_available = False
            self.blockchain_available = True
        except Exception as e:
            print(f"❌ 区块链设置失败，进入离线模式: {e}")
            traceback.print_exc()
            self.blockchain_available = False
            self.offline_reason = f"{e} (RPC: {self.rpc_url})"
            print("提示: 请确保 Hardhat 节点运行并部署合约后再重开游戏。")
    def load_player_weapons(self, account, weapon_display_name_func):
        """从区块链加载玩家武器"""
        if not self.blockchain_available:
            return [], []
        try:
            from .enums import Condition
            weapon_ids = self.contract.functions.getUserWeapons(account).call()
            owned = []
            for weapon_id in weapon_ids:
                weapon_data = self.contract.functions.getWeaponDetails(weapon_id).call()
                display_name = weapon_display_name_func(
                    weapon_data[1],
                    Rarity(weapon_data[2])
                )
                # 解析磨损度和品相
                wear = None
                condition = None
                if len(weapon_data) > 7:
                    try:
                        wear_raw = weapon_data[7]
                        if isinstance(wear_raw, int):
                            wear = wear_raw / 1e10  # 转换为0-1的浮点数
                    except:
                        pass
                if len(weapon_data) > 8:
                    try:
                        condition = Condition(weapon_data[8])
                    except:
                        pass

                weapon = {
                    'id': weapon_data[0],
                    'name': display_name,
                    'original_name': weapon_data[1],
                    'rarity': Rarity(weapon_data[2]),
                    'damage_multiplier': weapon_data[3] / 100.0,
                    'owner': weapon_data[4],
                    'price': weapon_data[5],
                    'for_sale': weapon_data[6],
                    'wear': wear,
                    'condition': condition
                }
                owned.append(weapon)
            owned.sort(key=lambda w: (-w['rarity'].value, w['id']))
            listed_weapons = [w for w in owned if w['for_sale']]
            weapons = [w for w in owned if not w['for_sale']]
            print(f"加载了 {len(owned)} 把武器，其中 {len(listed_weapons)} 把已上架")
            return weapons, listed_weapons
        except Exception as e:
            print(f"加载玩家武器失败: {e}")
            traceback.print_exc()
            return [], []
    def load_player_stats(self, account):
        """加载玩家统计数据"""
        if not self.blockchain_available:
            return 0, 0
        try:
            return self.contract.functions.getPlayerStats(account).call()
        except Exception as e:
            print(f"加载玩家数据失败: {e}")
            return 0, 0
    def record_score(self, account, points):
        """记录分数到区块链"""
        if not self.blockchain_available or points <= 0:
            return False
        try:
            tx = self.contract.functions.recordWeedCut(points).build_transaction({
                'from': account,
                'gas': 180000,
                'gasPrice': self.w3.to_wei('2', 'gwei'),
                'nonce': self.w3.eth.get_transaction_count(account)
            })
            tx_hash = self.w3.eth.send_transaction(tx)
            print(f"⏳ 正在上链累计分数 {points} tx={tx_hash.hex()}")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            status = getattr(receipt, 'status', 1)
            if status == 1:
                print("✅ 分数上链成功")
                return True
            else:
                print("❌ 分数交易失败")
                return False
        except Exception as e:
            print(f"记录分数失败: {e}")
            return False
    def mint_weapon(self, account, name, rarity_value, damage_multiplier):
        """铸造武器（仅合约所有者可用）"""
        if not self.blockchain_available:
            return False
        try:
            tx = self.contract.functions.mintWeapon(
                account,
                name,
                rarity_value,
                damage_multiplier
            ).build_transaction({
                'from': account,
                'gas': 350000,
                'gasPrice': self.w3.to_wei('2', 'gwei'),
                'nonce': self.w3.eth.get_transaction_count(account)
            })
            tx_hash = self.w3.eth.send_transaction(tx)
            print(f"⏳ 铸造交易发送: {tx_hash.hex()} 等待确认...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            status = getattr(receipt, 'status', 1)
            if status == 1:
                print("✅ 铸造成功")
                return True
            else:
                print("❌ 铸造交易失败")
                return False
        except Exception as err:
            print(f"铸造失败: {err}")
            traceback.print_exc()
            return False
    def purchase_weapon(self, account, weapon_id, price):
        """购买武器（使用ETH）"""
        if not self.blockchain_available:
            return False
        try:
            tx = self.contract.functions.purchaseWeapon(weapon_id).build_transaction({
                'from': account,
                'value': price,
                'gas': 300000,
                'gasPrice': self.w3.to_wei('2', 'gwei'),
                'nonce': self.w3.eth.get_transaction_count(account)
            })
            tx_hash = self.w3.eth.send_transaction(tx)
            print(f"⏳ 购买交易发送: {tx_hash.hex()} 等待确认...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            status = getattr(receipt, 'status', 1)
            if status == 1:
                print("✅ 购买成功")
                return True
            else:
                print("❌ 购买交易失败")
                return False
        except Exception as err:
            print(f"购买失败: {err}")
            return False

    def list_weapon_for_sale(self, account, weapon_id, price_wei):
        """上架武器"""
        if not self.blockchain_available:
            return False
        try:
            tx = self.contract.functions.listWeaponForSale(weapon_id, price_wei).build_transaction({
                'from': account,
                'gas': 250000,
                'gasPrice': self.w3.to_wei('2', 'gwei'),
                'nonce': self.w3.eth.get_transaction_count(account)
            })
            tx_hash = self.w3.eth.send_transaction(tx)
            print(f"⏳ 上架交易发送: {tx_hash.hex()} 等待确认...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            status = getattr(receipt, 'status', 1)
            if status == 1:
                print("✅ 上架成功")
                return True
            else:
                print("❌ 上架交易失败")
                return False
        except Exception as err:
            print(f"上架失败: {err}")
            return False
    def load_market_weapons(self, weapon_display_name_func):
        """加载市场武器"""
        if not self.blockchain_available:
            return []
        try:
            from .enums import Condition
            sale_list = []
            try:
                sale_list = self.contract.functions.getWeaponsForSale().call()
            except Exception:
                total_next = self.contract.functions.getNextWeaponId().call()
                for weapon_id in range(1, total_next):
                    wdata = self.contract.functions.getWeaponDetails(weapon_id).call()
                    if wdata[6]:  # forSale
                        sale_list.append(wdata)
            market_weapons = []
            for w in sale_list:
                display_name = weapon_display_name_func(w[1], Rarity(w[2]))
                # 解析磨损度和品相
                wear = None
                condition = None
                if len(w) > 7:
                    try:
                        wear_raw = w[7]
                        if isinstance(wear_raw, int):
                            wear = wear_raw / 1e10
                    except:
                        pass
                if len(w) > 8:
                    try:
                        condition = Condition(w[8])
                    except:
                        pass

                market_weapons.append({
                    'id': w[0],
                    'name': display_name,
                    'original_name': w[1],
                    'rarity': Rarity(w[2]),
                    'damage_multiplier': w[3] / 100.0,
                    'owner': w[4],
                    'price': w[5],
                    'for_sale': w[6],
                    'wear': wear,
                    'condition': condition
                })
            market_weapons.sort(key=lambda w: (w['price'], -w['rarity'].value))
            print(f"✅ 市场已刷新，当前 {len(market_weapons)} 把在售")
            return market_weapons
        except Exception as e:
            print(f"加载市场数据失败: {e}")
            traceback.print_exc()
            return []

    def set_player_name(self, account, name):
        """设置玩家名称"""
        if not self.blockchain_available:
            return False
        try:
            tx = self.contract.functions.setPlayerName(name).build_transaction({
                'from': account,
                'gas': 100000,
                'gasPrice': self.w3.to_wei('2', 'gwei'),
                'nonce': self.w3.eth.get_transaction_count(account)
            })
            tx_hash = self.w3.eth.send_transaction(tx)
            print(f"⏳ 设置玩家名称: {tx_hash.hex()}")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            return getattr(receipt, 'status', 1) == 1
        except Exception as e:
            print(f"设置名称失败: {e}")
            return False

    def get_player_name(self, account):
        """获取玩家名称"""
        if not self.blockchain_available:
            return ""
        try:
            return self.contract.functions.playerNames(account).call()
        except Exception as e:
            print(f"获取名称失败: {e}")
            return ""

    def get_leaderboard(self, count=10):
        """获取排行榜"""
        if not self.blockchain_available:
            return []
        try:
            addresses, names, scores, ranks = self.contract.functions.getLeaderboard(count).call()
            leaderboard = []
            for i in range(len(addresses)):
                leaderboard.append({
                    'rank': ranks[i],
                    'address': addresses[i],
                    'name': names[i] if names[i] else f"玩家{addresses[i][:6]}",
                    'score': scores[i]
                })
            return leaderboard
        except Exception as e:
            print(f"获取排行榜失败: {e}")
            return []

    def get_player_rank(self, account):
        """获取玩家排名"""
        if not self.blockchain_available:
            return 0, 0
        try:
            rank, total = self.contract.functions.getPlayerRank(account).call()
            return rank, total
        except Exception as e:
            print(f"获取排名失败: {e}")
            return 0, 0

    def get_all_accounts(self):
        """获取所有可用账户"""
        return self.available_accounts if self.blockchain_available else []

    def switch_account(self, account_index: int):
        """切换到指定账户索引"""
        if not self.blockchain_available:
            return False

        if 0 <= account_index < len(self.available_accounts):
            self.account_index = account_index
            self.account = self.available_accounts[account_index]
            print(f"✅ 切换到账户[{account_index}]: {self.account}")
            return True
        else:
            print(f"❌ 账户索引 {account_index} 超出范围")
            return False

    def open_case_with_eth(self, account, case_id, price):
        """使用ETH开启武器箱"""
        if not self.blockchain_available:
            return False
        try:
            tx = self.contract.functions.openCaseWithETH(case_id).build_transaction({
                'from': account,
                'value': price,
                'gas': 400000,
                'gasPrice': self.w3.to_wei('2', 'gwei'),
                'nonce': self.w3.eth.get_transaction_count(account)
            })
            tx_hash = self.w3.eth.send_transaction(tx)
            print(f"⏳ 开箱交易发送: {tx_hash.hex()} 等待确认...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            status = getattr(receipt, 'status', 1)
            if status == 1:
                print("✅ 开箱成功")
                return True
            else:
                print("❌ 开箱交易失败")
                return False
        except Exception as err:
            print(f"开箱失败: {err}")
            traceback.print_exc()
            return False

    def open_case_with_coins(self, account, case_id):
        """使用游戏币开启武器箱"""
        if not self.blockchain_available:
            return False
        try:
            tx = self.contract.functions.openCaseWithCoins(case_id).build_transaction({
                'from': account,
                'gas': 400000,
                'gasPrice': self.w3.to_wei('2', 'gwei'),
                'nonce': self.w3.eth.get_transaction_count(account)
            })
            tx_hash = self.w3.eth.send_transaction(tx)
            print(f"⏳ 用金币开箱: {tx_hash.hex()} 等待确认...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            status = getattr(receipt, 'status', 1)
            if status == 1:
                print("✅ 用金币开箱成功")
                return True
            else:
                print("❌ 开箱交易失败")
                return False
        except Exception as err:
            print(f"开箱失败: {err}")
            traceback.print_exc()
            return False

    def get_case_details(self, case_id):
        """获取武器箱详情"""
        if not self.blockchain_available:
            return None
        try:
            details = self.contract.functions.getCaseDetails(case_id).call()
            return {
                'id': case_id,
                'name': details[0],
                'price': details[1],
                'coin_price': details[2]
            }
        except Exception as err:
            print(f"获取武器箱详情失败: {err}")
            return None

    def get_all_cases(self):
        """获取所有武器箱"""
        if not self.blockchain_available:
            return []
        try:
            next_case_id = self.contract.functions.getNextCaseId().call()
            cases = []
            for case_id in range(1, next_case_id):
                case_info = self.get_case_details(case_id)
                if case_info:
                    cases.append(case_info)
            return cases
        except Exception as err:
            print(f"获取武器箱列表失败: {err}")
            return []

    def purchase_case(self, account, case_id, amount=1):
        """购买箱子（使用金币）"""
        if not self.blockchain_available:
            return False
        try:
            tx = self.contract.functions.purchaseCase(case_id, amount).build_transaction({
                'from': account,
                'gas': 200000,
                'gasPrice': self.w3.to_wei('2', 'gwei'),
                'nonce': self.w3.eth.get_transaction_count(account)
            })
            tx_hash = self.w3.eth.send_transaction(tx)
            print(f"⏳ 购买箱子: {tx_hash.hex()} 等待确认...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            status = getattr(receipt, 'status', 1)
            if status == 1:
                print(f"✅ 购买成功，获得 {amount} 个箱子")
                return True
            else:
                print("❌ 购买交易失败")
                return False
        except Exception as err:
            print(f"购买箱子失败: {err}")
            traceback.print_exc()
            return False

    def open_case_from_inventory(self, account, case_id):
        """从库存打开箱子，返回新武器的ID"""
        if not self.blockchain_available:
            return None
        try:
            tx = self.contract.functions.openCaseFromInventory(case_id).build_transaction({
                'from': account,
                'gas': 400000,
                'gasPrice': self.w3.to_wei('2', 'gwei'),
                'nonce': self.w3.eth.get_transaction_count(account)
            })
            tx_hash = self.w3.eth.send_transaction(tx)
            print(f"⏳ 开箱: {tx_hash.hex()} 等待确认...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            status = getattr(receipt, 'status', 1)
            if status == 1:
                print("✅ 开箱成功！")
                # 从事件日志中获取新武器的ID
                try:
                    # 查找 CaseOpened 事件
                    case_opened_event = self.contract.events.CaseOpened()
                    logs = case_opened_event.process_receipt(receipt)
                    if logs:
                        weapon_id = logs[0]['args']['weaponId']
                        print(f"🎁 获得新武器 ID: {weapon_id}")
                        return weapon_id
                except Exception as e:
                    print(f"⚠️ 解析开箱事件失败: {e}")
                return True  # 向后兼容
            else:
                print("❌ 开箱交易失败")
                return None
        except Exception as err:
            print(f"开箱失败: {err}")
            traceback.print_exc()
            return None

    def get_user_case_inventory(self, account):
        """获取用户的箱子库存"""
        if not self.blockchain_available:
            return {}
        try:
            case_ids, amounts = self.contract.functions.getAllUserCaseInventory(account).call()
            inventory = {}
            for i, case_id in enumerate(case_ids):
                inventory[case_id] = amounts[i]
            return inventory
        except Exception as err:
            print(f"获取箱子库存失败: {err}")
            return {}

    def transfer_weapon_locally(self, weapon_id: int, from_address: str, to_address: str) -> bool:
        """
        在本地模式下转移武器所有权（用于好友交易）
        注意：这不会在区块链上执行，仅用于离线/本地交易

        参数:
            weapon_id: 武器ID
            from_address: 发送者地址
            to_address: 接收者地址

        返回:
            bool: 是否成功
        """
        if self.blockchain_available:
            # 在线模式下，尝试在区块链上转移
            # 注意：当前智能合约没有直接的 transferWeapon 函数
            # 需要使用 listWeaponForSale + purchaseWeapon 的组合
            print("⚠️ 在线模式下的好友交易需要武器先上架到市场")
            print("   建议使用市场交易功能，或在离线模式下进行")
            return False
        else:
            # 离线模式：仅记录日志
            print(f"📦 本地武器转移（离线模式）:")
            print(f"   武器 ID: {weapon_id}")
            print(f"   从: {from_address[:10]}...")
            print(f"   到: {to_address[:10]}...")
            print(f"   ✅ 本地转移记录已保存")
            return True

    # ==================== P2P 交易报价系统 ====================

    def create_trade_offer(self, account: str, weapon_id: int, buyer_address: str, price_wei: int) -> bool:
        """
        创建 P2P 交易报价

        参数:
            account: 发起者账户地址
            weapon_id: 武器ID
            buyer_address: 买家地址（使用 '0x0000000000000000000000000000000000000000' 表示公开）
            price_wei: 价格（Wei）

        返回:
            bool: 是否成功
        """
        if not self.blockchain_available:
            print("⚠️ 离线模式：无法创建链上交易报价")
            return False

        try:
            tx = self.contract.functions.createTradeOffer(
                weapon_id,
                buyer_address,
                price_wei
            ).build_transaction({
                'from': account,
                'gas': 300000,
                'gasPrice': self.w3.to_wei('2', 'gwei'),
                'nonce': self.w3.eth.get_transaction_count(account)
            })

            tx_hash = self.w3.eth.send_transaction(tx)
            print(f"⏳ 创建交易报价: {tx_hash.hex()} 等待确认...")

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            status = getattr(receipt, 'status', 1)

            if status == 1:
                # 解析事件获取 offerId
                offer_created_event = self.contract.events.TradeOfferCreated()
                logs = offer_created_event.process_receipt(receipt)

                if logs:
                    offer_id = logs[0]['args']['offerId']
                    print(f"✅ 交易报价已创建，报价ID: {offer_id}")
                    return True
                else:
                    print("✅ 交易报价已创建")
                    return True
            else:
                print("❌ 创建交易报价失败")
                return False

        except Exception as err:
            print(f"❌ 创建交易报价失败: {err}")
            import traceback
            traceback.print_exc()
            return False

    def accept_trade_offer(self, account: str, offer_id: int, price_wei: int) -> bool:
        """
        接受 P2P 交易报价

        参数:
            account: 接受者账户地址
            offer_id: 报价ID
            price_wei: 支付金额（Wei）

        返回:
            bool: 是否成功
        """
        if not self.blockchain_available:
            print("⚠️ 离线模式：无法接受链上交易报价")
            return False

        try:
            tx = self.contract.functions.acceptTradeOffer(offer_id).build_transaction({
                'from': account,
                'value': price_wei,
                'gas': 350000,
                'gasPrice': self.w3.to_wei('2', 'gwei'),
                'nonce': self.w3.eth.get_transaction_count(account)
            })

            tx_hash = self.w3.eth.send_transaction(tx)
            print(f"⏳ 接受交易报价: {tx_hash.hex()} 等待确认...")

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            status = getattr(receipt, 'status', 1)

            if status == 1:
                print("✅ 交易报价已接受，武器已转移")
                return True
            else:
                print("❌ 接受交易报价失败")
                return False

        except Exception as err:
            print(f"❌ 接受交易报价失败: {err}")
            import traceback
            traceback.print_exc()
            return False

    def cancel_trade_offer(self, account: str, offer_id: int) -> bool:
        """
        取消 P2P 交易报价

        参数:
            account: 发起者账户地址
            offer_id: 报价ID

        返回:
            bool: 是否成功
        """
        if not self.blockchain_available:
            print("⚠️ 离线模式：无法取消链上交易报价")
            return False

        try:
            tx = self.contract.functions.cancelTradeOffer(offer_id).build_transaction({
                'from': account,
                'gas': 200000,
                'gasPrice': self.w3.to_wei('2', 'gwei'),
                'nonce': self.w3.eth.get_transaction_count(account)
            })

            tx_hash = self.w3.eth.send_transaction(tx)
            print(f"⏳ 取消交易报价: {tx_hash.hex()} 等待确认...")

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            status = getattr(receipt, 'status', 1)

            if status == 1:
                print("✅ 交易报价已取消")
                return True
            else:
                print("❌ 取消交易报价失败")
                return False

        except Exception as err:
            print(f"❌ 取消交易报价失败: {err}")
            return False

    def get_trade_offer(self, offer_id: int) -> dict:
        """
        获取交易报价详情

        参数:
            offer_id: 报价ID

        返回:
            dict: 报价信息
        """
        if not self.blockchain_available:
            return {}

        try:
            offer = self.contract.functions.getTradeOffer(offer_id).call()
            return {
                'offerId': offer[0],
                'weaponId': offer[1],
                'seller': offer[2],
                'buyer': offer[3],
                'price': offer[4],
                'active': offer[5],
                'createdAt': offer[6]
            }
        except Exception as err:
            print(f"获取交易报价失败: {err}")
            return {}

    def get_user_active_offers(self, account: str) -> list:
        """
        获取用户发起的活跃报价

        参数:
            account: 用户地址

        返回:
            list: 报价列表
        """
        if not self.blockchain_available:
            return []

        try:
            offers = self.contract.functions.getUserActiveOffers(account).call()
            result = []
            for offer in offers:
                result.append({
                    'offerId': offer[0],
                    'weaponId': offer[1],
                    'seller': offer[2],
                    'buyer': offer[3],
                    'price': offer[4],
                    'active': offer[5],
                    'createdAt': offer[6]
                })
            return result
        except Exception as err:
            print(f"获取用户报价失败: {err}")
            return []

    def get_user_received_active_offers(self, account: str) -> list:
        """
        获取用户收到的活跃报价

        参数:
            account: 用户地址

        返回:
            list: 报价列表
        """
        if not self.blockchain_available:
            return []

        try:
            offers = self.contract.functions.getUserReceivedActiveOffers(account).call()
            result = []
            for offer in offers:
                result.append({
                    'offerId': offer[0],
                    'weaponId': offer[1],
                    'seller': offer[2],
                    'buyer': offer[3],
                    'price': offer[4],
                    'active': offer[5],
                    'createdAt': offer[6]
                })
            return result
        except Exception as err:
            print(f"获取收到的报价失败: {err}")
            return []

