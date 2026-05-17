from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/config.py -> project root is parents[2]
PROJECT_ROOT = Path(__file__).resolve().parents[2]
_ENV_CANDIDATES = [
    PROJECT_ROOT / ".env",
    PROJECT_ROOT / "backend" / ".env",
    Path.cwd() / ".env",
]

for _env_path in _ENV_CANDIDATES:
    if _env_path.exists():
        load_dotenv(_env_path, override=False)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[str(p) for p in _ENV_CANDIDATES if p.exists()] or ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 通义千问 / DashScope（OpenAI 兼容接口）
    dashscope_api_key: str = ""
    llm_chat_model: str = "qwen-max"
    llm_embedding_model: str = "text-embedding-v3"
    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # Brand / prompt
    app_name: str = "Chatbot Support"
    brand_name: str = "Your Company"
    company_description: str = "AI-powered customer support"
    system_prompt_tone: str = "friendly, concise, professional"
    custom_system_prompt: str = ""  # overrides default when set

    # Paths
    data_dir: str = ""
    database_url: str = ""

    # Chat
    memory_max_turns: int = 12
    max_tokens: int = 800
    temperature: float = 0.3

    # RAG（默认关：无知识库时避免无意义调用 Embedding）
    rag_enabled: bool = False
    llm_timeout: float = 120.0
    rag_top_k: int = 5
    rag_score_threshold: float = 0.35
    chunk_size: int = 600
    chunk_overlap: int = 100

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "*"

    # Logging
    log_level: str = "INFO"

    def model_post_init(self, __context) -> None:
        api_key = (self.dashscope_api_key or "").strip()
        object.__setattr__(self, "dashscope_api_key", api_key)
        base_url = (self.llm_base_url or "").strip().rstrip("/")
        object.__setattr__(self, "llm_base_url", base_url)

        data = Path(self.data_dir) if self.data_dir else (PROJECT_ROOT / "data")
        if not data.is_absolute():
            data = PROJECT_ROOT / data
        object.__setattr__(self, "data_dir", str(data.resolve()))

        if not self.database_url:
            db_path = Path(self.data_dir) / "chatbot.db"
            object.__setattr__(
                self, "database_url", f"sqlite+aiosqlite:///{db_path.as_posix()}"
            )
        elif self.database_url.startswith("sqlite") and ":///" in self.database_url:
            rel = self.database_url.split("///", 1)[1]
            if rel.startswith("./") or not Path(rel).is_absolute():
                db_path = (PROJECT_ROOT / rel.removeprefix("./")).resolve()
                object.__setattr__(
                    self, "database_url", f"sqlite+aiosqlite:///{db_path.as_posix()}"
                )

    @property
    def llm_configured(self) -> bool:
        key = self.dashscope_api_key
        if not key or key.startswith("sk-your-") or key in ("your-api-key", "sk-xxx"):
            return False
        return True

    # 兼容旧代码/健康检查字段名
    @property
    def openai_configured(self) -> bool:
        return self.llm_configured

    @property
    def data_path(self) -> Path:
        p = Path(self.data_dir)
        p.mkdir(parents=True, exist_ok=True)
        (p / "uploads").mkdir(exist_ok=True)
        (p / "faiss").mkdir(exist_ok=True)
        return p

    @property
    def cors_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
