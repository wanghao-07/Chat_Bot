# 产品化与接单指南

## 可售卖形态

将本项目打包为 **「AI 智能客服 SaaS / 私有化部署」** 三档报价：

| 档位 | 交付内容 | 参考报价思路 |
|------|----------|--------------|
| **Starter** | 单租户、聊天 + 知识库上传、品牌 Prompt 配置 | 按项目 3k–8k |
| **Business** | 多租户、嵌入 Widget、用量统计、Docker 部署 | 8k–20k |
| **Enterprise** | 人工接管 Webhook、CRM 对接、SLA | 20k+ / 年维保 |

## 给客户的价值话术

- **7×24 即时回复**：常见问题由知识库 + GPT 自动解答
- **可控**：答案基于上传文档，减少胡编；可配置语气与品牌
- **可运营**：后台上传 PDF/文档即可更新知识库，无需改代码
- **可扩展**：会话记忆、转人工标记 `[HANDOFF]`，便于后续接工单系统

## 部署清单（交付用）

1. 复制 `.env.example` → `.env`，填入 `DASHSCOPE_API_KEY`
2. `pip install -r backend/requirements.txt`
3. `cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000`
4. 浏览器打开 `http://localhost:8000`
5. 在「知识库」上传客户 FAQ / 产品手册
6. 在「设置」配置品牌名与自定义 Prompt

## Portfolio 展示建议

1. **录屏 60–90 秒**：上传文档 → 提问 → 展示引用来源 → 转人工场景
2. **架构图**：前端 + FastAPI + FAISS + OpenAI（放 README）
3. **案例页**：虚构「电商客服」场景 + 3 个示例问答截图
4. **GitHub README**：突出 `RAG`、`可配置 Prompt`、`生产级错误处理`
5. **技术关键词**：FastAPI, 通义千问, DashScope, RAG, FAISS, SQLite

## 真实客户场景

- **电商**：退换货、物流、优惠规则（PDF 政策文档）
- **SaaS**：功能说明、计费、入门教程（Markdown 帮助中心导出）
- **教培/咨询**：课程 FAQ、报名流程（TXT/MD）

## 后续增值功能（报价加项）

- 网站嵌入 `<script>` Widget
- 企业微信 / 飞书机器人通道
- 对话分析看板（热点问题、满意度）
- Azure/OpenAI 国内代理与合规说明
