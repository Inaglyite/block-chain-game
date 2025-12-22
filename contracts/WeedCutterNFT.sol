// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

contract WeedCutterNFT {
    struct Weapon {
        uint256 id;
        string name;
        Rarity rarity;
        uint256 damageMultiplier;
        address owner;
        uint256 price;        // ETH价格（wei）
        uint256 coinPrice;    // 金币价格
        bool forSale;
    }

    enum Rarity { COMMON, RARE, EPIC, LEGENDARY }

    mapping(uint256 => Weapon) public weapons;
    mapping(address => uint256[]) public userWeapons;
    mapping(address => uint256) public scores;
    mapping(address => uint256) public coins;

    // 排行榜相关
    address[] public players;  // 所有玩过游戏的玩家地址
    mapping(address => bool) public hasPlayed;  // 记录玩家是否玩过游戏
    mapping(address => string) public playerNames;  // 玩家自定义名称

    uint256 private nextWeaponId = 1;
    address public owner;
    // 以游戏内金币计价的铸造成本
    uint256 public mintCost = 20;

    event WeaponMinted(address indexed to, uint256 weaponId, Rarity rarity);
    event WeaponSold(address indexed from, address indexed to, uint256 weaponId);
    event WeaponListed(uint256 weaponId, uint256 price);
    event WeedCut(address indexed player, uint256 score, uint256 coinsEarned);
    event PlayerNameSet(address indexed player, string name);

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    constructor() {
        owner = msg.sender;
        // 初始化一些默认武器 - 使用英文名称
        _mintWeapon(msg.sender, "Starter Cutter", Rarity.COMMON, 100);
        _mintWeapon(msg.sender, "Sharp Sickle", Rarity.RARE, 120);
        _mintWeapon(msg.sender, "Epic Sword", Rarity.EPIC, 150);
    }

    function mintWeapon(address to, string memory name, Rarity rarity, uint256 damageMultiplier) public onlyOwner {
        _mintWeapon(to, name, rarity, damageMultiplier);
    }

    // 玩家使用游戏内金币自助铸造
    function mintWeaponWithCoins(string memory name, Rarity rarity, uint256 damageMultiplier) public {
        require(coins[msg.sender] >= mintCost, "Not enough coins");
        coins[msg.sender] -= mintCost;
        _mintWeapon(msg.sender, name, rarity, damageMultiplier);
    }

    function _mintWeapon(address to, string memory name, Rarity rarity, uint256 damageMultiplier) internal {
        weapons[nextWeaponId] = Weapon({
            id: nextWeaponId,
            name: name,
            rarity: rarity,
            damageMultiplier: damageMultiplier,
            owner: to,
            price: 0,
            coinPrice: 0,
            forSale: false
        });

        userWeapons[to].push(nextWeaponId);
        emit WeaponMinted(to, nextWeaponId, rarity);
        nextWeaponId++;
    }

    function purchaseWeapon(uint256 weaponId) public payable {
        Weapon storage weapon = weapons[weaponId];
        require(weapon.forSale, "Weapon not for sale");
        require(msg.value >= weapon.price, "Insufficient funds");
        require(weapon.owner != msg.sender, "Cannot buy your own weapon");

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

    // 新增：使用金币购买武器
    function purchaseWeaponWithCoins(uint256 weaponId, uint256 coinPrice) public {
        Weapon storage weapon = weapons[weaponId];
        require(weapon.forSale, "Weapon not for sale");
        require(weapon.owner != msg.sender, "Cannot buy your own weapon");
        require(coins[msg.sender] >= coinPrice, "Insufficient coins");

        address previousOwner = weapon.owner;

        // 扣除买家金币
        coins[msg.sender] -= coinPrice;
        // 给卖家金币
        coins[previousOwner] += coinPrice;

        // 转移所有权
        weapon.owner = msg.sender;
        weapon.forSale = false;
        weapon.price = 0;

        // 更新用户武器列表
        _removeWeaponFromUser(previousOwner, weaponId);
        userWeapons[msg.sender].push(weaponId);

        emit WeaponSold(previousOwner, msg.sender, weaponId);
    }

    function listWeaponForSale(uint256 weaponId, uint256 price) public {
        Weapon storage weapon = weapons[weaponId];
        require(weapon.owner == msg.sender, "Not owner");
        require(price > 0, "Invalid price");

        weapon.forSale = true;
        weapon.price = price;
        // 自动设置金币价格（1 ETH = 1000 金币的比例）
        weapon.coinPrice = price / 1e15;  // 将wei转换为合理的金币数量

        emit WeaponListed(weaponId, price);
    }

    // 新增：直接设置金币价格上架
    function listWeaponForSaleWithCoins(uint256 weaponId, uint256 coinPrice) public {
        Weapon storage weapon = weapons[weaponId];
        require(weapon.owner == msg.sender, "Not owner");
        require(coinPrice > 0, "Invalid coin price");

        weapon.forSale = true;
        weapon.coinPrice = coinPrice;
        weapon.price = 0;  // ETH价格设为0表示只用金币出售

        emit WeaponListed(weaponId, coinPrice);
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
        uint256 coinPrice,
        bool forSale
    ) {
        Weapon memory weapon = weapons[weaponId];
        return (
            weapon.id,
            weapon.name,
            weapon.rarity,
            weapon.damageMultiplier,
            weapon.owner,
            weapon.price,
            weapon.coinPrice,
            weapon.forSale
        );
    }

    function getPlayerStats(address player) public view returns (uint256 score, uint256 coinBalance) {
        return (scores[player], coins[player]);
    }

    // 管理员可调整铸造成本
    function setMintCost(uint256 newCost) public onlyOwner {
        mintCost = newCost;
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