"""
统一日志工具
- 所有模块通过 get_logger(__name__) 获取 logger
- 日志同时输出到控制台和文件
- 文件按模块分流：app.log（主服务）、chat.log、tts.log、asr.log
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from config import PathConfig

_initialized: set[str] = set()


def get_logger(name: str, log_file: str | None = None) -> logging.Logger:
    """
    获取带控制台 + 文件 Handler 的 logger。
    同一 name 多次调用不会重复添加 handler。
    """
    logger = logging.getLogger(name)

    if name in _initialized:
        return logger

    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter(
        "%(asctime)s  %(levelname)-8s  [%(name)s]  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台 handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # 文件 handler（滚动，最大 10 MB，保留 3 份）
    _log_file = log_file or f"{name.split('.')[-1]}.log"
    fh = RotatingFileHandler(
        PathConfig.LOG_DIR / _log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    # 禁止向 root logger 传播，避免与 uvicorn/第三方日志重复输出
    logger.propagate = False

    _initialized.add(name)
    return logger
