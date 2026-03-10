# 科研数据分析平台 - 一键启动脚本 (Windows PowerShell)
# 用法: .\start.ps1
# 停止: Ctrl+C (会自动清理所有后台进程)

$ErrorActionPreference = "Continue"
$ROOT = $PSScriptRoot

# --- 颜色输出 ---
function Write-Status($msg) { Write-Host "[*] $msg" -ForegroundColor Cyan }
function Write-Ok($msg)     { Write-Host "[+] $msg" -ForegroundColor Green }
function Write-Warn($msg)   { Write-Host "[!] $msg" -ForegroundColor Yellow }
function Write-Err($msg)    { Write-Host "[-] $msg" -ForegroundColor Red }

# --- 前置检查 ---
Write-Status "检查前置依赖..."

$missing = @()
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { $missing += "Python (>=3.11)" }
if (-not (Get-Command Rscript -ErrorAction SilentlyContinue)) { $missing += "R (>=4.x)" }
if (-not (Get-Command node -ErrorAction SilentlyContinue))    { $missing += "Node.js (>=18)" }

if ($missing.Count -gt 0) {
    Write-Err "缺少以下依赖:"
    $missing | ForEach-Object { Write-Err "  - $_" }
    exit 1
}
Write-Ok "Python / R / Node.js 已就绪"

# --- Redis 检查 ---
$redisRunning = $false
try {
    $tcp = New-Object System.Net.Sockets.TcpClient
    $tcp.Connect("127.0.0.1", 6379)
    $tcp.Close()
    $redisRunning = $true
    Write-Ok "Redis 已在运行 (端口 6379)"
} catch {
    Write-Warn "Redis 未检测到 (端口 6379)"
    if (Get-Command redis-server -ErrorAction SilentlyContinue) {
        Write-Status "启动 Redis..."
        Start-Process -NoNewWindow -FilePath "redis-server" -RedirectStandardOutput "$ROOT\logs\redis.log" -RedirectStandardError "$ROOT\logs\redis-err.log"
        Start-Sleep -Seconds 2
        $redisRunning = $true
        Write-Ok "Redis 已启动"
    } else {
        Write-Warn "未找到 redis-server, 尝试 Docker..."
        if (Get-Command docker -ErrorAction SilentlyContinue) {
            docker run -d -p 6379:6379 --name data-analysis-redis redis:latest 2>$null
            Start-Sleep -Seconds 3
            $redisRunning = $true
            Write-Ok "Redis Docker 容器已启动"
        } else {
            Write-Err "无法启动 Redis, 请手动安装或启动 Redis"
            Write-Err "  方式1: 安装 Redis - https://github.com/tporadowski/redis/releases"
            Write-Err "  方式2: Docker - docker run -d -p 6379:6379 redis:latest"
            exit 1
        }
    }
}

# --- 创建日志目录 ---
$logDir = Join-Path $ROOT "logs"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }

# --- Python 虚拟环境 ---
$venvPath = Join-Path $ROOT "backend\.venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"
$venvPip = Join-Path $venvPath "Scripts\pip.exe"

if (-not (Test-Path $venvPython)) {
    Write-Status "创建 Python 虚拟环境..."
    python -m venv "$venvPath"
    Write-Ok "虚拟环境已创建"
}

Write-Status "安装 Python 依赖..."
& $venvPip install -e "$ROOT\backend[dev]" --quiet 2>$null
Write-Ok "Python 依赖已就绪"

# --- R 包检查 ---
Write-Status "检查 R 包..."
$rCheck = Rscript -e "pkgs <- c('plumber','jsonlite','car','agricolae','vegan'); missing <- pkgs[!pkgs %%in%% installed.packages()[,'Package']]; if(length(missing)>0){cat(paste(missing,collapse=',')); quit(status=1)}else{cat('ok')}" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Warn "安装缺失的 R 包: $rCheck"
    Rscript -e "install.packages(c('plumber','jsonlite','car','agricolae','vegan'), repos='https://cloud.r-project.org', quiet=TRUE)"
}
Write-Ok "R 包已就绪"

# --- 前端依赖 ---
$nodeModules = Join-Path $ROOT "frontend\node_modules"
if (-not (Test-Path $nodeModules)) {
    Write-Status "安装前端依赖..."
    Push-Location "$ROOT\frontend"
    npm install --silent 2>$null
    Pop-Location
}
Write-Ok "前端依赖已就绪"

# --- 启动服务 ---
$jobs = @()

# R Plumber
Write-Status "启动 R Plumber (端口 8787)..."
$jobs += Start-Process -NoNewWindow -PassThru -FilePath "Rscript" `
    -ArgumentList "$ROOT\backend\r_plumber\start.R", "8787" `
    -RedirectStandardOutput "$logDir\r-plumber.log" `
    -RedirectStandardError "$logDir\r-plumber-err.log"

Start-Sleep -Seconds 3

# FastAPI
Write-Status "启动 FastAPI 后端 (端口 8000)..."
$jobs += Start-Process -NoNewWindow -PassThru -FilePath $venvPython `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000" `
    -WorkingDirectory "$ROOT\backend" `
    -RedirectStandardOutput "$logDir\fastapi.log" `
    -RedirectStandardError "$logDir\fastapi-err.log"

# Celery Worker
Write-Status "启动 Celery Worker..."
$celeryExe = Join-Path $venvPath "Scripts\celery.exe"
$jobs += Start-Process -NoNewWindow -PassThru -FilePath $celeryExe `
    -ArgumentList "-A", "app.workers.celery_worker", "worker", "-l", "info", "-P", "solo" `
    -WorkingDirectory "$ROOT\backend" `
    -RedirectStandardOutput "$logDir\celery.log" `
    -RedirectStandardError "$logDir\celery-err.log"

Start-Sleep -Seconds 2

# --- 健康检查 ---
Write-Status "健康检查..."

try {
    $r = Invoke-RestMethod -Uri "http://localhost:8787/health" -TimeoutSec 5
    Write-Ok "R Plumber: $($r.status)"
} catch {
    Write-Warn "R Plumber 未响应 (可能仍在启动中)"
}

try {
    $r = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/health" -TimeoutSec 5
    Write-Ok "FastAPI: OK"
} catch {
    Write-Warn "FastAPI 未响应 (可能仍在启动中)"
}

# --- 前端 (前台运行) ---
Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
Write-Ok "所有后台服务已启动!"
Write-Host "  R Plumber : http://localhost:8787"
Write-Host "  FastAPI   : http://localhost:8000"
Write-Host "  Celery    : 后台运行中"
Write-Host "  日志目录  : $logDir"
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""
Write-Status "启动前端开发服务器 (Ctrl+C 停止所有服务)..."
Write-Host ""

try {
    Push-Location "$ROOT\frontend"
    npm run dev
} finally {
    Pop-Location
    Write-Host ""
    Write-Status "正在停止后台服务..."
    foreach ($job in $jobs) {
        if (-not $job.HasExited) {
            Stop-Process -Id $job.Id -Force -ErrorAction SilentlyContinue
        }
    }
    # 清理 Docker Redis (如果是我们启动的)
    docker stop data-analysis-redis 2>$null | Out-Null
    docker rm data-analysis-redis 2>$null | Out-Null
    Write-Ok "所有服务已停止"
}
