// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

// 简化的 ERC721 接口（核心功能）
interface IERC721 {
    event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);
    event Approval(address indexed owner, address indexed approved, uint256 indexed tokenId);

    function balanceOf(address owner) external view returns (uint256 balance);
    function ownerOf(uint256 tokenId) external view returns (address owner);
    function transferFrom(address from, address to, uint256 tokenId) external;
    function approve(address to, uint256 tokenId) external;
    function getApproved(uint256 tokenId) external view returns (address operator);
}

contract WeedCutterNFT is IERC721 {
    // 磨损度枚举，扩展为六档：S A B C D E
    enum Condition { S, A, B, C, D, E }

    // 武器配置结构体，用于武器箱中的武器定义
    struct WeaponConfig {
        string name;
        Rarity rarity;
        uint256 baseDamageMultiplier;
        uint256 weight;  // 概率权重
    }

    // 武器箱结构体
    struct Case {
        uint256 id;
        string name;
        uint256 price;  // 开箱价格，以wei为单位
        uint256 coinPrice;  // 开箱价格，以游戏币为单位
        uint256[] weaponConfigIds;  // 包含的武器配置ID列表
    }

    // wear: 0 .. 10**10-1 (表示 0.0000000000 .. 0.9999999999)
    struct Weapon {
        uint256 id;
        string name;
        Rarity rarity;
        uint256 damageMultiplier;
        address owner;
        uint256 price;
        bool forSale;
        uint256 wear;
        Condition condition;  // 兼容性保留
    }

    enum Rarity { COMMON, RARE, EPIC, LEGENDARY }

    mapping(uint256 => Weapon) public weapons;
    mapping(address => uint256[]) public userWeapons;
    mapping(address => uint256) public scores;
    mapping(address => uint256) public coins;

    // ERC721 必需的映射
    mapping(uint256 => address) private _tokenApprovals;
    mapping(address => uint256) private _balances;

    // 武器箱相关的映射
    mapping(uint256 => Case) public cases;
    mapping(uint256 => WeaponConfig) public weaponConfigs;
    uint256 private nextCaseId = 1;
    uint256 private nextWeaponConfigId = 1;

    // 箱子库存：玩家地址 => (箱子ID => 数量)
    mapping(address => mapping(uint256 => uint256)) public userCaseInventory;

    // 排行榜相关
    address[] public players;  // 所有玩过游戏的玩家地址
    mapping(address => bool) public hasPlayed;  // 记录玩家是否玩过游戏
    mapping(address => string) public playerNames;  // 玩家自定义名称

    uint256 private nextWeaponId = 1;
    address public owner;

    event WeaponMinted(address indexed to, uint256 weaponId, Rarity rarity, Condition condition, uint256 wear);
    event WeaponSold(address indexed from, address indexed to, uint256 weaponId);
    event WeaponListed(uint256 weaponId, uint256 price);
    event WeedCut(address indexed player, uint256 score, uint256 coinsEarned);
    event CaseOpened(address indexed player, uint256 caseId, uint256 weaponId, Rarity rarity, Condition condition, uint256 wear);
    event CaseCreated(uint256 caseId, string name, uint256 price, uint256 coinPrice);
    event CasePurchased(address indexed buyer, uint256 caseId, uint256 amount);
    event PlayerNameSet(address indexed player, string name);

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    // 用于生成伪随机数的nonce
    uint256 private nonce = 0;

    constructor() {
        owner = msg.sender;
        // 初始化一些默认武器 - 使用英文名称
        // 为初始武器生成磨损度并铸造
        uint256 w1 = _generateRandomWear();
        _mintWeapon(msg.sender, "Starter Cutter", Rarity.COMMON, 100, w1, _wearToCondition(w1));
        uint256 w2 = _generateRandomWear();
        _mintWeapon(msg.sender, "Sharp Sickle", Rarity.RARE, 120, w2, _wearToCondition(w2));
        uint256 w3 = _generateRandomWear();
        _mintWeapon(msg.sender, "Epic Sword", Rarity.EPIC, 150, w3, _wearToCondition(w3));

        // 初始化武器配置 - 按类型和稀有度分类
        // 刀类武器 (Knife/Cutter)
        _createWeaponConfig("Starter Knife", Rarity.COMMON, 100, 50);
        _createWeaponConfig("Sharp Knife", Rarity.RARE, 130, 30);
        _createWeaponConfig("Epic Knife", Rarity.EPIC, 160, 15);
        _createWeaponConfig("Legendary Knife", Rarity.LEGENDARY, 200, 5);

        // 剑类武器 (Sword/Blade)
        _createWeaponConfig("Basic Sword", Rarity.COMMON, 105, 50);
        _createWeaponConfig("Golden Blade", Rarity.RARE, 135, 30);
        _createWeaponConfig("Epic Sword", Rarity.EPIC, 165, 15);
        _createWeaponConfig("Legendary Blade", Rarity.LEGENDARY, 205, 5);

        // 斧头类武器 (Axe)
        _createWeaponConfig("Basic Axe", Rarity.COMMON, 110, 50);
        _createWeaponConfig("Battle Axe", Rarity.RARE, 140, 30);
        _createWeaponConfig("Epic Axe", Rarity.EPIC, 170, 15);
        _createWeaponConfig("Legendary Axe", Rarity.LEGENDARY, 210, 5);

        // 镰刀类武器 (Sickle/Scythe)
        _createWeaponConfig("Basic Sickle", Rarity.COMMON, 108, 50);
        _createWeaponConfig("Steel Sickle", Rarity.RARE, 138, 30);
        _createWeaponConfig("Epic Scythe", Rarity.EPIC, 168, 15);
        _createWeaponConfig("Legendary Scythe", Rarity.LEGENDARY, 208, 5);

        // 初始化武器箱（按武器类型分类）
        // 刀箱子 - 包含4个等级的刀
        uint256[] memory knifeIds = new uint256[](4);
        knifeIds[0] = 1;  // Starter Knife (COMMON)
        knifeIds[1] = 2;  // Sharp Knife (RARE)
        knifeIds[2] = 3;  // Epic Knife (EPIC)
        knifeIds[3] = 4;  // Legendary Knife (LEGENDARY)
        createCase("Knife Case", 0 ether, 50, knifeIds);

        // 剑箱子 - 包含4个等级的剑
        uint256[] memory swordIds = new uint256[](4);
        swordIds[0] = 5;  // Basic Sword (COMMON)
        swordIds[1] = 6;  // Golden Blade (RARE)
        swordIds[2] = 7;  // Epic Sword (EPIC)
        swordIds[3] = 8;  // Legendary Blade (LEGENDARY)
        createCase("Sword Case", 0 ether, 50, swordIds);

        // 斧头箱子 - 包含4个等级的斧头
        uint256[] memory axeIds = new uint256[](4);
        axeIds[0] = 9;   // Basic Axe (COMMON)
        axeIds[1] = 10;  // Battle Axe (RARE)
        axeIds[2] = 11;  // Epic Axe (EPIC)
        axeIds[3] = 12;  // Legendary Axe (LEGENDARY)
        createCase("Axe Case", 0 ether, 50, axeIds);

        // 镰刀箱子 - 包含4个等级的镰刀
        uint256[] memory sickleIds = new uint256[](4);
        sickleIds[0] = 13;  // Basic Sickle (COMMON)
        sickleIds[1] = 14;  // Steel Sickle (RARE)
        sickleIds[2] = 15;  // Epic Scythe (EPIC)
        sickleIds[3] = 16;  // Legendary Scythe (LEGENDARY)
        createCase("Sickle Case", 0 ether, 50, sickleIds);
    }

    // 创建武器配置
    function _createWeaponConfig(string memory name, Rarity rarity, uint256 baseDamageMultiplier, uint256 weight) internal {
        weaponConfigs[nextWeaponConfigId] = WeaponConfig({
            name: name,
            rarity: rarity,
            baseDamageMultiplier: baseDamageMultiplier,
            weight: weight
        });
        nextWeaponConfigId++;
    }

    // 创建武器箱（仅管理员）
    function createCase(string memory name, uint256 price, uint256 coinPrice, uint256[] memory weaponConfigIds) public onlyOwner {
        cases[nextCaseId] = Case({
            id: nextCaseId,
            name: name,
            price: price,
            coinPrice: coinPrice,
            weaponConfigIds: weaponConfigIds
        });

        emit CaseCreated(nextCaseId, name, price, coinPrice);
        nextCaseId++;
    }

    // 获取武器箱总数
    function getNextCaseId() public view returns (uint256) {
        return nextCaseId;
    }

    // 根据权重随机选择武器配置
    function _selectRandomWeaponConfig(uint256[] memory configIds) internal view returns (WeaponConfig memory) {
        uint256 totalWeight = 0;

        // 计算总权重
        for (uint256 i = 0; i < configIds.length; i++) {
            totalWeight += weaponConfigs[configIds[i]].weight;
        }

        // 生成随机数
        uint256 rand = uint256(keccak256(abi.encodePacked(block.timestamp, block.prevrandao, msg.sender))) % totalWeight;

        // 根据权重选择武器配置
        uint256 cumulativeWeight = 0;
        for (uint256 i = 0; i < configIds.length; i++) {
            cumulativeWeight += weaponConfigs[configIds[i]].weight;
            if (rand < cumulativeWeight) {
                return weaponConfigs[configIds[i]];
            }
        }

        // 防止意外情况，返回第一个配置
        return weaponConfigs[configIds[0]];
    }

    // 购买箱子（使用金币）
    function purchaseCase(uint256 caseId, uint256 amount) public {
        require(caseId > 0 && caseId < nextCaseId, "Invalid case ID");
        require(amount > 0, "Amount must be positive");

        Case storage caseInfo = cases[caseId];
        uint256 totalCost = caseInfo.coinPrice * amount;

        require(coins[msg.sender] >= totalCost, "Insufficient coins");

        // 扣除金币
        coins[msg.sender] -= totalCost;

        // 添加到库存
        userCaseInventory[msg.sender][caseId] += amount;

        emit CasePurchased(msg.sender, caseId, amount);
    }

    // 从库存中开启武器箱
    function openCaseFromInventory(uint256 caseId) public {
        require(caseId > 0 && caseId < nextCaseId, "Invalid case ID");
        require(userCaseInventory[msg.sender][caseId] > 0, "No cases in inventory");

        // 消耗一个箱子
        userCaseInventory[msg.sender][caseId] -= 1;

        // 获取武器箱信息
        Case storage caseInfo = cases[caseId];

        // 随机选择武器配置
        WeaponConfig memory selectedConfig = _selectRandomWeaponConfig(caseInfo.weaponConfigIds);

        // 生成随机磨损度并映射到等级
        uint256 wear = _generateRandomWear();
        Condition randomCondition = _wearToCondition(wear);

        // 铸造新武器
        uint256 weaponId = _mintWeapon(msg.sender, selectedConfig.name, selectedConfig.rarity, selectedConfig.baseDamageMultiplier, wear, randomCondition);

        // 触发事件
        emit CaseOpened(msg.sender, caseId, weaponId, selectedConfig.rarity, randomCondition, wear);
    }

    // 使用ETH开启武器箱（直接开箱，不进库存）
    function openCaseWithETH(uint256 caseId) public payable {
        // 验证武器箱是否存在
        require(caseId > 0 && caseId < nextCaseId, "Invalid case ID");

        // 获取武器箱信息
        Case storage caseInfo = cases[caseId];

        // 验证支付金额
        require(msg.value >= caseInfo.price, "Insufficient ETH");

        // 随机选择武器配置
        WeaponConfig memory selectedConfig = _selectRandomWeaponConfig(caseInfo.weaponConfigIds);

        // 生成随机磨损度（10位精度）并映射到等级
        uint256 wear = _generateRandomWear();
        Condition randomCondition = _wearToCondition(wear);

        // 铸造新武器（携带 wear）
        uint256 weaponId = _mintWeapon(msg.sender, selectedConfig.name, selectedConfig.rarity, selectedConfig.baseDamageMultiplier, wear, randomCondition);

        // 发送多余的ETH退款
        if (msg.value > caseInfo.price) {
            payable(msg.sender).transfer(msg.value - caseInfo.price);
        }

        // 触发事件（包含 wear）
        emit CaseOpened(msg.sender, caseId, weaponId, selectedConfig.rarity, randomCondition, wear);
    }

    // 使用游戏币开启武器箱
    function openCaseWithCoins(uint256 caseId) public {
        // 验证武器箱是否存在
        require(caseId > 0 && caseId < nextCaseId, "Invalid case ID");

        // 获取武器箱信息
        Case storage caseInfo = cases[caseId];

        // 验证游戏币余额
        require(coins[msg.sender] >= caseInfo.coinPrice, "Insufficient coins");

        // 扣除游戏币
        coins[msg.sender] -= caseInfo.coinPrice;

        // 随机选择武器配置
        WeaponConfig memory selectedConfig = _selectRandomWeaponConfig(caseInfo.weaponConfigIds);

        // 生成随机磨损度（10位精度）并映射到等级
        uint256 wear = _generateRandomWear();
        Condition randomCondition = _wearToCondition(wear);

        // 铸造新武器（携带 wear）
        uint256 weaponId = _mintWeapon(msg.sender, selectedConfig.name, selectedConfig.rarity, selectedConfig.baseDamageMultiplier, wear, randomCondition);

        // 触发事件（包含 wear）
        emit CaseOpened(msg.sender, caseId, weaponId, selectedConfig.rarity, randomCondition, wear);
    }

    // 管理员可以提取合约中的ETH
    function withdrawETH() public onlyOwner {
        payable(owner).transfer(address(this).balance);
    }

    // 生成 0 .. 10**10-1 的随机 wear（表示 0.0000000000 .. 0.9999999999）
    function _generateRandomWear() internal returns (uint256) {
        uint256 val = uint256(keccak256(abi.encodePacked(
            block.timestamp,
            block.prevrandao,
            block.difficulty,
            msg.sender,
            address(this),
            nonce
        )));
        nonce++;
        return val % (10**10);
    }

    // 根据 wear 映射到 Condition（与前端的阈值一致）
    function _wearToCondition(uint256 wear) internal pure returns (Condition) {
        uint256 t1 = (10**10 * 5) / 100;   // 0.05
        uint256 t2 = (10**10 * 15) / 100;  // 0.15
        uint256 t3 = (10**10 * 30) / 100;  // 0.30
        uint256 t4 = (10**10 * 50) / 100;  // 0.50
        uint256 t5 = (10**10 * 75) / 100;  // 0.75
        if (wear < t1) return Condition.S;
        if (wear < t2) return Condition.A;
        if (wear < t3) return Condition.B;
        if (wear < t4) return Condition.C;
        if (wear < t5) return Condition.D;
        return Condition.E;
    }

    function mintWeapon(address to, string memory name, Rarity rarity, uint256 damageMultiplier) public onlyOwner {
        // 管理员铸造时也生成随机 wear并映射等级
        uint256 wear = _generateRandomWear();
        Condition condition = _wearToCondition(wear);
        _mintWeapon(to, name, rarity, damageMultiplier, wear, condition);
    }

    function _mintWeapon(address to, string memory name, Rarity rarity, uint256 damageMultiplier, uint256 wear, Condition condition) internal returns (uint256) {
        uint256 newWeaponId = nextWeaponId;
        nextWeaponId++;

        weapons[newWeaponId] = Weapon({
            id: newWeaponId,
            name: name,
            rarity: rarity,
            damageMultiplier: damageMultiplier,
            owner: to,
            price: 0,
            forSale: false,
            wear: wear,
            condition: condition
        });

        userWeapons[to].push(newWeaponId);
        _balances[to]++;  // ERC721: 增加余额

        emit WeaponMinted(to, newWeaponId, rarity, condition, wear);
        emit Transfer(address(0), to, newWeaponId);  // ERC721: 铸造事件

        return newWeaponId;
    }

    function purchaseWeapon(uint256 weaponId) public payable {
        Weapon storage weapon = weapons[weaponId];
        require(weapon.forSale, "Weapon not for sale");
        require(msg.value >= weapon.price, "Insufficient funds");
        require(weapon.owner != msg.sender, "Cannot buy your own weapon");

        address previousOwner = weapon.owner;
        uint256 purchasePrice = weapon.price;

        // 更新 ERC721 余额
        _balances[previousOwner]--;
        _balances[msg.sender]++;

        // 转移所有权
        weapon.owner = msg.sender;
        weapon.forSale = false;
        weapon.price = 0;

        // 更新用户武器列表
        _removeWeaponFromUser(previousOwner, weaponId);
        userWeapons[msg.sender].push(weaponId);

        // 转账给原所有者
        payable(previousOwner).transfer(purchasePrice);

        emit WeaponSold(previousOwner, msg.sender, weaponId);
        emit Transfer(previousOwner, msg.sender, weaponId);  // ERC721 事件
    }

    function listWeaponForSale(uint256 weaponId, uint256 price) public {
        Weapon storage weapon = weapons[weaponId];
        require(weapon.owner == msg.sender, "Not owner");
        require(price > 0, "Invalid price");

        weapon.forSale = true;
        weapon.price = price;

        emit WeaponListed(weaponId, price);
    }


    function recordWeedCut(uint256 points) public {
        // 如果是新玩家，添加到玩家列表
        if (!hasPlayed[msg.sender]) {
            players.push(msg.sender);
            hasPlayed[msg.sender] = true;
        }

        scores[msg.sender] += points;
        uint256 coinsEarned = points / 5;
        coins[msg.sender] += coinsEarned;

        emit WeedCut(msg.sender, points, coinsEarned);
    }

    // 设置玩家名称
    function setPlayerName(string memory name) public {
        playerNames[msg.sender] = name;
        if (!hasPlayed[msg.sender]) {
            players.push(msg.sender);
            hasPlayed[msg.sender] = true;
        }
        emit PlayerNameSet(msg.sender, name);
    }

    // 获取排行榜（返回前N名玩家）
    function getLeaderboard(uint256 count) public view returns (
        address[] memory addresses,
        string[] memory names,
        uint256[] memory playerScores,
        uint256[] memory ranks
    ) {
        uint256 totalPlayers = players.length;
        uint256 returnCount = count > totalPlayers ? totalPlayers : count;

        // 创建临时数组用于排序
        address[] memory tempAddresses = new address[](totalPlayers);
        uint256[] memory tempScores = new uint256[](totalPlayers);

        // 复制数据
        for (uint256 i = 0; i < totalPlayers; i++) {
            tempAddresses[i] = players[i];
            tempScores[i] = scores[players[i]];
        }

        // 简单的冒泡排序（降序）
        for (uint256 i = 0; i < totalPlayers; i++) {
            for (uint256 j = i + 1; j < totalPlayers; j++) {
                if (tempScores[j] > tempScores[i]) {
                    // 交换分数
                    uint256 tempScore = tempScores[i];
                    tempScores[i] = tempScores[j];
                    tempScores[j] = tempScore;
                    // 交换地址
                    address tempAddr = tempAddresses[i];
                    tempAddresses[i] = tempAddresses[j];
                    tempAddresses[j] = tempAddr;
                }
            }
        }

        // 准备返回数据
        addresses = new address[](returnCount);
        names = new string[](returnCount);
        playerScores = new uint256[](returnCount);
        ranks = new uint256[](returnCount);

        for (uint256 i = 0; i < returnCount; i++) {
            addresses[i] = tempAddresses[i];
            names[i] = playerNames[tempAddresses[i]];
            playerScores[i] = tempScores[i];
            ranks[i] = i + 1;
        }

        return (addresses, names, playerScores, ranks);
    }

    // 获取玩家排名
    function getPlayerRank(address player) public view returns (uint256 rank, uint256 totalPlayers) {
        totalPlayers = players.length;
        uint256 playerScore = scores[player];
        rank = 1;

        for (uint256 i = 0; i < totalPlayers; i++) {
            if (scores[players[i]] > playerScore) {
                rank++;
            }
        }

        return (rank, totalPlayers);
    }

    function getUserWeapons(address user) public view returns (uint256[] memory) {
        return userWeapons[user];
    }

    function getWeaponDetails(uint256 weaponId) public view returns (
        uint256 id,
        string memory name,
        Rarity rarity,
        uint256 damageMultiplier,
        address weaponOwner,
        uint256 price,
        bool forSale,
        uint256 wear,
        Condition condition
    ) {
        Weapon memory weapon = weapons[weaponId];
        require(weapon.id != 0, "Weapon does not exist");
        return (
            weapon.id,
            weapon.name,
            weapon.rarity,
            weapon.damageMultiplier,
            weapon.owner,
            weapon.price,
            weapon.forSale,
            weapon.wear,
            weapon.condition
        );
    }

    // 获取武器箱的详细信息
    function getCaseDetails(uint256 caseId) public view returns (
        string memory name,
        uint256 price,
        uint256 coinPrice
    ) {
        require(caseId > 0 && caseId < nextCaseId, "Invalid case ID");

        Case storage caseInfo = cases[caseId];
        return (
            caseInfo.name,
            caseInfo.price,
            caseInfo.coinPrice
        );
    }

    // 获取武器箱中包含的武器配置数量
    function getCaseWeaponConfigCount(uint256 caseId) public view returns (uint256) {
        require(caseId > 0 && caseId < nextCaseId, "Invalid case ID");
        return cases[caseId].weaponConfigIds.length;
    }

    // 获取武器箱中的第i个武器配置ID
    function getCaseWeaponConfigIdAt(uint256 caseId, uint256 index) public view returns (uint256) {
        require(caseId > 0 && caseId < nextCaseId, "Invalid case ID");
        require(index < cases[caseId].weaponConfigIds.length, "Index out of bounds");
        return cases[caseId].weaponConfigIds[index];
    }

    // 获取用户武器数量
    function getUserWeaponCount(address user) public view returns (uint256) {
        return userWeapons[user].length;
    }

    // 获取用户的第i个武器ID
    function getUserWeaponIdAt(address user, uint256 index) public view returns (uint256) {
        require(index < userWeapons[user].length, "Index out of bounds");
        return userWeapons[user][index];
    }

    function getPlayerStats(address player) public view returns (uint256 score, uint256 coinBalance) {
        return (scores[player], coins[player]);
    }

    // 获取用户的箱子库存
    function getUserCaseInventory(address user, uint256 caseId) public view returns (uint256) {
        return userCaseInventory[user][caseId];
    }

    // 获取用户所有箱子的库存（返回所有箱子ID和对应数量）
    function getAllUserCaseInventory(address user) public view returns (uint256[] memory caseIds, uint256[] memory amounts) {
        uint256 totalCases = nextCaseId - 1;

        // 先计算有多少个箱子有库存
        uint256 count = 0;
        for (uint256 i = 1; i <= totalCases; i++) {
            if (userCaseInventory[user][i] > 0) {
                count++;
            }
        }

        // 创建数组
        caseIds = new uint256[](count);
        amounts = new uint256[](count);

        // 填充数组
        uint256 index = 0;
        for (uint256 i = 1; i <= totalCases; i++) {
            if (userCaseInventory[user][i] > 0) {
                caseIds[index] = i;
                amounts[index] = userCaseInventory[user][i];
                index++;
            }
        }

        return (caseIds, amounts);
    }

    // 新增: 查询当前已铸造武器的下一个ID（总数量+1）
    function getNextWeaponId() public view returns (uint256) {
        return nextWeaponId;
    }

    // 新增: 返回当前所有在售武器列表
    function getWeaponsForSale() public view returns (Weapon[] memory) {
        uint256 total = nextWeaponId - 1;
        uint256 count = 0;
        for (uint256 i = 1; i <= total; i++) {
            if (weapons[i].forSale) {
                count++;
            }
        }
        Weapon[] memory saleList = new Weapon[](count);
        uint256 idx = 0;
        for (uint256 i = 1; i <= total; i++) {
            if (weapons[i].forSale) {
                saleList[idx] = weapons[i];
                idx++;
            }
        }
        return saleList;
    }

    function _removeWeaponFromUser(address user, uint256 weaponId) internal {
        uint256[] storage weaponsList = userWeapons[user];
        for (uint256 i = 0; i < weaponsList.length; i++) {
            if (weaponsList[i] == weaponId) {
                weaponsList[i] = weaponsList[weaponsList.length - 1];
                weaponsList.pop();
                break;
            }
        }
    }

    // ==================== P2P 交易报价系统 ====================

    // 交易报价结构
    struct TradeOffer {
        uint256 offerId;
        uint256 weaponId;
        address seller;       // 发起者（武器所有者）
        address buyer;        // 接受者（指定买家，address(0) 表示公开）
        uint256 price;        // 报价（Wei）
        bool active;          // 是否有效
        uint256 createdAt;    // 创建时间
    }

    mapping(uint256 => TradeOffer) public tradeOffers;
    uint256 private nextOfferId = 1;

    // 用户的活跃报价列表：seller => offerIds[]
    mapping(address => uint256[]) public userOffers;

    // 用户收到的报价列表：buyer => offerIds[]
    mapping(address => uint256[]) public userReceivedOffers;

    event TradeOfferCreated(uint256 offerId, uint256 weaponId, address indexed seller, address indexed buyer, uint256 price);
    event TradeOfferAccepted(uint256 offerId, uint256 weaponId, address indexed seller, address indexed buyer, uint256 price);
    event TradeOfferCancelled(uint256 offerId, address indexed seller);

    /**
     * @dev 创建交易报价（发起者）
     * @param weaponId 武器ID
     * @param buyer 指定买家地址（address(0) 表示公开给所有人）
     * @param price 报价（Wei）
     */
    function createTradeOffer(uint256 weaponId, address buyer, uint256 price) public {
        Weapon storage weapon = weapons[weaponId];
        require(weapon.owner == msg.sender, "Not weapon owner");
        require(!weapon.forSale, "Weapon already listed for sale");
        require(price > 0, "Price must be greater than 0");

        uint256 offerId = nextOfferId++;

        tradeOffers[offerId] = TradeOffer({
            offerId: offerId,
            weaponId: weaponId,
            seller: msg.sender,
            buyer: buyer,
            price: price,
            active: true,
            createdAt: block.timestamp
        });

        // 添加到发起者的报价列表
        userOffers[msg.sender].push(offerId);

        // 如果指定了买家，添加到买家的接收列表
        if (buyer != address(0)) {
            userReceivedOffers[buyer].push(offerId);
        }

        emit TradeOfferCreated(offerId, weaponId, msg.sender, buyer, price);
    }

    /**
     * @dev 接受交易报价（接受者支付 ETH）
     * @param offerId 报价ID
     */
    function acceptTradeOffer(uint256 offerId) public payable {
        TradeOffer storage offer = tradeOffers[offerId];

        require(offer.active, "Offer not active");
        require(offer.buyer == address(0) || offer.buyer == msg.sender, "Not designated buyer");
        require(msg.value >= offer.price, "Insufficient payment");

        Weapon storage weapon = weapons[offer.weaponId];
        require(weapon.owner == offer.seller, "Seller no longer owns weapon");

        address previousOwner = offer.seller;
        uint256 weaponId = offer.weaponId;
        uint256 paymentAmount = offer.price;

        // 更新 ERC721 余额
        _balances[previousOwner]--;
        _balances[msg.sender]++;

        // 转移武器所有权
        weapon.owner = msg.sender;
        weapon.forSale = false;
        weapon.price = 0;

        // 更新用户武器列表
        _removeWeaponFromUser(previousOwner, weaponId);
        userWeapons[msg.sender].push(weaponId);

        // 转账给卖家
        payable(previousOwner).transfer(paymentAmount);

        // 如果支付超过报价，退还差额
        if (msg.value > paymentAmount) {
            payable(msg.sender).transfer(msg.value - paymentAmount);
        }

        // 标记报价为已完成（不活跃）
        offer.active = false;

        emit TradeOfferAccepted(offerId, weaponId, previousOwner, msg.sender, paymentAmount);
        emit Transfer(previousOwner, msg.sender, weaponId);  // ERC721 事件
    }

    /**
     * @dev 取消交易报价（发起者）
     * @param offerId 报价ID
     */
    function cancelTradeOffer(uint256 offerId) public {
        TradeOffer storage offer = tradeOffers[offerId];

        require(offer.seller == msg.sender, "Not offer creator");
        require(offer.active, "Offer not active");

        offer.active = false;

        emit TradeOfferCancelled(offerId, msg.sender);
    }

    /**
     * @dev 获取用户发起的所有活跃报价
     * @param user 用户地址
     */
    function getUserActiveOffers(address user) public view returns (TradeOffer[] memory) {
        uint256[] storage offerIds = userOffers[user];
        uint256 activeCount = 0;

        // 计算活跃报价数量
        for (uint256 i = 0; i < offerIds.length; i++) {
            if (tradeOffers[offerIds[i]].active) {
                activeCount++;
            }
        }

        // 构建活跃报价数组
        TradeOffer[] memory activeOffers = new TradeOffer[](activeCount);
        uint256 index = 0;

        for (uint256 i = 0; i < offerIds.length; i++) {
            uint256 offerId = offerIds[i];
            if (tradeOffers[offerId].active) {
                activeOffers[index] = tradeOffers[offerId];
                index++;
            }
        }

        return activeOffers;
    }

    /**
     * @dev 获取用户收到的所有活跃报价
     * @param user 用户地址
     */
    function getUserReceivedActiveOffers(address user) public view returns (TradeOffer[] memory) {
        uint256[] storage offerIds = userReceivedOffers[user];
        uint256 activeCount = 0;

        // 计算活跃报价数量
        for (uint256 i = 0; i < offerIds.length; i++) {
            if (tradeOffers[offerIds[i]].active) {
                activeCount++;
            }
        }

        // 构建活跃报价数组
        TradeOffer[] memory activeOffers = new TradeOffer[](activeCount);
        uint256 index = 0;

        for (uint256 i = 0; i < offerIds.length; i++) {
            uint256 offerId = offerIds[i];
            if (tradeOffers[offerId].active) {
                activeOffers[index] = tradeOffers[offerId];
                index++;
            }
        }

        return activeOffers;
    }

    /**
     * @dev 获取报价详情
     * @param offerId 报价ID
     */
    function getTradeOffer(uint256 offerId) public view returns (TradeOffer memory) {
        return tradeOffers[offerId];
    }

    // 仅限所有者可以提取合约余额
    function withdraw() public onlyOwner {
        payable(owner).transfer(address(this).balance);
    }

    // 接收以太币
    receive() external payable {}

    // ==================== ERC721 标准实现 ====================

    /**
     * @dev 返回某地址拥有的 NFT 数量
     */
    function balanceOf(address owner) external view override returns (uint256) {
        require(owner != address(0), "ERC721: balance query for the zero address");
        return _balances[owner];
    }

    /**
     * @dev 返回某个 tokenId 的所有者
     */
    function ownerOf(uint256 tokenId) external view override returns (address) {
        address tokenOwner = weapons[tokenId].owner;
        require(tokenOwner != address(0), "ERC721: owner query for nonexistent token");
        return tokenOwner;
    }

    /**
     * @dev 转移 NFT（必须是所有者或被授权者）
     */
    function transferFrom(address from, address to, uint256 tokenId) external override {
        require(_isApprovedOrOwner(msg.sender, tokenId), "ERC721: transfer caller is not owner nor approved");
        require(weapons[tokenId].owner == from, "ERC721: transfer from incorrect owner");
        require(to != address(0), "ERC721: transfer to the zero address");
        require(!weapons[tokenId].forSale, "Cannot transfer weapon listed for sale");

        // 清除授权
        _approve(address(0), tokenId);

        // 更新余额
        _balances[from]--;
        _balances[to]++;

        // 更新武器所有者
        weapons[tokenId].owner = to;

        // 更新用户武器列表
        _removeWeaponFromUser(from, tokenId);
        userWeapons[to].push(tokenId);

        emit Transfer(from, to, tokenId);
    }

    /**
     * @dev 授权某地址可以操作某个 NFT
     */
    function approve(address to, uint256 tokenId) external override {
        address tokenOwner = weapons[tokenId].owner;
        require(to != tokenOwner, "ERC721: approval to current owner");
        require(msg.sender == tokenOwner, "ERC721: approve caller is not owner");

        _approve(to, tokenId);
    }

    /**
     * @dev 获取某个 NFT 的被授权地址
     */
    function getApproved(uint256 tokenId) external view override returns (address) {
        require(weapons[tokenId].owner != address(0), "ERC721: approved query for nonexistent token");
        return _tokenApprovals[tokenId];
    }

    /**
     * @dev 内部授权函数
     */
    function _approve(address to, uint256 tokenId) internal {
        _tokenApprovals[tokenId] = to;
        emit Approval(weapons[tokenId].owner, to, tokenId);
    }

    /**
     * @dev 检查某地址是否有权操作某个 NFT
     */
    function _isApprovedOrOwner(address spender, uint256 tokenId) internal view returns (bool) {
        address tokenOwner = weapons[tokenId].owner;
        require(tokenOwner != address(0), "ERC721: operator query for nonexistent token");
        return (spender == tokenOwner || _tokenApprovals[tokenId] == spender);
    }

    /**
     * @dev 安全转移（带数据回调）- 简化版本
     */
    function safeTransferFrom(address from, address to, uint256 tokenId) external {
        require(_isApprovedOrOwner(msg.sender, tokenId), "ERC721: transfer caller is not owner nor approved");
        require(weapons[tokenId].owner == from, "ERC721: transfer from incorrect owner");
        require(to != address(0), "ERC721: transfer to the zero address");
        require(!weapons[tokenId].forSale, "Cannot transfer weapon listed for sale");

        // 清除授权
        _approve(address(0), tokenId);

        // 更新余额
        _balances[from]--;
        _balances[to]++;

        // 更新武器所有者
        weapons[tokenId].owner = to;

        // 更新用户武器列表
        _removeWeaponFromUser(from, tokenId);
        userWeapons[to].push(tokenId);

        emit Transfer(from, to, tokenId);
    }

    /**
     * @dev 销毁 NFT（仅所有者可以销毁自己的武器）
     */
    function burnWeapon(uint256 tokenId) external {
        require(weapons[tokenId].owner == msg.sender, "Only owner can burn weapon");
        require(!weapons[tokenId].forSale, "Cannot burn weapon listed for sale");

        address tokenOwner = weapons[tokenId].owner;

        // 清除授权
        _approve(address(0), tokenId);

        // 更新余额
        _balances[tokenOwner]--;

        // 从用户武器列表中移除
        _removeWeaponFromUser(tokenOwner, tokenId);

        // 删除武器数据
        delete weapons[tokenId];

        emit Transfer(tokenOwner, address(0), tokenId);
    }
}
