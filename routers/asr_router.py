"""
ASR 路由
POST /api/asr   — 上传音频文件，返回识别文本
"""
from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status

from pydantic import BaseModel

from utils.logger import get_logger

logger = get_logger("routers.asr")
router = APIRouter(prefix="/api/asr", tags=["ASR"])

# 允许的音频格式
ALLOWED_SUFFIXES = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm"}


class ASRResponse(BaseModel):
    text: str


def get_asr_service(request):
    svc = request.app.state.asr_service
    if svc is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ASR 服务尚未就绪",
        )
    return svc


@router.post("", response_model=ASRResponse)
async def transcribe(request: Request, file: UploadFile = File(...)):
    # 文件后缀检查
    suffix = ""
    if file.filename:
        from pathlib import Path as _P
        suffix = _P(file.filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式 {suffix}，支持：{ALLOWED_SUFFIXES}",
        )

    svc = get_asr_service(request)
    audio_bytes = await file.read()
    try:
        text = svc.transcribe(audio_bytes, suffix=suffix)
    except RuntimeError as e:
        logger.error(f"ASR 识别失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))
    return ASRResponse(text=text)
