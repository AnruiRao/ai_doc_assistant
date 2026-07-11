#!/bin/bash
cd "$(dirname "$0")"

# 加载 .env（本地开发用，Docker 由 compose 传入）
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Docker 环境下不加 --reload
RELOAD_FLAG=""
if [ -z "${DOCKER:-}" ]; then
    RELOAD_FLAG="--reload"
fi

# 启动 FastAPI（后台）
echo "Starting FastAPI..."
.venv/bin/uvicorn api.main:app $RELOAD_FLAG --host 0.0.0.0 --port 8000 --app-dir src &
API_PID=$!

# 等待 FastAPI 就绪
echo "Waiting for FastAPI to be ready..."
for i in $(seq 1 30); do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "FastAPI ready"
        break
    fi
    sleep 1
done

# 退出时清理后台进程
cleanup() {
    echo ""
    echo "Shutting down FastAPI..."
    kill $API_PID 2>/dev/null
    wait $API_PID 2>/dev/null
    echo "Done"
}
trap cleanup EXIT

# 启动 Streamlit（前台）
echo "Starting Streamlit..."
exec .venv/bin/streamlit run src/ui/ui.py
