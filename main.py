"""
ChatBot — 统一后端入口（FastAPI）

启动方式：
    conda activate CHATBOT
    python main.py

或使用 uvicorn 直接启动：
    uvicorn main:app --host 0.0.0.0 --port 8000

API 文档：
    http://<server_ip>:8000/docs
"""
from __future__ import annotations

import logging
import traceback
import warnings
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import ServerConfig
from utils.logger import get_logger

# ── 日志/告警降噪（仅过滤已知无害项）───────────────────────────────────────
warnings.filterwarnings(
    "ignore",
    message=r"Sliding Window Attention is enabled but not implemented for `sdpa`.*",
)
warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    message=r"`LoRACompatibleLinear` is deprecated.*",
)
warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    message=r"`torch\.nn\.utils\.weight_norm` is deprecated.*",
)

# 下调 HTTP 客户端调试噪声，仅保留 warning/error。
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = get_logger("main", "app.log")


# ── Lifespan：统一管理服务初始化与销毁 ──────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    启动时按顺序初始化各服务，写入 app.state。
    任一服务初始化失败时，该服务置为 None，其路由返回 503，不影响其他服务。
    """
    logger.info("═" * 60)
    logger.info("ChatBot 后端启动中…")
    logger.info("═" * 60)

    # 1. RAG 服务（必须最先，Chat 依赖它）
    app.state.rag_service = None
    try:
        from services.rag_service import RAGService
        app.state.rag_service = RAGService()
    except Exception:
        logger.error(f"RAG 服务初始化失败：\n{traceback.format_exc()}")

    # 2. Chat 服务
    app.state.chat_service = None
    if app.state.rag_service is not None:
        try:
            from services.chat_service import ChatService
            app.state.chat_service = ChatService(app.state.rag_service)
        except Exception:
            logger.error(f"Chat 服务初始化失败：\n{traceback.format_exc()}")
            raise RuntimeError("Chat 服务初始化失败，应用终止启动")
    else:
        logger.warning("RAG 服务不可用，Chat 服务跳过初始化")

    # 3. TTS 服务
    app.state.tts_service = None
    try:
        from services.tts_service import TTSService
        app.state.tts_service = TTSService()
    except Exception:
        logger.error(f"TTS 服务初始化失败：\n{traceback.format_exc()}")

    # 4. ASR 服务（懒加载 Whisper，此处仅创建实例）
    app.state.asr_service = None
    try:
        from services.asr_service import ASRService
        app.state.asr_service = ASRService()
    except Exception:
        logger.error(f"ASR 服务初始化失败：\n{traceback.format_exc()}")

    # 启动状态汇报
    status_map = {
        "RAG":  app.state.rag_service,
        "Chat": app.state.chat_service,
        "TTS":  app.state.tts_service,
        "ASR":  app.state.asr_service,
    }
    logger.info("── 服务启动状态 ──")
    for name, svc in status_map.items():
        state = "✅ 就绪" if svc is not None else "❌ 不可用"
        logger.info(f"  {name:<6} {state}")
    logger.info("═" * 60)

    yield  # ── 应用运行期间 ────────────────────────────────────────────────

    logger.info("ChatBot 后端正在关闭…")


# ── FastAPI 应用 ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="ChatBot API",
    description="哪吒角色对话后端：Chat / TTS / ASR 统一接口",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS（允许 Jetson 等跨域客户端访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=ServerConfig.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 全局异常处理 ─────────────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理异常 [{request.url}]：{exc}\n{traceback.format_exc()}")
    return JSONResponse(status_code=500, content={"detail": "服务器内部错误"})


# ── 路由注册 ─────────────────────────────────────────────────────────────────

from routers.chat_router import router as chat_router
from routers.tts_router  import router as tts_router
from routers.asr_router  import router as asr_router

app.include_router(chat_router)
app.include_router(tts_router)
app.include_router(asr_router)


# ── 健康检查 ─────────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health():
    """各服务就绪状态快照"""
    return {
        "status": "ok",
        "services": {
            "rag":  app.state.rag_service  is not None,
            "chat": app.state.chat_service is not None,
            "tts":  app.state.tts_service  is not None,
            "asr":  app.state.asr_service  is not None,
        },
    }


# ── 入口 ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=ServerConfig.HOST,
        port=ServerConfig.PORT,
        log_level=ServerConfig.LOG_LEVEL,
        reload=False,
    )
