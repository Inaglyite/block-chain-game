// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

contract WeedCutterNFT {
    struct Weapon {
        uint256 id;
        string name;
        Rarity rarity;
        uint256 damageMultiplier;
        address owner;
        uint256 price;
        bool forSale;
    }

    enum Rarity { COMMON, RARE, EPIC, LEGENDARY }

    mapping(uint256 => Weapon) public weapons;
    mapping(address => uint256[]) public userWeapons;
    mapping(address => uint256) public scores;
    mapping(address => uint256) public coins;

    uint256 private nextWeaponId = 1;
    address public owner;

    event WeaponMinted(address indexed to, uint256 weaponId, Rarity rarity);
    event WeaponSold(address indexed from, address indexed to, uint256 weaponId);
    event WeaponListed(uint256 weaponId, uint256 price);
    event WeedCut(address indexed player, uint256 score, uint256 coinsEarned);

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

    function _mintWeapon(address to, string memory name, Rarity rarity, uint256 damageMultiplier) internal {
        weapons[nextWeaponId] = Weapon({
            id: nextWeaponId,
            name: name,
            rarity: rarity,
            damageMultiplier: damageMultiplier,
            owner: to,
            price: 0,
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
            weapon.forSale
        );
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