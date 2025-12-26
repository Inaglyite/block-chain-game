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
        """生成钱包地址（基于用户名和时间戳）"""
        # 创建一个确定性的地址，但看起来像以太坊地址
        data = f"{username}{datetime.now().isoformat()}{secrets.token_hex(8)}"
        address_hash = hashlib.sha256(data.encode()).hexdigest()[:40]
        return f"0x{address_hash}"
    
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
    
    def complete_trade(self, trade_id: str) -> Tuple[bool, str]:
        """标记交易为已完成"""
        if not self.current_user:
            return False, "请先登录"
        
        current_data = self.users[self.current_user]
        trade_requests = current_data.get('trade_requests', [])
        
        for req in trade_requests:
            if req['trade_id'] == trade_id:
                req['status'] = 'completed'
                self.save_data()
                return True, "交易已完成"
        
        return False, "交易请求不存在"
    
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

