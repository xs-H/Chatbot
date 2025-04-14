from snownlp import SnowNLP
import torchaudio
from pathlib import  Path
import os
import sys

# 系统路径配置
dir_path = "./COSYVoice"
sys.path.append(dir_path)
sys.path.append(dir_path + r"/third_party/Matcha-TTS")
# 获取 cosy_voice.py 文件当前路径
current_file = Path(__file__).resolve()
# 项目根目录
project_root = current_file.parents[2]  # cosy_voice.py -> tts_backend -> backend -> [chatbot-v1]

# 测试文本
text = '你好,罗夕阳我能和你做朋友吗？'
# SnowNLP 类实例化
s = SnowNLP(text)
sen = s.sentiments
# CosyVoice 类实例化
from COSYVoice.cosyvoice.cli.cosyvoice import CosyVoice2
from COSYVoice.cosyvoice.utils.file_utils import load_wav


cosyvoice = CosyVoice2(
    dir_path + "/pretrained_models/CosyVoice2-0.5B", # 路径格式要求
    load_jit=False,  # 是否加载JIT编译加速
    load_trt=False,  # 是否加载TensorRT加速
    fp16=False  # 设置为True可以减少显存占用，但是效果下降
)

def use_happy():
    reference_audio = project_root / 'resource' / 'voice' / "NZ_happy.mp3"  # 参考的音频文件
    reference_text = '你会来吧，因为你是我唯一的朋友啊。一言为定，我等你哦！'
    return reference_audio, reference_text

def use_angry():
    reference_audio = project_root / 'resource' / 'voice' / "NZ_angry.mp3"  # 参考的音频文件
    reference_text = '拜个屁的师我什么都不学！修炼了出去捧那些白痴的臭脚，还不如在这睡大觉。'
    return reference_audio, reference_text

actions = {
    (lambda x:x<0.5) : use_angry(),
    (lambda x:x>=0.5) : use_happy()
}

for condition, action in actions.items():
    if condition(sen):
        reference_audio, reference_text = action
        break

prompt_speech_16k = load_wav(reference_audio, 16000)
for i, j in enumerate(cosyvoice.inference_zero_shot(text, reference_text, prompt_speech_16k, stream=False)):
    torchaudio.save('./example_audio/emotion_{}.wav'.format(i), j['tts_speech'], cosyvoice.sample_rate)
