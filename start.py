import subprocess
import sys
import threading
import time
import os
import webbrowser

# 启动 api
def start_tts_api():
    # 设置 tts_api 的工作目录为 backend/tts_backend
    cwd = os.path.join("backend", "tts_backend")
    proc = subprocess.Popen([sys.executable, "tts_api.py"], cwd=cwd)
    proc.wait()

def start_chat_api():
    # 设置 chat_api 的工作目录为 backend/chat_backend
    cwd = os.path.join("backend", "chat_backend")
    proc = subprocess.Popen([sys.executable, "chat_api.py"], cwd=cwd)
    proc.wait()

# 启动前端页面
def open_frontend():
    # 构造 frontend/index.html 的绝对路径并转换为 file:// URL
    index_path = os.path.abspath(os.path.join("frontend", "index.html"))
    url = f"file://{index_path}"
    print(f"正在打开前端页面: {url}")
    webbrowser.open(url)

if __name__ == '__main__':
    # 分别通过线程启动两个 API 服务
    tts_thread = threading.Thread(target=start_tts_api, name="TTS_API_Thread")
    chat_thread = threading.Thread(target=start_chat_api, name="CHAT_API_Thread")

    tts_thread.start()
    chat_thread.start()

    # 延迟等待 API 启动，打开前端网页
    time.sleep(2)
    open_frontend()

    # 保持主线程运行，直到收到中断信号
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("检测到中断信号，正在终止服务...")
