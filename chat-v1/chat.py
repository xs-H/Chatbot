import os
import logging
import ollama
import pynvml
from rag import Config, TextEmbedding


pynvml.nvmlInit()
handle = pynvml.nvmlDeviceGetHandleByIndex(0)

class ChatSystem:
    def __init__(self):
        self.text_embedding = TextEmbedding()
        self.client = ollama.Client(host='http://localhost:11434')
        self.model_name = 'qwen-role:latest'
        self.conversation_history = []

    def _format_messages(self, query, context):
        """构造消息结构"""
        history = [{'role': msg['role'], 'content': msg['content']} for msg in
                   self.conversation_history[-Config.max_history:]]
        context_str = '\n'.join([f'[角色资料 {i + 1}] {text}' for i, text in enumerate(context)])

        return [
            *history,
            {'role': 'user', 'content': f"请你扮演哪吒，模仿哪吒回复我的话：{query}（避免让我察觉你在模仿）。"
                                        f"\n回复时适当参考哪吒的资料：{context_str}"}
        ]

    # def _process_reply(self, reply):
    #     """提取和处理回复内容，去除<think>...</think>部分"""
    #     # 使用正则表达式去除思考部分
    #     think_content_pattern = re.compile(r'<think>.*?</think>', re.DOTALL)
    #     think_parts = re.findall(think_content_pattern, reply)
    #
    #     # 去除<think>...</think>标签内容
    #     clean_reply = re.sub(think_content_pattern, '', reply)
    #
    #     return clean_reply, think_parts  # 返回干净的回复和思考部分

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
                Q = f"{query}+哪吒台词"
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
                logging.info(f"显存占用：{pynvml.nvmlDeviceGetMemoryInfo(handle).used / 1024 ** 3}")
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

                # 记录日志
                logging.info(f"Query: {query}")
                logging.info(f"Reply: {reply}")


            except KeyboardInterrupt:
                break
            except Exception as e:
                logging.error(f"对话异常: {str(e)}")
                print("抱歉，出现错误，请重新输入")

        print("\n=== 对话结束 ===")


if __name__ == '__main__':
    try:
        print(f"显存占用：{pynvml.nvmlDeviceGetMemoryInfo(handle).used/1024**3}GB")
        chat_system = ChatSystem()
        print(f"显存占用：{pynvml.nvmlDeviceGetMemoryInfo(handle).used/1024**3}GB")
        chat_system.chat_loop()
    except Exception as e:
        logging.critical(f"系统启动失败: {str(e)}")
        print(f"系统初始化错误: {str(e)}")
