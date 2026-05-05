"""
Chat 服务
- 封装 Ollama 调用与多轮对话管理
- 支持按 session_id 隔离会话历史（为 Jetson 多客户端预留）
- RAGService 以依赖注入方式传入，不在本模块硬依赖
"""
from __future__ import annotations

import ollama

from config import LLMConfig, RAGConfig
from utils.logger import get_logger

logger = get_logger("services.chat", "chat.log")


class ChatService:
    """
    对话服务（单例，由 main.py lifespan 初始化）

    conversation_history 以 session_id 为键分开存储，
    默认会话 id 为 "default"（兼容单客户端场景）。
    """

    def __init__(self, rag_service) -> None:
        logger.info("初始化 Chat 服务，连接 Ollama…")
        self._rag = rag_service
        self._client = ollama.Client(host=LLMConfig.OLLAMA_HOST)
        self._model = LLMConfig.MODEL_NAME
        self._histories: dict[str, list[dict]] = {}

        # 连通性探测
        try:
            models = self._client.list()
            if isinstance(models, dict):
                model_items = models.get("models", [])
            else:
                model_items = getattr(models, "models", []) or []
            names: list[str] = []
            for m in model_items:
                # 兼容不同 Ollama 版本/SDK 返回字段：name 或 model
                if isinstance(m, dict):
                    model_name = m.get("name") or m.get("model")
                else:
                    model_name = getattr(m, "name", None) or getattr(m, "model", None)
                if model_name:
                    names.append(model_name)
            logger.info(f"Ollama 已连接，可用模型：{names}")
            if self._model not in names:
                logger.warning(f"模型 {self._model} 不在列表中，请确认已注册")
        except Exception as e:
            logger.error(f"Ollama 连接失败：{e}，终止应用启动")
            raise RuntimeError(f"Ollama 连接失败：{e}") from e

        logger.info("Chat 服务就绪。")

    # ── 内部工具 ─────────────────────────────────────────────────────────────

    def _get_history(self, session_id: str) -> list[dict]:
        return self._histories.setdefault(session_id, [])

    def _build_messages(
        self, query: str, context: list[str], history: list[dict]
    ) -> list[dict]:
        """构造发送给 Ollama 的消息列表"""
        trimmed = history[-LLMConfig.MAX_HISTORY:]
    
        # 按字符预算截断上下文
        packed: list[str] = []
        total_len = 0
        for i, t in enumerate(context, start=1):
            block = f"[角色资料 {i}] {t}"
            if total_len + len(block) > RAGConfig.MAX_CONTEXT_LEN:
                break
            packed.append(block)
            total_len += len(block)
        context_str = "\n".join(packed) if packed else "暂无相关资料"
    
        user_msg = {
            "role": "user",
            "content": (
                f"用户询问：{query}\n"
                f"请适当参考你的经历：{context_str}\n"
                f"回复用户的聊天对话：{query}"
            ),
        }
    
        return [*trimmed, user_msg]


    # ── 对外接口 ─────────────────────────────────────────────────────────────

    def chat(self, query: str, session_id: str = "default") -> str:
        """
        单轮对话入口。
        返回角色回复字符串，异常时抛出 RuntimeError。
        """
        history = self._get_history(session_id)
        context = self._rag.retrieve(query)
        messages = self._build_messages(query, context, history)

        try:
            resp = self._client.chat(
                model=self._model,
                messages=messages,
                options={"temperature": LLMConfig.TEMPERATURE},
            )
        except Exception as e:
            logger.error(f"Ollama 推理失败 [{session_id}]：{e}")
            raise RuntimeError(f"LLM 推理错误：{e}") from e

        reply: str = resp["message"]["content"].lstrip("\n")

        # 更新会话历史
        history.extend([
            {"role": "user",      "content": query},
            {"role": "assistant", "content": reply},
        ])

        logger.info(f"[{session_id}] Q: {query[:50]}… | A: {reply[:80]}…")
        return reply

    def reset(self, session_id: str = "default") -> None:
        """清空指定会话的历史记录"""
        self._histories.pop(session_id, None)
        logger.info(f"会话 [{session_id}] 历史已重置")

    def reset_all(self) -> None:
        """清空所有会话"""
        self._histories.clear()
        logger.info("所有会话历史已清空")
