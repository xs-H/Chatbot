"""
RAG 服务
- 负责 JSON 知识库的向量化、FAISS 索引的持久化与增量更新
- 对上层提供 retrieve(query) 接口
"""
import hashlib
import json
import os
from typing import Any

import chardet
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

from config import PathConfig, RAGConfig
from utils.logger import get_logger

logger = get_logger("services.rag", "rag.log")


# ── 工具函数 ────────────────────────────────────────────────────────────────

def _detect_encoding(file_path: str) -> str:
    with open(file_path, "rb") as f:
        raw = f.read(10000)
    result = chardet.detect(raw)
    if result["confidence"] < 0.85:
        return _try_common_encodings(raw)
    enc = result["encoding"].lower()
    return {"gb2312": "gb18030", "ascii": "utf-8", "windows-1252": "utf-8"}.get(enc, enc)


def _try_common_encodings(data: bytes) -> str:
    for enc in ["utf-8-sig", "gb18030", "utf-16", "big5"]:
        try:
            data.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
    return "utf-8"


def _process_value(value: Any) -> str:
    if isinstance(value, dict):
        return "；".join(f"{k}：{_process_value(v)}" for k, v in value.items())
    if isinstance(value, list):
        return "、".join(map(str, value))
    return str(value)


def _extract_texts(data: dict) -> list[str]:
    """将 NeZha.json 的嵌套结构展平为字符串列表"""
    results = []
    db = data.get("数据库", {})
    for top_key, top_data in db.items():
        if not isinstance(top_data, dict):
            continue
        for role_name, role_data in top_data.items():
            if not isinstance(role_data, dict):
                continue
            for sub_key, sub_val in role_data.items():
                content = _process_value(sub_val)
                results.append(f"{top_key}-{role_name}-{sub_key}：{content}")
    return results


# ── 主服务类 ────────────────────────────────────────────────────────────────

class RAGService:
    """向量检索服务（单例，由 main.py lifespan 初始化）"""

    def __init__(self) -> None:
        logger.info("初始化 RAG 服务，加载 Embedding 模型…")
        self._embeddings = HuggingFaceEmbeddings(
            model_name=PathConfig.EMBEDDING_MODEL
        )
        self._db: FAISS = self._load_or_build_index()
        logger.info("RAG 服务就绪。")

    # ── 索引管理 ─────────────────────────────────────────────────────────────

    def _current_hash(self) -> str:
        with open(PathConfig.JSON_PATH, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()

    def _load_or_build_index(self) -> FAISS:
        hash_file = PathConfig.VECTOR_SAVE_PATH / "db_hash.txt"
        current = self._current_hash()

        if hash_file.exists():
            if hash_file.read_text().strip() == current:
                logger.info("向量库未变更，直接加载…")
                return FAISS.load_local(
                    str(PathConfig.VECTOR_SAVE_PATH),
                    self._embeddings,
                    allow_dangerous_deserialization=True,
                )
            logger.warning("知识库文件已更新，重新构建向量索引…")

        return self._build_index(current, hash_file)

    def _build_index(self, current_hash: str, hash_file) -> FAISS:
        logger.info("开始构建向量索引…")
        enc = _detect_encoding(str(PathConfig.JSON_PATH))
        try:
            with open(PathConfig.JSON_PATH, "r", encoding=enc) as f:
                data = json.load(f)
        except UnicodeDecodeError:
            logger.warning(f"编码 {enc} 解码失败，使用 errors='replace' 重试")
            with open(PathConfig.JSON_PATH, "r", encoding=enc, errors="replace") as f:
                data = json.load(f)

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=RAGConfig.CHUNK_SIZE,
            chunk_overlap=RAGConfig.CHUNK_OVERLAP,
        )
        docs = []
        for text in _extract_texts(data):
            docs.extend(splitter.create_documents([text]))

        db = FAISS.from_documents(docs, self._embeddings)
        db.save_local(str(PathConfig.VECTOR_SAVE_PATH))
        hash_file.write_text(current_hash)
        logger.info(f"向量索引构建完成，共 {len(docs)} 个分块。")
        return db

    # ── 对外接口 ─────────────────────────────────────────────────────────────

    def retrieve(self, query: str) -> list[str]:
        """
        检索与 query 最相关的知识片段，返回文本列表。
        """
        results = self._db.similarity_search(query, k=RAGConfig.DEFAULT_K)
        texts = [r.page_content for r in results]
        logger.debug(f"RAG 检索 [{query[:30]}…] → {len(texts)} 条结果")
        return texts
