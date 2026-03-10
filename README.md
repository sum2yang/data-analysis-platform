# 科研数据分析平台

面向农学、生态学、生物学的 Web 端统计分析平台。上传数据后即可完成描述性统计、差异分析、相关性分析、排序分析等全流程，并支持图表预览与导出。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 19 + TypeScript + Ant Design + ECharts |
| 后端 | FastAPI + SQLAlchemy + Celery |
| 统计引擎 | R Plumber (HTTP API) |
| 数据库 | SQLite |
| 任务队列 | Celery + Redis |
| 图表导出 | matplotlib (后端 PNG/PDF) + ECharts (前端交互) |

## 架构

```
                  +-----------+
                  | React SPA |  :5173
                  +-----+-----+
                        |
                  +-----v-----+
                  |  FastAPI   |  :8000
                  +-----+-----+
                        |
              +---------+---------+
              |                   |
        +-----v-----+     +------v------+
        |  Celery    |     |   SQLite    |
        |  Worker    |     |   (app.db)  |
        +-----+------+     +-------------+
              |
        +-----v-----+
        | R Plumber  |  :8787
        |  (16 端点)  |
        +------------+
```

## 快速开始

### 前置条件

- **Python** >= 3.11
- **R** >= 4.x (需安装 plumber, jsonlite, car, agricolae, vegan 包)
- **Node.js** >= 18
- **Redis** (本地运行或 Docker)

### 一键启动 (Windows PowerShell)

```powershell
.\start.ps1
```

### 一键启动 (Linux / macOS)

```bash
chmod +x start.sh
./start.sh
```

脚本会自动检查依赖、安装缺失的包、按顺序启动全部 5 个服务。

## 手动启动

如需单独启动各服务，按以下顺序执行:

### 1. Redis

```bash
# 本地安装
redis-server

# 或 Docker
docker run -d -p 6379:6379 redis:latest
```

### 2. R Plumber (端口 8787)

```bash
cd backend/r_plumber
Rscript start.R 8787
```

首次运行前安装 R 包:

```r
install.packages(c("plumber", "jsonlite", "car", "agricolae", "vegan"))
```

### 3. FastAPI 后端 (端口 8000)

```bash
cd backend

# 创建虚拟环境 (首次)
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 安装依赖
pip install -e ".[dev]"

# 启动
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Celery Worker

```bash
cd backend
celery -A app.workers.celery_worker worker -l info -P solo
```

> Windows 必须加 `-P solo`，Linux/macOS 可省略。

### 5. 前端 (端口 5173)

```bash
cd frontend
npm install
npm run dev
```

启动完成后打开 http://localhost:5173

## 环境变量

在 `backend/.env` 中配置 (均有默认值，开发环境可不配置):

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DEBUG` | `False` | 调试模式 |
| `DATABASE_URL` | `sqlite:///./data/app.db` | 数据库连接 |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 地址 |
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | Celery Broker |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/1` | Celery 结果存储 |
| `R_PLUMBER_BASE_URL` | `http://localhost:8787` | R Plumber 地址 |
| `JWT_SECRET_KEY` | `change-me-in-production` | JWT 签名密钥 (生产环境必须修改) |
| `UPLOAD_ROOT` | `./data/uploads` | 上传文件目录 |
| `ARTIFACT_ROOT` | `./data/artifacts` | 导出文件目录 |
| `MAX_UPLOAD_SIZE_MB` | `50` | 最大上传大小 (MB) |

## API 端点

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/auth/register` | 注册 |
| POST | `/api/v1/auth/login` | 登录 |
| POST | `/api/v1/auth/refresh` | 刷新 Token |

### 数据集

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/datasets/upload` | 上传 CSV/Excel |
| GET | `/api/v1/datasets` | 数据集列表 |
| GET | `/api/v1/datasets/{id}` | 数据集详情 |

### 统计分析 (统一派发)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/analyses/run` | 统一分析入口 |
| GET | `/api/v1/analysis-runs/{id}` | 查询运行状态 |
| GET | `/api/v1/analysis-runs/{id}/result` | 获取分析结果 |

支持的 `analysis_type`:

| 类型 | R 端点 | 说明 |
|------|--------|------|
| `descriptive` | `/descriptive` | 描述性统计 |
| `assumptions` | `/assumptions` | 正态性/方差齐性检验 |
| `t_test` | `/t-test` | t 检验 |
| `anova_one_way` | `/anova/one-way` | 单因素方差分析 |
| `anova_multi_way` | `/anova/multi-way` | 多因素方差分析 |
| `anova_welch` | `/anova/welch` | Welch 方差分析 |
| `kruskal_wallis` | `/nonparametric/kruskal-wallis` | Kruskal-Wallis 检验 |
| `mann_whitney` | `/nonparametric/mann-whitney` | Mann-Whitney U 检验 |
| `correlation` | `/correlation` | 相关性分析 |
| `regression_linear` | `/regression/linear` | 线性回归 |
| `regression_glm` | `/regression/glm` | 广义线性模型 |
| `pca` | `/ordination/pca` | 主成分分析 |
| `pcoa` | `/ordination/pcoa` | 主坐标分析 |
| `nmds` | `/ordination/nmds` | 非度量多维标度 |
| `rda` | `/ordination/rda` | 冗余分析 |
| `cca` | `/ordination/cca` | 典范对应分析 |

## 测试

```bash
# 后端单元测试 (mock R Plumber)
cd backend
pytest tests/ -v

# 后端 E2E 测试 (需启动 R Plumber)
pytest tests/ -v --live-r

# 前端测试
cd frontend
npm test
```

## 项目结构

```
.
├── backend/
│   ├── app/
│   │   ├── api/routes/        # API 路由
│   │   ├── core/              # 配置、安全、错误处理
│   │   ├── db/                # 数据库连接
│   │   ├── models/            # SQLAlchemy 模型
│   │   ├── repositories/      # 数据访问层
│   │   ├── schemas/           # Pydantic 验证模型
│   │   ├── services/          # 业务逻辑
│   │   ├── tasks/             # Celery 异步任务
│   │   └── workers/           # Celery Worker 配置
│   ├── r_plumber/             # R Plumber API
│   │   ├── R/                 # 分析处理函数
│   │   ├── plumber.R          # 路由定义
│   │   └── start.R            # 启动脚本
│   ├── tests/                 # pytest 测试
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── features/          # 分析页面 (按功能模块)
│   │   ├── components/        # 共享组件
│   │   ├── hooks/             # 自定义 Hooks
│   │   └── utils/             # 工具函数
│   └── package.json
├── start.ps1                  # Windows 一键启动
├── start.sh                   # Linux/macOS 一键启动
└── README.md
```
