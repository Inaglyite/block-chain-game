#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

NODE_URL="http://127.0.0.1:8545"
NODE_LOG="hardhat-node.log"
NODE_PID_FILE=".hardhat-node.pid"
NODE_STARTED=0
MAX_TRIES=60   # 60 * 0.5s = 30s 等待，可按需增大
SLEEP_MS=0.5

rpc_ping() {
  curl --silent --fail \
    -H 'Content-Type: application/json' \
    -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
    "$NODE_URL" >/dev/null 2>&1
}

start_node() {
  echo "[1/3] 启动 Hardhat 节点..."
  if ! command -v npx >/dev/null 2>&1; then
    echo "❌ 未找到 npx，请先安装 Node/npm" >&2
    exit 1
  fi

  # 清理旧日志
  : > "$NODE_LOG"

  # 使用 --yes 避免 npx 交互提示
  nohup npx --yes hardhat node --hostname 127.0.0.1 --port 8545 >"$NODE_LOG" 2>&1 &
  NODE_PID=$!
  echo "$NODE_PID" > "$NODE_PID_FILE"
  NODE_STARTED=1

  for i in $(seq 1 $MAX_TRIES); do
    if rpc_ping; then
      echo "Hardhat 节点已启动 (pid=$NODE_PID)"
      return
    fi
    # 如果进程已经退出，提前失败并打印日志
    if ! kill -0 "$NODE_PID" >/dev/null 2>&1; then
      echo "❌ Hardhat 进程已退出，查看 $NODE_LOG"
      tail -n 200 "$NODE_LOG" >&2 || true
      exit 1
    fi
    sleep "$SLEEP_MS"
  done

  echo "❌ Hardhat 节点启动超时 (查看 $NODE_LOG)" >&2
  echo "---- $NODE_LOG (tail 200) ----" >&2
  tail -n 200 "$NODE_LOG" >&2 || true
  exit 1
}

cleanup() {
  if [[ ${NODE_STARTED:-0} -eq 1 && -f "$NODE_PID_FILE" ]]; then
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
npx --yes hardhat run scripts/deploy.ts --network localhost

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
python main.py


