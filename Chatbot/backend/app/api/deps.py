from functools import lru_cache

from app.config import Settings, get_settings
from app.services.config_service import ConfigService
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService


@lru_cache
def get_llm_service() -> LLMService:
    return LLMService(get_settings())


@lru_cache
def get_rag_service() -> RAGService:
    settings = get_settings()
    return RAGService(settings, get_llm_service())


@lru_cache
def get_config_service() -> ConfigService:
    return ConfigService(get_settings())


def get_settings_dep() -> Settings:
    return get_settings()
