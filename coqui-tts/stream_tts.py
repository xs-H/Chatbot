import os
import time
import torch
import torchaudio
import threading
import queue
import numpy as np
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts
import pyaudio

# 创建一个队列用于生成和播放之间的通信
audio_queue = queue.Queue(maxsize=20)  # 设置最大队列大小
stop_event = threading.Event()

# 音频生成线程
def generate_audio(text, lang, gpt_cond_latent, speaker_embedding, model):
    try:
        for chunk in model.inference_stream(
            text,
            lang,
            gpt_cond_latent,
            speaker_embedding
        ):
            # 将tensor转换为numpy数组
            audio_data = chunk.cpu().numpy()
            # 将数据放入队列
            audio_queue.put(audio_data)
            # 检查是否应该停止
            if stop_event.is_set():
                break
        # 生成完成后，放入一个None表示结束
        audio_queue.put(None)
    except Exception as e:
        print(f"生成音频时出错: {e}")
        audio_queue.put(None)

# 音频播放线程
def play_audio():
    # 初始化PyAudio
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paFloat32,
                    channels=1,
                    rate=24000,
                    output=True,
                    frames_per_buffer=1024)
    
    # 等待足够的缓冲填充
    buffer_size = 3  # 缓冲数量
    buffer = []
    
    print("缓冲音频中...")
    # 收集初始缓冲
    for _ in range(buffer_size):
        # 等待数据，但设置超时以防死锁
        try:
            data = audio_queue.get(timeout=5)
            if data is None:  # 检查是否结束
                break
            buffer.append(data)
        except queue.Empty:
            print("缓冲超时")
            break
    
    print("开始播放...")
    # 播放缓冲的数据
    for data in buffer:
        stream.write(data.tobytes())
    
    # 继续从队列获取并播放
    while not stop_event.is_set():
        try:
            data = audio_queue.get(timeout=2)
            if data is None:  # 检查是否结束
                break
            stream.write(data.tobytes())
        except queue.Empty:
            print("播放等待数据中...")
            continue
    
    # 清理
    stream.stop_stream()
    stream.close()
    p.terminate()
    print("播放结束")

def main():
    try:
        print("加载模型...")
        config = XttsConfig()
        config.load_json(r"C:\Users\lenovo\AppData\Local\tts\tts_models--multilingual--multi-dataset--xtts_v2\config.json")
        
        # 可以尝试设置较小的chunk_size以加速生成
        model = Xtts.init_from_config(config)
        model.load_checkpoint(config, checkpoint_dir=r"C:\Users\lenovo\AppData\Local\tts\tts_models--multilingual--multi-dataset--xtts_v2", use_deepspeed=False)
        
        # 尝试使用半精度加速
        if torch.cuda.is_available():
            model.cuda()
            # 可以尝试使用半精度加速
            # model.half()
        
        print("计算说话人特征...")
        gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(audio_path=["E:\OneDrive\桌面\入党申请书\zh_combine.mp3"])
        
        text = "你好，我是朱慧。我来自江苏大学。现在我正在测试文本转语音的流式生成效果，希望能够流畅播放，不出现卡顿现象。"
        lang = "zh-cn"
        
        # 创建并启动生成线程
        generator_thread = threading.Thread(
            target=generate_audio, 
            args=(text, lang, gpt_cond_latent, speaker_embedding, model)
        )

        time.sleep(2)
        # 创建并启动播放线程
        player_thread = threading.Thread(target=play_audio)
        
        # 启动线程
        generator_thread.start()
        player_thread.start()
        
        # 等待线程完成
        generator_thread.join()
        player_thread.join()
        
        print("处理完成")
        
    except KeyboardInterrupt:
        print("用户中断")
        stop_event.set()
    except Exception as e:
        print(f"发生错误: {e}")
        stop_event.set()

if __name__ == "__main__":
    main()