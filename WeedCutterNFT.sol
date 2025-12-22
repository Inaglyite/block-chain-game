// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

contract WeedCutterNFT {
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
    
    // 武器箱相关的映射
    mapping(uint256 => Case) public cases;
    mapping(uint256 => WeaponConfig) public weaponConfigs;
    uint256 private nextCaseId = 1;
    uint256 private nextWeaponConfigId = 1;

    uint256 private nextWeaponId = 1;
    address public owner;

    event WeaponMinted(address indexed to, uint256 weaponId, Rarity rarity, Condition condition, uint256 wear);
    event WeaponSold(address indexed from, address indexed to, uint256 weaponId);
    event WeaponListed(uint256 weaponId, uint256 price);
    event WeedCut(address indexed player, uint256 score, uint256 coinsEarned);
    event CaseOpened(address indexed player, uint256 caseId, uint256 weaponId, Rarity rarity, Condition condition, uint256 wear);
    event CaseCreated(uint256 caseId, string name, uint256 price, uint256 coinPrice);

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
        
        // 初始化武器配置
        _createWeaponConfig("Basic Weed Cutter", Rarity.COMMON, 100, 50);
        _createWeaponConfig("Steel Sickle", Rarity.COMMON, 110, 40);
        _createWeaponConfig("Golden Blade", Rarity.RARE, 130, 30);
        _createWeaponConfig("Diamond Cutter", Rarity.RARE, 150, 20);
        _createWeaponConfig("Legendary Scythe", Rarity.EPIC, 180, 10);
        _createWeaponConfig("Mythical Sickle", Rarity.LEGENDARY, 200, 5);
        
        // 初始化武器箱
        // 创建第一个武器箱
        uint256[] memory weaponIds1 = new uint256[](4);
        weaponIds1[0] = 1;  // Basic Weed Cutter
        weaponIds1[1] = 2;  // Steel Sickle
        weaponIds1[2] = 3;  // Golden Blade
        weaponIds1[3] = 4;  // Diamond Cutter
        createCase("Basic Case", 0.001 ether, 100, weaponIds1);
        
        // 创建高级武器箱
        uint256[] memory weaponIds2 = new uint256[](4);
        weaponIds2[0] = 3;  // Golden Blade
        weaponIds2[1] = 4;  // Diamond Cutter
        weaponIds2[2] = 5;  // Legendary Scythe
        weaponIds2[3] = 6;  // Mythical Sickle
        createCase("Premium Case", 0.005 ether, 500, weaponIds2);
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
    
    // 使用ETH开启武器箱
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
        emit WeaponMinted(to, newWeaponId, rarity, condition, wear);

        return newWeaponId;
    }

    function purchaseWeapon(uint256 weaponId) public payable {
        Weapon storage weapon = weapons[weaponId];
        require(weapon.forSale, "Weapon not for sale");
        require(msg.value >= weapon.price, "Insufficient funds");
        // 移除了禁止购买自己武器的限制

        address previousOwner = weapon.owner;
        uint256 purchasePrice = weapon.price;

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
        scores[msg.sender] += points;
        uint256 coinsEarned = points / 5;
        coins[msg.sender] += coinsEarned;

        emit WeedCut(msg.sender, points, coinsEarned);
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

    // 仅限所有者可以提取合约余额
    function withdraw() public onlyOwner {
        payable(owner).transfer(address(this).balance);
    }

    // 接收以太币
    receive() external payable {}
}