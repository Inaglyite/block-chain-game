# 🎮 Weed Cutter - 区块链 NFT 游戏

一个完整的区块链 NFT 游戏，每个武器都是链上独一无二的 ERC721 NFT。

![Blockchain](https://img.shields.io/badge/Blockchain-Ethereum-blue)
![Solidity](https://img.shields.io/badge/Solidity-0.8.28-green)
![Python](https://img.shields.io/badge/Python-3.8+-yellow)
![License](https://img.shields.io/badge/License-MIT-red)

## ✨ 核心特性

### 🔗 真正的区块链游戏
- ✅ 所有武器都是 **ERC721 NFT**
- ✅ 符合以太坊标准，完全去中心化
- ✅ 玩家真正拥有游戏资产
- ✅ 可在区块链浏览器验证所有权

### 🎯 游戏玩法
- 🌿 割草赚取金币
- 📦 开箱获得随机 NFT 武器
- ⚔️ 4 种武器类型 × 4 个稀有度 = 16 种武器
- 📊 磨损度系统（影响外观）
- 🏆 排行榜和成就系统

### 💰 经济系统
- 💎 市场交易：上架/购买武器 NFT
- 🤝 P2P 交易：好友间私密交易
- 💵 ETH 支付：真实的链上交易
- 📈 动态定价：市场推荐价格

### 🔐 安全特性
- 🔒 RSA 加密的用户系统
- ⛓️ 智能合约保障交易安全
- 🚫 防止双花和伪造
- ✅ 完整的交易历史追溯

## 📦 技术栈

### 区块链
- **Ethereum** - 区块链平台
- **Solidity 0.8.28** - 智能合约语言
- **Hardhat** - 开发环境
- **Web3.py** - Python 区块链交互库

### 游戏引擎
- **Pygame** - 游戏框架
- **Python 3.8+** - 主要编程语言

### 智能合约
- **ERC721** - NFT 标准
- **OpenZeppelin** - 安全组件

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone <your-repo-url>
cd block-weed-game
```

### 2. 安装依赖
```bash
# Python 依赖
pip install -r requirements.txt

# Node.js 依赖
npm install
```

### 3. 启动游戏
```bash
# Linux/Mac
./run_game.sh

# Windows
run_game.bat
```

详细说明请查看 [快速开始指南](QUICK_START.md)

## 📖 文档

- 📘 [快速开始指南](QUICK_START.md) - 5 分钟上手
- 📗 [NFT 系统指南](NFT_SYSTEM_GUIDE.md) - 完整技术文档
- 📕 [实施总结](IMPLEMENTATION_SUMMARY.md) - 开发历程

## 🎮 游戏截图

### 主菜单
```
╔══════════════════════════════════════╗
║     🎮 Weed Cutter NFT Game 🎮      ║
║                                      ║
║  ▶ 开始游戏                          ║
║    个人中心                          ║
║    排行榜                            ║
║    切换账户                          ║
║    退出游戏                          ║
╚══════════════════════════════════════╝
```

### 游戏界面
```
┌────────────────────────────────────┐
│ 💰 金币: 150  🏆 分数: 450        │
│ ⚔️ Epic Sword (EPIC) 伤害: 1.65x │
├────────────────────────────────────┤
│                                    │
│       🌿 🌿 🌿                    │
│    🌿  😊  🌿                     │
│       🌿 🌿 🌿                    │
│                                    │
└────────────────────────────────────┘
```

### 箱子商店
```
╔════════════════════════════════════╗
║         🎁 箱子商店 🎁            ║
╠════════════════════════════════════╣
║  👴 盗贼老人：                    ║
║  "勇者，要不要买点箱子！"          ║
╠════════════════════════════════════╣
║  🔪 刀箱子    50 金币  [购买]     ║
║  ⚔️ 剑箱子    50 金币  [购买]     ║
║  🪓 斧头箱子  50 金币  [购买]     ║
║  🔨 镰刀箱子  50 金币  [购买]     ║
╚════════════════════════════════════╝
```

## 🏗️ 项目结构

```
block-weed-game/
├── contracts/              # 智能合约
│   └── WeedCutterNFT.sol  # 主合约（ERC721）
├── src/                   # 游戏源码
│   ├── game.py           # 游戏主逻辑
│   ├── blockchain.py     # 区块链交互
│   ├── user_manager.py   # 用户管理
│   ├── weapon.py         # 武器系统
│   ├── ui.py            # UI 渲染
│   └── ...
├── scripts/              # 部署脚本
│   └── deploy.ts        # 合约部署
├── test_nft_system.py   # NFT 测试脚本
├── main.py              # 游戏入口
└── README.md            # 本文件
```

## 🧪 测试

### 运行 NFT 系统测试
```bash
python test_nft_system.py
```

### 测试输出示例
```
✅ 已铸造武器数量: 3
✅ balanceOf: 3 个 NFT
✅ ERC721 标准函数正常工作
✅ 市场系统工作正常
✅ P2P 交易系统工作正常
🎮 你的游戏现在是一个真正的区块链 NFT 游戏！
```

## 📊 智能合约功能

### ERC721 标准
```solidity
// 查询余额
function balanceOf(address owner) external view returns (uint256);

// 查询所有者
function ownerOf(uint256 tokenId) external view returns (address);

// 转移 NFT
function transferFrom(address from, address to, uint256 tokenId) external;
```

### 游戏功能
```solidity
// 开箱铸造武器
function openCaseFromInventory(uint256 caseId) public;

// 上架市场
function listWeaponForSale(uint256 weaponId, uint256 price) public;

// 购买武器
function purchaseWeapon(uint256 weaponId) public payable;

// P2P 交易
function createTradeOffer(uint256 weaponId, address buyer, uint256 price) public;
function acceptTradeOffer(uint256 offerId) public payable;
```

## 🎯 武器系统

### 稀有度
| 稀有度 | 颜色 | 伤害倍率 | 掉落概率 |
|--------|------|----------|----------|
| 普通 (COMMON) | ⚪ 白色 | 1.0x-1.1x | 50% |
| 稀有 (RARE) | 🔵 蓝色 | 1.3x-1.4x | 30% |
| 史诗 (EPIC) | 🟣 紫色 | 1.6x-1.7x | 15% |
| 传说 (LEGENDARY) | 🟠 橙色 | 2.0x-2.1x | 5% |

### 武器类型
- 🔪 刀 (Knife/Cutter)
- ⚔️ 剑 (Sword/Blade)
- 🪓 斧头 (Axe)
- 🔨 镰刀 (Sickle/Scythe)

### 磨损度
- S 级: 0% - 5% 磨损
- A 级: 5% - 15% 磨损
- B 级: 15% - 30% 磨损
- C 级: 30% - 50% 磨损
- D 级: 50% - 75% 磨损
- E 级: 75% - 100% 磨损

## 🔄 交易流程

### 市场交易
```
卖家上架 → 设置价格 → 买家浏览 → 支付 ETH → NFT 转移
```

### P2P 交易
```
发起报价 → 指定接收者 → 接收者查看 → 接受报价 → NFT 转移
```

## 🛠️ 开发

### 编译合约
```bash
npx hardhat compile
```

### 部署合约
```bash
npx hardhat run scripts/deploy.ts --network localhost
```

### 运行测试
```bash
npx hardhat test
```

## 📝 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交 Pull Request！

## 📧 联系方式

如有问题或建议，请提交 Issue。

---

## 🌟 特别说明

这是一个**真正的区块链 NFT 游戏**，不同于传统游戏：

- ✅ 武器是链上资产，你真正拥有它们
- ✅ 所有交易都记录在区块链上
- ✅ 符合 ERC721 标准，可跨平台使用
- ✅ 智能合约保障安全，无法篡改

**这不仅仅是一个游戏，更是区块链技术的实际应用！**

---

**开始你的 NFT 冒险之旅吧！** 🎮⚔️💎

