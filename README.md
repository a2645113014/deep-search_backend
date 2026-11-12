# Deep Search Backend

基于多智能体协作的企业级深度搜索后端系统。主智能体负责协调多个子智能体，从**企业数据库**、**内部知识库**和**互联网**三个渠道获取信息，最终可生成 Markdown / PDF 文档。

## 功能特性

- **多源信息检索**：MySQL 数据库查询 + RAGFlow 知识库检索 + Tavily 网络搜索，按优先级自动选择或组合
- **智能体编排**：基于 `deepagents` 框架，主 Agent 动态调度三个子 Agent，支持多轮工具调用
- **文件上传与分析**：支持上传 PDF / Word / Excel / Markdown 等文件，Agent 可读取并纳入分析
- **文档生成**：根据检索结果自动生成 Markdown 报告，并可转换为 PDF
- **实时流式推送**：通过 WebSocket 实时推送 Agent 的思考过程、工具调用、最终结果

## 系统架构

```
用户请求 → FastAPI /api/task → 主 Agent (deepagents)
                                  │
                  ┌───────────────┼───────────────┐
                  ▼               ▼               ▼
          数据库查询助手    RAGFlow助手    网络搜索助手
          (MySQL)       (内部知识库)    (Tavily)
                  │               │               │
                  └───────────────┼───────────────┘
                                  ▼
                         文档生成工具链
                      generate_markdown / convert_md_to_pdf
```

## 目录结构

```
├── agent/                  # 智能体定义
│   ├── llm.py              # LLM 模型配置
│   ├── load_prompt.py      # Prompt 加载
│   ├── main_agent.py       # 主 Agent
│   └── sub_agents/         # 子 Agent (db / ragflow / internet)
├── api/                    # Web 服务
│   ├── server.py           # FastAPI 路由
│   ├── context.py          # 会话上下文管理
│   └── monitor.py          # WebSocket 推送管理
├── tools/                  # Agent 可调用的工具
│   ├── mysql_tools.py      # 数据库查询
│   ├── ragflow_tools.py    # RAGFlow 交互
│   ├── internet_search_tool.py  # 网络搜索
│   ├── upload_file_read_tool.py # 上传文件读取
│   ├── markdown_tools.py   # Markdown 生成
│   └── pdf_tools.py        # PDF 转换
├── prompt/prompts.yaml     # Agent system prompt 配置
├── sql/db.sql              # 数据库初始化脚本
├── main.py                 # 启动入口
└── pyproject.toml
```

## 技术栈

| 组件 | 技术 |
|------|------|
| Web 框架 | FastAPI + Uvicorn |
| Agent 框架 | deepagents |
| LLM | 阿里云 DashScope (兼容 OpenAI 接口) |
| 数据库 | MySQL |
| 知识库 | RAGFlow |
| 网络搜索 | Tavily |
| 文档处理 | pypdf / python-docx / openpyxl / markdown |
| 包管理 | uv |

## 快速开始

### 1. 安装依赖

```bash
uv sync
```

### 2. 配置环境变量

复制 `.env` 并填入你的实际配置：

| 变量 | 说明 |
|------|------|
| `MYSQL_HOST` / `MYSQL_PORT` / `MYSQL_USER` / `MYSQL_PASSWORD` / `MYSQL_DATABASE` | MySQL 数据库连接 |
| `RAGFLOW_API_URL` / `RAGFLOW_API_KEY` | RAGFlow 服务地址和密钥 |
| `TAVILY_API_KEY` | Tavily 网络搜索 API Key |
| `DASHSCOPE_BASE_URL` / `DASHSCOPE_API_KEY` | 阿里云 DashScope LLM 配置 |

### 3. 初始化数据库

```bash
mysql -u root -p < sql/db.sql
```

### 4. 启动服务

```bash
python main.py
```

服务默认监听 `http://0.0.0.0:8000`。

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/task` | 启动 Agent 任务，body: `{"query": "...", "thread_id": "..."}` |
| POST | `/api/upload` | 上传文件，form: `files[]` + `thread_id` |
| GET | `/api/files?path=...` | 列出输出目录下的文件 |
| GET | `/api/download?path=...` | 下载生成的文件 |
| WS | `/ws/{thread_id}` | 订阅实时推送（子 Agent 调用、工具调用、最终结果） |