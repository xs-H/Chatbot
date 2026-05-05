"""
统一配置文件 — 所有路径、模型参数、服务参数均在此处管理
修改配置只需编辑本文件，无需深入各个模块。
"""
import os
from pathlib import Path

# ── 项目根目录（本文件所在位置）────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent


class PathConfig:
    """路径配置"""
    # 资源目录
    RESOURCE_DIR    = BASE_DIR / "resource"
    LOG_DIR         = BASE_DIR / "logs"
    DATABASE_DIR    = RESOURCE_DIR / "database"
    VOICE_DIR       = RESOURCE_DIR / "voice"
    AUDIO_OUT_DIR   = BASE_DIR / "output" / "generated_audio"

    # RAG 向量库
    JSON_PATH       = DATABASE_DIR / "NeZha.json"
    VECTOR_SAVE_PATH = DATABASE_DIR  # FAISS 索引存储目录

    # 向量编码模型（本地路径，解决 transformers 版本兼容问题）
    EMBEDDING_MODEL = str(BASE_DIR / "modules" / "Text2Vec")

    # TTS
    COSYVOICE_DIR   = BASE_DIR / "modules" / "COSYVoice"
    TTS_MODEL_DIR   = COSYVOICE_DIR / "pretrained_models" / "CosyVoice2-0.5B"
    REFERENCE_AUDIO = VOICE_DIR / "NZ_angry.mp3"

    # ASR（Whisper 模型缓存目录，None 则使用默认 ~/.cache）
    WHISPER_CACHE_DIR = None


class LLMConfig:
    """LLM / Ollama 配置"""
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    # 按显存选择量化版本：
    #   qwen-role-lora:latest  → FP16  ~16 GB
    #   qwen-role-Q8:latest    → Q8_0  ~10 GB  ← 推荐
    #   qwen-role-Q5:latest    → Q5_K_M ~6 GB
    MODEL_NAME  = os.getenv("LLM_MODEL", "NeZha:latest")

    MAX_HISTORY     = 20    # 携带的历史轮次（条）
    TEMPERATURE     = 0.5


class RAGConfig:
    """RAG 检索配置"""
    DEFAULT_K           = 5      # 每次检索返回条数
    MIN_SIMILARITY      = 0.8    # 相似度阈值（暂保留，供二次过滤）
    SEARCH_MULTIPLIER   = 5      # similarity_search 扩展倍数
    MAX_CONTEXT_LEN     = 1000   # 上下文拼接最大字符数
    CHUNK_SIZE          = 500    # 文本切分块大小
    CHUNK_OVERLAP       = 50


class TTSConfig:
    """TTS 配置"""
    REFERENCE_TEXT = "拜个屁的师我什么都不学！修炼了出去捧那些白痴的臭脚，还不如在这睡大觉。"
    SAMPLE_RATE    = 22050   # 由 CosyVoice 实例覆盖，此处仅为回退值
    FP16           = False
    LOAD_JIT       = False
    LOAD_TRT       = False


class ASRConfig:
    """ASR / Whisper 配置"""
    # 模型规格：tiny / base / small / medium / large-v3
    # 服务器推荐 small 或 medium，延迟与精度平衡较好
    MODEL_SIZE = os.getenv("WHISPER_MODEL", "small")
    LANGUAGE   = "zh"   # 强制中文，加速推理；None 则自动检测


class ServerConfig:
    """FastAPI 服务配置"""
    HOST      = "0.0.0.0"
    PORT      = int(os.getenv("PORT", 6008))
    LOG_LEVEL = "info"
    # 允许跨域的来源，生产环境请收紧为 Jetson IP
    CORS_ORIGINS = ["*"]


# ── 确保必要目录存在 ────────────────────────────────────────────────────────
for _d in [PathConfig.LOG_DIR, PathConfig.AUDIO_OUT_DIR, PathConfig.DATABASE_DIR]:
    _d.mkdir(parents=True, exist_ok=True)
