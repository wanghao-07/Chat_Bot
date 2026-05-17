# Chatbot — AI 智能客服（可商用）

通义千问（qwen-max）驱动的客服机器人：网站聊天界面、会话记忆、知识库 RAG（FAISS）、可配置品牌 Prompt。

## 功能

- **对话**：通义千问 Max（DashScope），多轮上下文记忆（SQLite）
- **RAG**：上传 PDF/TXT/MD，自动分块、向量化、检索增强回答
- **可配置**：品牌名、业务描述、语气、自定义 System Prompt（API + 前端设置页）
- **产品化**：结构化日志、统一错误响应、健康检查、知识库增删

## 快速开始

### 1. 环境

- Python 3.11+
- 阿里云 DashScope API Key（通义千问）

### 2. 安装

```bash
cd d:\Chatbot
copy .env.example .env
# 编辑 .env，填入 DASHSCOPE_API_KEY

python -m venv .venv
.venv\Scripts\activate
pip install -r backend\requirements.txt
```

### 3. 启动

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

浏览器访问：**http://localhost:8000**

### 4. 导入示例知识库

在界面「知识库」上传 `docs/sample_knowledge/refund_policy.txt`，然后问：「退款要多久？」

> 若从 OpenAI 切换为通义千问，请删除 `data/faiss/` 后重新上传知识库（嵌入模型维度不同）。

### 上传文档报 429 / insufficient_quota？

这是**向量化（Embedding）额度**问题，不是对话 Key 配错（对话与嵌入计费分开）。

1. 打开 [百炼控制台](https://bailian.console.aliyun.com/) → 费用/额度 → 查看 **text-embedding** 是否还有免费额度或需充值  
2. 确认已开通嵌入模型服务  
3. 可在 `.env` 尝试：`LLM_EMBEDDING_MODEL=text-embedding-v2`  
4. 修改后重启 `.\run.ps1`，删除 `data/faiss/` 后重新上传文档

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/chat` | 发送消息 |
| GET | `/api/v1/sessions/{id}` | 获取会话历史 |
| GET/POST/DELETE | `/api/v1/knowledge/documents` | 知识库列表/上传/删除 |
| GET/PUT | `/api/v1/config/prompt` | 读取/更新 Prompt 配置 |
| GET | `/api/v1/health` | 健康检查 |

## 项目结构

```
Chatbot/
├── backend/app/          # FastAPI 应用
│   ├── api/v1/           # 路由
│   ├── core/             # 编排、Prompt、异常
│   ├── services/         # LLM、RAG、记忆、入库
│   ├── rag/              # 分块、FAISS
│   └── models/           # ORM + Pydantic
├── frontend/             # 聊天 UI（HTML/CSS/JS）
├── data/                 # 运行时数据（自动创建）
└── docs/                 # 示例与产品文档
```

## 配置说明（.env）

| 变量 | 说明 |
|------|------|
| `DASHSCOPE_API_KEY` | 必填（百炼控制台） |
| `LLM_CHAT_MODEL` | 默认 `qwen-max` |
| `LLM_EMBEDDING_MODEL` | 默认 `text-embedding-v3`（RAG 向量） |
| `RAG_ENABLED` | 是否默认启用检索 |
| `MEMORY_MAX_TURNS` | 记忆轮数 |
| `BRAND_NAME` / `CUSTOM_SYSTEM_PROMPT` | 品牌与 Prompt |

## 接单与产品化

详见 [docs/PRODUCT.md](docs/PRODUCT.md)

## License

MIT（可按客户项目调整）
