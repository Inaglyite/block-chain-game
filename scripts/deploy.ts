import { network, artifacts } from "hardhat";
import fs from "fs";
import { formatEther } from "viem";

async function main() {
  console.log("开始部署 WeedCutterNFT 合约...");

  // 连接当前网络（由 CLI --network 参数决定）
  const { viem } = await network.connect();
  const publicClient = await viem.getPublicClient();
  const [walletClient] = await viem.getWalletClients();
  const deployerAddress = walletClient.account.address;

  const balance = await publicClient.getBalance({ address: deployerAddress });
  console.log("部署者地址:", deployerAddress);
  console.log("部署者余额:", formatEther(balance), "ETH");

  // 部署合约（使用合约名称，Hardhat 会从 artifacts 中解析）
  const weedCutter = await viem.deployContract("WeedCutterNFT");
  console.log("✅ 合约部署成功");
  console.log("合约地址:", weedCutter.address);

  // 读取初始武器（合约构造函数里已铸造）
  const initialWeapons = await weedCutter.read.getUserWeapons([deployerAddress]);
  console.log("初始武器数量:", initialWeapons.length.toString());

  const rarityNames = ["COMMON", "RARE", "EPIC", "LEGENDARY"];
  for (let i = 0; i < initialWeapons.length; i++) {
    const weaponId = initialWeapons[i];
    const weaponDetails = await weedCutter.read.getWeaponDetails([weaponId]);
    // weaponDetails 返回元组 (id, name, rarity, damageMultiplier, owner, price, forSale)
    const [id, name, rarity, damageMultiplier] = weaponDetails;
    console.log(
      `武器 ${i + 1}: ${name} (稀有度: ${rarityNames[Number(rarity)]}, 伤害: ${damageMultiplier})`
    );
  }

  const chainId = await publicClient.getChainId();
  const contractInfo = {
    address: weedCutter.address,
    deployer: deployerAddress,
    network: network.name,
    chainId
  };
  fs.writeFileSync("contract-info.json", JSON.stringify(contractInfo, null, 2));
  console.log("合约信息已保存到 contract-info.json");

  // 导出 ABI 与字节码
  const artifact = await artifacts.readArtifact("WeedCutterNFT");
  const abiData = { abi: artifact.abi, bytecode: artifact.bytecode };
  fs.writeFileSync("WeedCutterNFT.json", JSON.stringify(abiData, null, 2));
  console.log("ABI 已导出到 WeedCutterNFT.json");
}

main().catch((e) => {
  console.error("部署失败:", e);
  process.exit(1);
});
