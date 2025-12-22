# File: run_game.bat
:: Windows bat 版本（基础）
@echo off
setlocal

set NODE_LOG=hardhat-node.log
set NODE_URL=http://127.0.0.1:8545

echo 启动 Hardhat 节点（后台）...
start "Hardhat" cmd /c "npx --yes hardhat node --hostname 127.0.0.1 --port 8545 >%NODE_LOG% 2>&1"

echo 等待节点启动...
powershell -Command ^
  "$url='%NODE_URL%'; for ($i=0; $i -lt 60; $i++) { try { $r=Invoke-RestMethod -Uri $url -Method Post -ContentType 'application/json' -Body '{\"jsonrpc\":\"2.0\",\"method\":\"eth_blockNumber\",\"params\":[],\"id\":1}'; Write-Host '节点已启动'; exit 0 } catch { Start-Sleep -Milliseconds 500 } } Write-Error 'Hardhat 节点启动超时'; exit 1"

if errorlevel 1 (
  echo 查看 %NODE_LOG%
  exit /b 1
)

echo 部署合约...
npx --yes hardhat run scripts/deploy.ts --network localhost

echo 启动游戏...
python main.py

endlocal