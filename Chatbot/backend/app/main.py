import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1 import chat, config, health, knowledge, sessions
from app.config import PROJECT_ROOT, get_settings
from app.core.exceptions import AppError
from app.models.db import init_db

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.data_path
    await init_db()
    if not settings.llm_configured:
        logger.warning(
            "DASHSCOPE_API_KEY 未配置或无效，对话功能不可用。请在 %s 配置",
            PROJECT_ROOT / ".env",
        )
    logger.info("Application started: %s", settings.app_name)
    yield
    logger.info("Application shutdown")


app = FastAPI(
    title=settings.app_name,
    description="AI Customer Support Chatbot API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    logger.warning("AppError path=%s code=%s msg=%s", request.url.path, exc.code, exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "code": exc.code},
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error path=%s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "code": "INTERNAL_ERROR"},
    )


app.include_router(health.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(sessions.router, prefix="/api/v1")
app.include_router(knowledge.router, prefix="/api/v1")
app.include_router(config.router, prefix="/api/v1")

# Serve frontend static files
_frontend = Path(__file__).resolve().parents[2] / "frontend"
if _frontend.exists():
    app.mount("/", StaticFiles(directory=str(_frontend), html=True), name="frontend")
