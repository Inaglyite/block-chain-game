# -*- coding: utf-8 -*-
"""
用户管理模块 - 处理用户注册、登录、好友系统
"""
import json
import os
import hashlib
import secrets
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend


class UserManager:
    """用户管理器 - 处理用户认证和好友系统"""
    
    def __init__(self, data_file="user_data.json"):
        self.data_file = data_file
        self.users = {}
        self.current_user = None
        self.load_data()
        self.migrate_wallet_addresses()  # 迁移旧用户的钱包地址

    def load_data(self):
        """加载用户数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
                print(f"✅ 加载了 {len(self.users)} 个用户数据")
            except Exception as e:
                print(f"⚠️ 加载用户数据失败: {e}")
                self.users = {}
        else:
            self.users = {}
    
    def migrate_wallet_addresses(self):
        """
        迁移旧用户的钱包地址
        将随机生成的地址替换为 Hardhat 固定测试账户地址
        """
        HARDHAT_ACCOUNTS = [
            "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
            "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
            "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
            "0x90F79bf6EB2c4f870365E785982E1f101E93b906",
            "0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65",
            "0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc",
            "0x976EA74026E726554dB657fA54763abd0C3a0aa9",
            "0x14dC79964da2C08b23698B3D3cc7Ca32193d9955",
            "0x23618e81E3f5cdF7f54C3d65f7FBc0aBf5B21E8f",
            "0xa0Ee7A142d267C1f36714E4a8F75612F20a79720",
            "0xBcd4042DE499D14e55001CcbB24a551F3b954096",
            "0x71bE63f3384f5fb98995898A86B02Fb2426c5788",
            "0xFABB0ac9d68B0B445fB7357272Ff202C5651694a",
            "0x1CBd3b2770909D4e10f157cABC84C7264073C9Ec",
            "0xdF3e18d64BC6A983f673Ab319CCaE4f1a57C7097",
            "0xcd3B766CCDd6AE721141F452C550Ca635964ce71",
            "0x2546BcD3c84621e976D8185a91A922aE77ECEc30",
            "0xbDA5747bFD65F08deb54cb465eB87D40e51B197E",
            "0xdD2FD4581271e230360230F9337D5c0430Bf44C0",
            "0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199",
        ]

        migrated = False
        for i, (username, user_data) in enumerate(self.users.items()):
            old_address = user_data.get('wallet_address', '')

            # 检查地址是否需要迁移（不在 Hardhat 账户列表中）
            if old_address not in HARDHAT_ACCOUNTS:
                # 分配 Hardhat 账户
                new_index = i % len(HARDHAT_ACCOUNTS)
                new_address = HARDHAT_ACCOUNTS[new_index]
                user_data['wallet_address'] = new_address
                print(f"🔄 迁移用户 {username}: {old_address[:10]}... -> {new_address}")
                migrated = True

        if migrated:
            self.save_data()
            print("✅ 钱包地址迁移完成")

    def save_data(self):
        """保存用户数据"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=2, ensure_ascii=False)
            print("✅ 用户数据已保存")
        except Exception as e:
            print(f"❌ 保存用户数据失败: {e}")
    
    def hash_password(self, password: str, salt: str = None) -> Tuple[str, str]:
        """使用 SHA-256 + 盐值哈希密码"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        # 使用 PBKDF2 进行密码哈希（更安全的方式）
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # 迭代次数
        ).hex()
        
        return password_hash, salt
    
    def verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """验证密码"""
        computed_hash, _ = self.hash_password(password, salt)
        return computed_hash == password_hash
    
    def generate_wallet_address(self, username: str) -> str:
        """
        生成钱包地址（使用 Hardhat 的固定测试账户）
        Hardhat 提供了 20 个固定的测试账户，地址是确定性的
        我们根据已注册用户数量来分配账户
        """
        # Hardhat 的前 20 个测试账户地址（这些地址是固定的）
        HARDHAT_ACCOUNTS = [
            "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",  # Account #0
            "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",  # Account #1
            "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",  # Account #2
            "0x90F79bf6EB2c4f870365E785982E1f101E93b906",  # Account #3
            "0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65",  # Account #4
            "0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc",  # Account #5
            "0x976EA74026E726554dB657fA54763abd0C3a0aa9",  # Account #6
            "0x14dC79964da2C08b23698B3D3cc7Ca32193d9955",  # Account #7
            "0x23618e81E3f5cdF7f54C3d65f7FBc0aBf5B21E8f",  # Account #8
            "0xa0Ee7A142d267C1f36714E4a8F75612F20a79720",  # Account #9
            "0xBcd4042DE499D14e55001CcbB24a551F3b954096",  # Account #10
            "0x71bE63f3384f5fb98995898A86B02Fb2426c5788",  # Account #11
            "0xFABB0ac9d68B0B445fB7357272Ff202C5651694a",  # Account #12
            "0x1CBd3b2770909D4e10f157cABC84C7264073C9Ec",  # Account #13
            "0xdF3e18d64BC6A983f673Ab319CCaE4f1a57C7097",  # Account #14
            "0xcd3B766CCDd6AE721141F452C550Ca635964ce71",  # Account #15
            "0x2546BcD3c84621e976D8185a91A922aE77ECEc30",  # Account #16
            "0xbDA5747bFD65F08deb54cb465eB87D40e51B197E",  # Account #17
            "0xdD2FD4581271e230360230F9337D5c0430Bf44C0",  # Account #18
            "0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199",  # Account #19
        ]

        # 计算当前用户索引（用于分配账户）
        user_index = len(self.users)

        # 如果用户数超过 20，循环使用账户（但这不推荐）
        if user_index >= len(HARDHAT_ACCOUNTS):
            print(f"⚠️ 警告：用户数量超过 {len(HARDHAT_ACCOUNTS)}，重复使用账户")
            user_index = user_index % len(HARDHAT_ACCOUNTS)

        address = HARDHAT_ACCOUNTS[user_index]
        print(f"💼 为用户 {username} 分配 Hardhat 账户 #{user_index}: {address}")
        return address

    def register_user(self, username: str, email: str, password: str) -> Tuple[bool, str, Optional[str]]:
        """
        注册新用户
        返回: (成功, 消息, 钱包地址)
        """
        # 验证用户名
        if not username or len(username) < 3:
            return False, "用户名至少需要3个字符", None
        
        if username in self.users:
            return False, "用户名已存在", None
        
        # 验证邮箱
        if not email or '@' not in email:
            return False, "请输入有效的邮箱地址", None
        
        # 检查邮箱是否已被使用
        for user_data in self.users.values():
            if user_data.get('email') == email:
                return False, "邮箱已被注册", None
        
        # 验证密码强度
        if len(password) < 6:
            return False, "密码至少需要6个字符", None
        
        # 生成密码哈希
        password_hash, salt = self.hash_password(password)
        
        # 生成钱包地址
        wallet_address = self.generate_wallet_address(username)
        
        # 生成 RSA 密钥对用于好友交易加密
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        
        # 序列化密钥
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        # 创建用户数据
        user_data = {
            'username': username,
            'email': email,
            'password_hash': password_hash,
            'salt': salt,
            'wallet_address': wallet_address,
            'created_at': datetime.now().isoformat(),
            'friends': [],  # 好友列表
            'friend_requests': [],  # 待处理的好友请求
            'trade_requests': [],  # 交易请求
            'public_key': public_pem,
            'private_key': private_pem,
            'profile': {
                'level': 1,
                'total_score': 0,
                'games_played': 0
            }
        }
        
        self.users[username] = user_data
        self.save_data()
        
        return True, "注册成功！", wallet_address
    
    def login(self, username: str, password: str) -> Tuple[bool, str]:
        """
        用户登录
        返回: (成功, 消息)
        """
        if username not in self.users:
            return False, "用户名不存在"
        
        user_data = self.users[username]
        
        if self.verify_password(password, user_data['password_hash'], user_data['salt']):
            self.current_user = username
            return True, "登录成功！"
        else:
            return False, "密码错误"
    
    def logout(self):
        """登出"""
        self.current_user = None
    
    def get_current_user_data(self) -> Optional[Dict]:
        """获取当前用户数据"""
        if self.current_user and self.current_user in self.users:
            return self.users[self.current_user]
        return None
    
    def get_wallet_address(self) -> str:
        """获取当前用户的钱包地址"""
        user_data = self.get_current_user_data()
        if user_data:
            return user_data['wallet_address']
        return "0x0000000000000000000000000000000000000000"
    
    # ==================== 好友系统 ====================
    
    def send_friend_request(self, target_username: str) -> Tuple[bool, str]:
        """发送好友请求"""
        if not self.current_user:
            return False, "请先登录"
        
        if target_username not in self.users:
            return False, "用户不存在"
        
        if target_username == self.current_user:
            return False, "不能添加自己为好友"
        
        current_data = self.users[self.current_user]
        target_data = self.users[target_username]
        
        # 检查是否已经是好友
        if target_username in current_data['friends']:
            return False, "已经是好友了"
        
        # 检查是否已经发送过请求
        if self.current_user in target_data['friend_requests']:
            return False, "已发送过好友请求"
        
        # 添加好友请求
        target_data['friend_requests'].append(self.current_user)
        self.save_data()
        
        return True, f"已向 {target_username} 发送好友请求"
    
    def accept_friend_request(self, requester_username: str) -> Tuple[bool, str]:
        """接受好友请求"""
        if not self.current_user:
            return False, "请先登录"
        
        current_data = self.users[self.current_user]
        
        if requester_username not in current_data['friend_requests']:
            return False, "没有来自该用户的好友请求"
        
        if requester_username not in self.users:
            return False, "请求用户不存在"
        
        # 移除请求
        current_data['friend_requests'].remove(requester_username)
        
        # 添加双向好友关系
        current_data['friends'].append(requester_username)
        self.users[requester_username]['friends'].append(self.current_user)
        
        self.save_data()
        
        return True, f"已添加 {requester_username} 为好友"
    
    def reject_friend_request(self, requester_username: str) -> Tuple[bool, str]:
        """拒绝好友请求"""
        if not self.current_user:
            return False, "请先登录"
        
        current_data = self.users[self.current_user]
        
        if requester_username not in current_data['friend_requests']:
            return False, "没有来自该用户的好友请求"
        
        current_data['friend_requests'].remove(requester_username)
        self.save_data()
        
        return True, f"已拒绝 {requester_username} 的好友请求"
    
    def get_friends_list(self) -> List[str]:
        """获取好友列表"""
        if not self.current_user:
            return []
        
        current_data = self.users[self.current_user]
        return current_data.get('friends', [])
    
    def get_friend_requests(self) -> List[str]:
        """获取待处理的好友请求"""
        if not self.current_user:
            return []
        
        current_data = self.users[self.current_user]
        return current_data.get('friend_requests', [])
    
    # ==================== 好友交易系统 ====================
    
    def create_trade_request(self, friend_username: str, weapon_id: int, price_eth: float) -> Tuple[bool, str]:
        """
        创建好友交易请求
        使用 RSA 加密交易信息确保安全
        """
        if not self.current_user:
            return False, "请先登录"
        
        current_data = self.users[self.current_user]
        
        # 验证是否是好友
        if friend_username not in current_data['friends']:
            return False, "只能与好友进行交易"
        
        if friend_username not in self.users:
            return False, "好友不存在"
        
        friend_data = self.users[friend_username]
        
        # 创建交易请求
        trade_request = {
            'from_user': self.current_user,
            'to_user': friend_username,
            'weapon_id': weapon_id,
            'price_eth': price_eth,
            'created_at': datetime.now().isoformat(),
            'status': 'pending',  # pending, accepted, rejected, completed
            'trade_id': secrets.token_hex(16)
        }
        
        # 使用好友的公钥加密交易信息（这里简化处理，实际可以加密敏感信息）
        try:
            # 获取好友公钥
            public_key_pem = friend_data['public_key']
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode('utf-8'),
                backend=default_backend()
            )
            
            # 加密交易数据（这里加密交易ID作为示例）
            trade_signature = public_key.encrypt(
                trade_request['trade_id'].encode('utf-8'),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            trade_request['encrypted_signature'] = trade_signature.hex()
            
        except Exception as e:
            print(f"⚠️ 加密交易数据失败: {e}")
            trade_request['encrypted_signature'] = None
        
        # 添加到好友的交易请求列表
        if 'trade_requests' not in friend_data:
            friend_data['trade_requests'] = []
        
        friend_data['trade_requests'].append(trade_request)
        self.save_data()
        
        return True, f"已向 {friend_username} 发送交易请求"
    
    def get_trade_requests(self) -> List[Dict]:
        """获取收到的交易请求"""
        if not self.current_user:
            return []
        
        current_data = self.users[self.current_user]
        return current_data.get('trade_requests', [])
    
    def accept_trade_request(self, trade_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        接受交易请求
        返回: (成功, 消息, 交易数据)
        """
        if not self.current_user:
            return False, "请先登录", None
        
        current_data = self.users[self.current_user]
        trade_requests = current_data.get('trade_requests', [])
        
        # 查找交易请求
        trade_request = None
        for req in trade_requests:
            if req['trade_id'] == trade_id:
                trade_request = req
                break
        
        if not trade_request:
            return False, "交易请求不存在", None
        
        if trade_request['status'] != 'pending':
            return False, "交易请求已处理", None
        
        # 验证加密签名（解密）
        try:
            if trade_request.get('encrypted_signature'):
                private_key_pem = current_data['private_key']
                private_key = serialization.load_pem_private_key(
                    private_key_pem.encode('utf-8'),
                    password=None,
                    backend=default_backend()
                )
                
                encrypted_sig = bytes.fromhex(trade_request['encrypted_signature'])
                decrypted_trade_id = private_key.decrypt(
                    encrypted_sig,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                ).decode('utf-8')
                
                if decrypted_trade_id != trade_id:
                    return False, "交易签名验证失败", None
                
                print("✅ 交易签名验证成功（RSA解密）")
        except Exception as e:
            print(f"⚠️ 交易签名验证失败: {e}")
        
        # 标记为已接受
        trade_request['status'] = 'accepted'
        self.save_data()
        
        return True, "交易请求已接受，等待区块链确认", trade_request
    
    def reject_trade_request(self, trade_id: str) -> Tuple[bool, str]:
        """拒绝交易请求"""
        if not self.current_user:
            return False, "请先登录"
        
        current_data = self.users[self.current_user]
        trade_requests = current_data.get('trade_requests', [])
        
        for req in trade_requests:
            if req['trade_id'] == trade_id:
                req['status'] = 'rejected'
                self.save_data()
                return True, "已拒绝交易请求"
        
        return False, "交易请求不存在"
    
    def complete_trade(self, trade_id: str, weapon_data: dict = None) -> Tuple[bool, str]:
        """
        标记交易为已完成并执行武器转移
        将武器从发起者转移到接受者（当前用户）

        参数:
            trade_id: 交易ID
            weapon_data: 武器数据字典（用于本地存储）
        """
        if not self.current_user:
            return False, "请先登录"
        
        current_data = self.users[self.current_user]
        trade_requests = current_data.get('trade_requests', [])
        
        # 查找交易请求
        trade_req = None
        for req in trade_requests:
            if req['trade_id'] == trade_id:
                trade_req = req
                break

        if not trade_req:
            return False, "交易请求不存在"

        # 标记为已完成
        trade_req['status'] = 'completed'

        # 执行武器转移
        from_user = trade_req['from_user']
        to_user = self.current_user  # 接受者是当前用户
        weapon_id = trade_req['weapon_id']

        print(f"🔄 执行本地武器转移: 武器 ID {weapon_id}")
        print(f"   从 {from_user} -> 到 {to_user}")

        # 在本地用户数据中记录武器所有权
        # 初始化武器列表（如果不存在）
        if 'local_weapons' not in current_data:
            current_data['local_weapons'] = {}

        if from_user in self.users:
            from_user_data = self.users[from_user]
            if 'local_weapons' not in from_user_data:
                from_user_data['local_weapons'] = {}

            # 从发起者移除武器
            if str(weapon_id) in from_user_data['local_weapons']:
                # 转移武器数据
                weapon_info = from_user_data['local_weapons'].pop(str(weapon_id))
                print(f"   ✅ 从 {from_user} 移除武器 {weapon_id}")

                # 添加到接受者
                current_data['local_weapons'][str(weapon_id)] = weapon_info
                print(f"   ✅ 添加武器 {weapon_id} 到 {to_user}")
            elif weapon_data:
                # 如果发起者没有本地记录，但提供了武器数据，直接添加到接受者
                current_data['local_weapons'][str(weapon_id)] = weapon_data
                print(f"   ✅ 使用提供的武器数据添加到 {to_user}")

        # 记录交易历史
        if 'trade_history' not in current_data:
            current_data['trade_history'] = []

        current_data['trade_history'].append({
            'trade_id': trade_id,
            'from_user': from_user,
            'to_user': to_user,
            'weapon_id': weapon_id,
            'price_eth': trade_req['price_eth'],
            'completed_at': datetime.now().isoformat(),
            'type': 'received'
        })

        # 在发起者的数据中也记录
        if from_user in self.users:
            from_user_data = self.users[from_user]
            if 'trade_history' not in from_user_data:
                from_user_data['trade_history'] = []

            from_user_data['trade_history'].append({
                'trade_id': trade_id,
                'from_user': from_user,
                'to_user': to_user,
                'weapon_id': weapon_id,
                'price_eth': trade_req['price_eth'],
                'completed_at': datetime.now().isoformat(),
                'type': 'sent'
            })

        self.save_data()
        print(f"✅ 武器转移完成并已保存")
        return True, "交易已完成，武器所有权已转移"

    def search_users(self, query: str) -> List[Dict]:
        """搜索用户（用于添加好友）"""
        if not query or len(query) < 2:
            return []
        
        results = []
        query_lower = query.lower()
        
        for username, user_data in self.users.items():
            if username == self.current_user:
                continue
            
            if query_lower in username.lower() or query_lower in user_data.get('email', '').lower():
                results.append({
                    'username': username,
                    'wallet_address': user_data['wallet_address'],
                    'level': user_data.get('profile', {}).get('level', 1)
                })
        
        return results[:10]  # 最多返回10个结果

