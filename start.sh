#!/usr/bin/env bash
# 科研数据分析平台 - 一键启动脚本 (Linux / macOS)
# 用法: ./start.sh
# 停止: Ctrl+C (会自动清理所有后台进程)

set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$ROOT/logs"
PIDS=()

# --- 颜色输出 ---
info()  { echo -e "\033[36m[*] $1\033[0m"; }
ok()    { echo -e "\033[32m[+] $1\033[0m"; }
warn()  { echo -e "\033[33m[!] $1\033[0m"; }
err()   { echo -e "\033[31m[-] $1\033[0m"; }

# --- 清理函数 ---
cleanup() {
    echo ""
    info "正在停止后台服务..."
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    wait 2>/dev/null
    ok "所有服务已停止"
    exit 0
}
trap cleanup SIGINT SIGTERM

# --- 前置检查 ---
info "检查前置依赖..."
missing=()
command -v python3 >/dev/null 2>&1 || missing+=("Python (>=3.11)")
command -v Rscript >/dev/null 2>&1 || missing+=("R (>=4.x)")
command -v node >/dev/null 2>&1    || missing+=("Node.js (>=18)")

if [ ${#missing[@]} -gt 0 ]; then
    err "缺少以下依赖:"
    for m in "${missing[@]}"; do err "  - $m"; done
    exit 1
fi
ok "Python / R / Node.js 已就绪"

# --- Redis ---
if redis-cli ping >/dev/null 2>&1; then
    ok "Redis 已在运行"
else
    warn "Redis 未检测到"
    if command -v redis-server >/dev/null 2>&1; then
        info "启动 Redis..."
        redis-server --daemonize yes
        ok "Redis 已启动"
    elif command -v docker >/dev/null 2>&1; then
        info "通过 Docker 启动 Redis..."
        docker run -d -p 6379:6379 --name data-analysis-redis redis:latest >/dev/null 2>&1 || true
        sleep 2
        ok "Redis Docker 已启动"
    else
        err "无法启动 Redis, 请手动安装"
        exit 1
    fi
fi

# --- 日志目录 ---
mkdir -p "$LOG_DIR"

# --- Python 虚拟环境 ---
VENV="$ROOT/backend/.venv"
if [ ! -f "$VENV/bin/python" ]; then
    info "创建 Python 虚拟环境..."
    python3 -m venv "$VENV"
fi

info "安装 Python 依赖..."
"$VENV/bin/pip" install -e "$ROOT/backend[dev]" --quiet 2>/dev/null
ok "Python 依赖已就绪"

# --- R 包 ---
info "检查 R 包..."
Rscript -e "
pkgs <- c('plumber','jsonlite','car','agricolae','vegan')
missing <- pkgs[!pkgs %in% installed.packages()[,'Package']]
if(length(missing) > 0) {
  cat('安装:', paste(missing, collapse=', '), '\n')
  install.packages(missing, repos='https://cloud.r-project.org', quiet=TRUE)
}
" 2>/dev/null
ok "R 包已就绪"

# --- 前端依赖 ---
if [ ! -d "$ROOT/frontend/node_modules" ]; then
    info "安装前端依赖..."
    cd "$ROOT/frontend" && npm install --silent 2>/dev/null
    cd "$ROOT"
fi
ok "前端依赖已就绪"

# --- 启动服务 ---

# R Plumber
info "启动 R Plumber (端口 8787)..."
Rscript "$ROOT/backend/r_plumber/start.R" 8787 > "$LOG_DIR/r-plumber.log" 2>&1 &
PIDS+=($!)

sleep 3

# FastAPI
info "启动 FastAPI 后端 (端口 8000)..."
cd "$ROOT/backend"
"$VENV/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8000 > "$LOG_DIR/fastapi.log" 2>&1 &
PIDS+=($!)

# Celery Worker
info "启动 Celery Worker..."
"$VENV/bin/celery" -A app.workers.celery_worker worker -l info > "$LOG_DIR/celery.log" 2>&1 &
PIDS+=($!)
cd "$ROOT"

sleep 2

# --- 健康检查 ---
info "健康检查..."
curl -sf http://localhost:8787/health >/dev/null && ok "R Plumber: ok" || warn "R Plumber 未响应"
curl -sf http://localhost:8000/api/v1/health >/dev/null && ok "FastAPI: ok" || warn "FastAPI 未响应"

# --- 前端 ---
echo ""
echo -e "\033[32m=====================================\033[0m"
ok "所有后台服务已启动!"
echo "  R Plumber : http://localhost:8787"
echo "  FastAPI   : http://localhost:8000"
echo "  Celery    : 后台运行中"
echo "  日志目录  : $LOG_DIR"
echo -e "\033[32m=====================================\033[0m"
echo ""
info "启动前端开发服务器 (Ctrl+C 停止所有服务)..."
echo ""

cd "$ROOT/frontend"
npx vite --host
