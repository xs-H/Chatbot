import sys
from pathlib import  Path


# 为了python查找包的时候，能找到我们安装的CosyVoice和附属的Matcha-TTS。因此这里的地址需要根据安装的位置进行更改
# 获取参考音频文件路径
current_file = Path(__file__).resolve()
# 项目根目录
root = current_file.parents[0]  # cosy_voice.py -> tts_backend
dir_path = r".\COSYVoice"
sys.path.append(dir_path + r"/third_party/Matcha-TTS")
sys.path.append(dir_path)

from COSYVoice.cosyvoice.cli.cosyvoice import CosyVoice2
from COSYVoice.cosyvoice.utils.file_utils import load_wav
from pathlib import Path
import torchaudio

# 获取 cosy_voice.py 文件当前路径
current_file = Path(__file__).resolve()
# 项目根目录
project_root = current_file.parents[2]  # cosy_voice.py -> tts_backend -> backend -> [chatbot-v1]
# 构建目标 mp3 文件的路径
mp3_path = project_root / 'resource' / 'voice' / "NeZha''.mp3"  # 参考的音频文件

if __name__=="__main__":

    # 实例化一个模型对象，注意该部分只需要运行一次，重复运行会导致浪费显存
    cosyvoice = CosyVoice2(
        dir_path + r"\pretrained_models\CosyVoice2-0.5B",
        load_jit=False,  # 是否加载JIT编译加速
        load_trt=False,  # 是否加载TensorRT加速
        fp16=False  # 设置为True可以减少显存占用，但是效果下降
    )

    # 这里注意的是，如果句子比较长，模型会自动分成几段生成。从而产生例如'zero_shot_0''zero_shot_1'这样两个或更多文件。播放的时候需要注意。
    # 你也可以直接在每一个循环里直接播放该块生成的音频，不用等全部生成完再播放。
    # cosyvoice = CosyVoice2(dir_path + r"\pretrained_models\CosyVoice2-0.5B", load_jit=False, load_trt=False, fp16=False)

    # zero_shot usage 这里只显示语音克隆的使用方法
    prompt_speech_16k = load_wav(mp3_path, 16000)  # 参考音频

    # 这下面有两段文字，第一个是想要生成对应音频的文本。第二个是参考音频的文本，也就是参考音频说了什么。
    for i, j in enumerate(cosyvoice.inference_zero_shot('我是哪吒，我想要把你胖揍一顿。我现在在西电读大学。', # 生成内容
                                                        '拜个屁的师我什么都不学！修炼了出去捧那些白痴的臭脚，还不如在这睡大觉。', # 参考的音频内容
                                                        prompt_speech_16k, stream=False)):
        torchaudio.save('./example_audio/infer_{}.wav'.format(i), j['tts_speech'], cosyvoice.sample_rate)