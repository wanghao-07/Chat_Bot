import logging

import httpx
from openai import APIConnectionError, APIError, APITimeoutError, AsyncOpenAI, RateLimitError

from app.config import Settings
from app.core.exceptions import LLMError

logger = logging.getLogger(__name__)

_QUOTA_HINT = (
    "阿里云百炼「向量化」额度不足或未开通。"
    "请登录 https://bailian.console.aliyun.com/ 查看余额、免费额度，"
    "并确认已开通 text-embedding 模型；也可在 .env 将 LLM_EMBEDDING_MODEL 改为 text-embedding-v2 后重试。"
)


def _format_api_error(e: APIError, *, for_embedding: bool = False) -> str:
    """将 DashScope 兼容接口错误转为中文说明（兼容 OpenAI 格式错误体）。"""
    raw = (getattr(e, "message", None) or str(e)).lower()
    status = getattr(e, "status_code", None)
    if status == 429 or "insufficient_quota" in raw or "quota" in raw:
        return _QUOTA_HINT if for_embedding else "通义千问调用额度不足，请在百炼控制台充值或检查套餐。"
    if status == 401:
        return "API Key 无效或已过期，请检查 DASHSCOPE_API_KEY。"
    if "connection" in raw or status is None:
        return "无法连接通义千问服务，请检查网络或 LLM_BASE_URL 配置。"
    if for_embedding:
        return f"向量嵌入失败: {e.message}"
    return f"通义千问 API 错误: {e.message}"


class LLMService:
    """通义千问（DashScope OpenAI 兼容模式）"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._client: AsyncOpenAI | None = None

    @property
    def client(self) -> AsyncOpenAI:
        if not self.settings.llm_configured:
            raise LLMError(
                "未配置通义千问 API Key，请在项目根目录 .env 中设置 DASHSCOPE_API_KEY",
                code="API_KEY_MISSING",
                status_code=503,
            )
        if self._client is None:
            timeout = httpx.Timeout(self.settings.llm_timeout, connect=30.0)
            self._client = AsyncOpenAI(
                api_key=self.settings.dashscope_api_key,
                base_url=self.settings.llm_base_url,
                timeout=timeout,
                max_retries=0,
            )
        return self._client

    async def chat(
        self,
        messages: list[dict[str, str]],
    ) -> tuple[str, dict]:
        try:
            response = await self.client.chat.completions.create(
                model=self.settings.llm_chat_model,
                messages=messages,
                max_tokens=self.settings.max_tokens,
                temperature=self.settings.temperature,
            )
            choice = response.choices[0]
            content = choice.message.content or ""
            usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            }
            logger.info(
                "LLM completion provider=dashscope model=%s tokens=%s",
                self.settings.llm_chat_model,
                usage["total_tokens"],
            )
            return content, usage
        except RateLimitError as e:
            logger.error("DashScope rate limit: %s", e)
            raw = str(e).lower()
            if "insufficient_quota" in raw or "quota" in raw:
                raise LLMError(
                    "通义千问额度不足或请求过快，请稍等 1 分钟后重试，"
                    "并暂时关闭左侧「知识库检索」。",
                    code="QUOTA_EXCEEDED",
                    status_code=429,
                ) from e
            raise LLMError("请求过于频繁，请等待 30 秒后重试。") from e
        except APITimeoutError as e:
            logger.error("DashScope chat timeout: %s", e)
            raise LLMError("对话请求超时，请稍后重试或改用 qwen-turbo 模型。") from e
        except APIConnectionError as e:
            logger.error("DashScope connection error: %s", e)
            raise LLMError("无法连接通义千问，请检查网络。") from e
        except APIError as e:
            logger.error("DashScope API error: %s", e)
            raise LLMError(_format_api_error(e)) from e
        except Exception as e:
            logger.exception("Unexpected LLM error")
            raise LLMError(f"生成回复失败: {e}") from e

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            response = await self.client.embeddings.create(
                model=self.settings.llm_embedding_model,
                input=texts,
            )
            return [item.embedding for item in response.data]
        except (APITimeoutError, APIConnectionError) as e:
            logger.error("DashScope embedding network error: %s", e)
            raise LLMError("向量服务连接超时，请稍后重试。") from e
        except APIError as e:
            logger.error("DashScope embedding error: %s", e)
            raise LLMError(_format_api_error(e, for_embedding=True)) from e
        except Exception as e:
            logger.error("DashScope embedding unexpected: %s", e)
            raise LLMError(f"向量嵌入失败: {e}") from e
