"""
TTS 路由
POST /api/tts               — 文本转语音，返回音频文件名列表
GET  /api/tts/audio/{name}  — 下载指定音频文件
"""
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from config import PathConfig
from utils.logger import get_logger

logger = get_logger("routers.tts")
router = APIRouter(prefix="/api/tts", tags=["TTS"])


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, description="需要合成的文本")


class TTSResponse(BaseModel):
    audio_files: list[str]   # 文件名列表，通过 /api/tts/audio/{name} 下载


def get_tts_service(request):
    svc = request.app.state.tts_service
    if svc is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="TTS 服务尚未就绪",
        )
    return svc


@router.post("", response_model=TTSResponse)
async def tts(body: TTSRequest, request: Request):
    svc = get_tts_service(request)
    try:
        paths = svc.synthesize(body.text)
    except (ValueError, RuntimeError) as e:
        logger.error(f"TTS 合成失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))
    return TTSResponse(audio_files=[p.name for p in paths])


@router.get("/audio/{filename}")
async def get_audio(filename: str):
    """下载合成的音频文件"""
    # 安全校验：仅允许 .wav 文件，防止路径穿越
    if not filename.endswith(".wav") or "/" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="非法文件名")
    file_path = PathConfig.AUDIO_OUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(str(file_path), media_type="audio/wav", filename=filename)
