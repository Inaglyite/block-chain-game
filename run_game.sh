#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

NODE_URL="http://127.0.0.1:8545"
NODE_LOG="hardhat-node.log"
NODE_PID_FILE=".hardhat-node.pid"
NODE_STARTED=0

rpc_ping() {
  curl --silent --fail \
    -H 'Content-Type: application/json' \
    -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
    "$NODE_URL" >/dev/null 2>&1
}

start_node() {
  echo "[1/3] 启动 Hardhat 节点..."
  nohup npx hardhat node --hostname 127.0.0.1 --port 8545 >"$NODE_LOG" 2>&1 &
  NODE_PID=$!
  echo "$NODE_PID" > "$NODE_PID_FILE"
  NODE_STARTED=1
  for _ in {1..30}; do
    if rpc_ping; then
      echo "Hardhat 节点已启动 (pid=$NODE_PID)"
      return
    fi
    sleep 0.5
  done
  echo "❌ Hardhat 节点启动超时 (查看 $NODE_LOG)" >&2
  exit 1
}

cleanup() {
  if [[ $NODE_STARTED -eq 1 && -f "$NODE_PID_FILE" ]]; then
    PID=$(cat "$NODE_PID_FILE" || true)
    if [[ -n "${PID:-}" ]] && kill -0 "$PID" >/dev/null 2>&1; then
      echo "正在停止 Hardhat 节点 (pid=$PID)"
      kill "$PID" >/dev/null 2>&1 || true
    fi
    rm -f "$NODE_PID_FILE"
  fi
}
trap cleanup EXIT

if rpc_ping; then
  echo "检测到已有 Hardhat 节点，跳过启动"
else
  start_node
fi

echo "[2/3] 部署合约..."
npx hardhat run scripts/deploy.ts --network localhost

enable_venv() {
  if [[ -d .venv ]]; then
    # shellcheck disable=SC1091
    source .venv/bin/activate
    return
  fi
  echo "创建 Python 虚拟环境 (.venv)"
  python3 -m venv .venv
  # shellcheck disable=SC1091
  source .venv/bin/activate
  python -m pip install --upgrade pip
  if [[ -f requirements.txt ]]; then
    pip install -r requirements.txt
  else
    pip install pygame web3 pytmx
  fi
}

echo "[3/3] 启动游戏..."
enable_venv
python game.py
