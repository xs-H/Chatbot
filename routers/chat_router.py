"""
Chat 路由
POST /api/chat          — 发送消息，获取角色回复
POST /api/chat/reset    — 重置指定会话历史
"""
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from utils.logger import get_logger

logger = get_logger("routers.chat")
router = APIRouter(prefix="/api/chat", tags=["Chat"])


# ── 请求 / 响应 Schema ────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message:    str = Field(..., min_length=1, description="用户消息")
    session_id: str = Field("default",         description="会话 ID，用于隔离多客户端历史")


class ChatResponse(BaseModel):
    reply:      str
    session_id: str


class ResetRequest(BaseModel):
    session_id: str = Field("default", description="要重置的会话 ID")


# ── 依赖注入（从 app.state 取服务实例）──────────────────────────────────────

def get_chat_service(request):
    svc = request.app.state.chat_service
    if svc is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat 服务尚未就绪",
        )
    return svc


# ── 路由处理 ─────────────────────────────────────────────────────────────────

@router.post("", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request):
    svc = get_chat_service(request)
    try:
        reply = svc.chat(body.message, session_id=body.session_id)
    except RuntimeError as e:
        logger.error(f"Chat 推理失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))
    return ChatResponse(reply=reply, session_id=body.session_id)


@router.post("/reset")
async def reset(body: ResetRequest, request: Request):
    svc = get_chat_service(request)
    svc.reset(session_id=body.session_id)
    return {"status": "ok", "session_id": body.session_id}
