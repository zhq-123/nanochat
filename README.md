# nanochat

> AI 对话平台

## 技术栈

- **后端框架**: FastAPI
- **ORM**: SQLAlchemy 2.0 (异步)
- **数据库**: PostgreSQL + PGVector
- **缓存**: Redis
- **消息队列**: RabbitMQ
- **AI框架**: LangChain + LangGraph
- **对象存储**: MinIO

## 快速开始

### 环境要求

- Python 3.11+
- Docker & Docker Compose
- uv

### 安装步骤

```bash
# 安装依赖
uv sync

# 启动基础服务
docker compose up -d

# 启动开发服务器
uv run uvicorn app.main:app --reload
```

访问 API 文档: http://localhost:8000/docs

## 项目结构


```
nanochat/
├── app/                    # 应用代码
│   ├── api/               # API 路由
│   ├── core/              # 核心配置
│   ├── db/                # 数据库连接
│   ├── models/            # 数据模型
│   ├── schemas/           # Pydantic 模型
│   ├── services/          # 业务逻辑
│   ├── repositories/      # 数据访问
│   ├── middleware/        # 中间件
│   ├── utils/             # 工具函数
│   └── workers/           # 后台任务
├── tests/                  # 测试代码
├── docker/                # Docker 配置
└── docs/                  # 项目文档
```