import subprocess
import time
import os

# 获取当前脚本所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 定义 API 脚本和日志路径
apis = {
    "chat_api": {
        "script": os.path.join(BASE_DIR, "chat_backend", "chat_api.py"),
        "log": os.path.join(BASE_DIR, "logs", "chat_api.log"),
        "cwd": os.path.join(BASE_DIR, "chat_backend"),  # 设定运行目录
    },
    "tts_api": {
        "script": os.path.join(BASE_DIR, "tts_backend", "tts_api.py"),
        "log": os.path.join(BASE_DIR, "logs", "tts_api.log"),
        "cwd": os.path.join(BASE_DIR, "tts_backend"),  # 设定运行目录
    },
}

# 创建日志目录
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)

# 存储 API 进程
processes = {}

# 启动 API
for name, config in apis.items():
    with open(config["log"], "w") as log_file:
        processes[name] = subprocess.Popen(
            ["python", config["script"]],
            cwd=config["cwd"],  # 设定 API 运行目录，防止 import 失败
            stdout=log_file,
            stderr=log_file,
        )
    print(f"{name} 已启动，日志记录在 {config['log']}")

try:
    while True:
        time.sleep(10)
        for name, process in processes.items():
            if process.poll() is not None:  # 如果进程崩溃
                print(f"⚠️ {name} 进程已退出，正在重启...")
                with open(apis[name]["log"], "a") as log_file:
                    processes[name] = subprocess.Popen(
                        ["python", apis[name]["script"]],
                        cwd=apis[name]["cwd"],
                        stdout=log_file,
                        stderr=log_file,
                    )
                print(f"✅ {name} 已重启，日志继续记录在 {apis[name]['log']}")
except KeyboardInterrupt:
    print("\n⏳ 检测到退出信号，正在关闭所有进程...")
    for process in processes.values():
        process.terminate()
    print("🚀 所有 API 已停止")