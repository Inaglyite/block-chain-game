@echo off
setlocal enabledelayedexpansion
set ROOT_DIR=%~dp0
cd /d "%ROOT_DIR%"
set NODE_LOG=hardhat-node.log
set NODE_PID_FILE=.hardhat-node.pid
set NODE_STARTED=0

:CHECK_NODE
for /f "tokens=*" %%C in ('powershell -NoProfile -Command "try { Invoke-RestMethod -Uri http://127.0.0.1:8545 -Method Post -Body '{\"jsonrpc\":\"2.0\",\"method\":\"eth_blockNumber\",\"params\":[],\"id\":1}' -ContentType 'application/json' | Out-Null; exit 0 } catch { exit 1 }"') do set RET=%%C
if !errorlevel! == 0 goto NODE_READY

echo [1/3] 启动 Hardhat 节点...
start "hardhat-node" /MIN cmd /c "npx hardhat node --hostname 127.0.0.1 --port 8545 > %NODE_LOG% 2>&1"
set NODE_STARTED=1
timeout /t 5 >nul
:WAIT_NODE
for /f "tokens=*" %%C in ('powershell -NoProfile -Command "try { Invoke-RestMethod -Uri http://127.0.0.1:8545 -Method Post -Body '{\"jsonrpc\":\"2.0\",\"method\":\"eth_blockNumber\",\"params\":[],\"id\":1}' -ContentType 'application/json' | Out-Null; exit 0 } catch { exit 1 }"') do set RET=%%C
if !errorlevel! neq 0 (
    timeout /t 1 >nul
    goto WAIT_NODE
)

:NODE_READY
echo Hardhat 节点已运行

echo [2/3] 部署合约...
npx hardhat run scripts/deploy.ts --network localhost
if errorlevel 1 goto END

if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else (
    echo 创建 Python 虚拟环境 (.venv)
    python -m venv .venv
    call .venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    if exist requirements.txt (
        pip install -r requirements.txt
    ) else (
        pip install pygame web3
    )
)

echo [3/3] 启动游戏...
python game.py

:END
if %NODE_STARTED%==1 (
    for /f "tokens=*" %%P in ('powershell -NoProfile -Command "Get-Process -Name node -ErrorAction SilentlyContinue | Where-Object { $_.Path -like '*hardhat*' } | Select -ExpandProperty Id"') do taskkill /PID %%P /F >nul 2>&1
)
endlocal

