# import os
import logging
import ollama
import pynvml
# from transformers import AutoModelForCausalLM, AutoTokenizer
from rag import Config, TextEmbedding


pynvml.nvmlInit()
handle = pynvml.nvmlDeviceGetHandleByIndex(0)

class ChatSystem:
    def __init__(self):
        self.text_embedding = TextEmbedding()
        self.client = ollama.Client(host='http://localhost:11434')
        # self.client_a = ollama.Client(host='http://localhost:11434')
        # self.model_name_a = 'qwen-assist:latest'
        self.model_name = 'qwen-role:latest'
        self.conversation_history = []

    def _format_messages(self, query, context):
        """构造消息结构"""
        history = [{'role': msg['role'], 'content': msg['content']} for msg in
                   self.conversation_history[-Config.max_history:]]
        context_str = '\n'.join([f'[角色资料 {i + 1}] {text}' for i, text in enumerate(context)])

        return [
            *history,
            {'role': 'user', 'content': f"可参考角色的资料：{context_str}"
                                        f"\n{query}"}
        ]

    def _query_enhance(self, query):
        message = [
            {'role': 'user', 'content': f"请适当优化当前用户查询（使表义更明确、通俗）：{query}，直接返回结果。"}
        ]
        try:
            response = self.client.chat(
                model=self.model_name_a,
                messages=message,
                options={'temperature': 0.6}
            )
            enhanced_query = response['message']['content']

            return enhanced_query
        except Exception as e:
            logging.error(f"查询增强出错：{e}")

    # 解决log乱码
    def _ensure_utf8(self, text):  # 添加 self 参数
        if isinstance(text, bytes):
            return text.decode('utf-8', errors='replace')
        return text


    def chat_loop(self):
        """主对话循环"""
        print("~~~~~~~~~~对话开始~~~~~~~~~~~~")
        print("输入 'exit' 结束对话\n")

        while True:
            try:
                query = input("您：").strip()
                if query.lower() in ('exit', 'quit'):
                    break
                if not query:
                    continue
                # 查询增强
                Q = self._query_enhance(query)
                # 检索上下文
                context = self.text_embedding._retrieve_context(Q)
                # 构造消息
                messages = self._format_messages(query, context)
                # 生成回复
                response = self.client.chat(
                    model=self.model_name,
                    messages=messages,
                    # options={'temperature': 0.7}
                )
                logging.info(f"显存占用：{pynvml.nvmlDeviceGetMemoryInfo(handle).used / 1024 ** 3} GB")

                reply = response['message']['content']

                # 处理回复，提取并移除<think>部分
                # clean_reply, think_parts = self._process_reply(reply)
                reply = reply.lstrip('\n')

                # 输出并记录
                print(f"哪吒：{reply}\n")
                self.conversation_history.extend([
                    {'role': 'user', 'content': query},
                    {'role': 'assistant', 'content': reply}
                ])

                # 记录日志: 解决乱码
                logging.info(f"Query: {self._ensure_utf8(query)}")
                logging.info(f"Reply: {self._ensure_utf8(reply)}")

            except KeyboardInterrupt:
                break
            except Exception as e:
                logging.error(f"对话异常: {str(e)}")
                print("抱歉，出现错误，请重新输入")

        print("\n========== 对话结束 ===========")


if __name__ == '__main__':
    try:
        print(f"显存占用：{pynvml.nvmlDeviceGetMemoryInfo(handle).used/1024**3} GB")
        chat_system = ChatSystem()
        print(f"显存占用：{pynvml.nvmlDeviceGetMemoryInfo(handle).used/1024**3} GB")
        chat_system.chat_loop()
    except Exception as e:
        logging.critical(f"系统启动失败: {str(e)}")
        print(f"系统初始化错误: {str(e)}")

