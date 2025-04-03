import sys

# 为了python查找包的时候，能找到我们安装的CosyVoice和附属的Matcha-TTS。因此这里的地址需要根据安装的位置进行更改
sys.path.append(r"E:\CosyVoice\third_party\Matcha-TTS")
sys.path.append("E:\CosyVoice")

from cosyvoice.cli.cosyvoice import CosyVoice, CosyVoice2
from cosyvoice.utils.file_utils import load_wav
import torchaudio
import matcha

# 这里是实例化一个模型对象，注意该部分只需要运行一次，重复运行会导致浪费显存
cosyvoice = CosyVoice2(
    r"E:\CosyVoice\pretrained_models\CosyVoice2-0.5B",
    load_jit=False, # 是否加载JIT编译加速
    load_trt=False, # 是否加载TensorRT加速
    fp16=False # 设置为True可以减少显存占用，但是效果下降
)

# 这里注意的是，如果句子比较长，模型会自动分成几段生成。从而产生例如'zero_shot_0''zero_shot_1'这样两个或更多文件。播放的时候需要注意。
# 你也可以直接在每一个循环里直接播放该块生成的音频，不用等全部生成完再播放。
cosyvoice = CosyVoice2(r"E:\CosyVoice\pretrained_models\CosyVoice2-0.5B", load_jit=False, load_trt=False, fp16=False)

# zero_shot usage 这里只显示语音克隆的使用方法
prompt_speech_16k = load_wav(r"E:\OneDrive\桌面\入党申请书\nz.mp3", 16000)# 这是参考音频

# 这下面有两段文字，第一个是想要生成对应音频的文本。第二个是参考音频的文本，也就是参考音频说了什么。
for i, j in enumerate(cosyvoice.inference_zero_shot('我是哪吒，我想要把你胖揍一顿。我现在在西电读大学。', '拜个屁的师我什么都不学！修炼了出去捧那些白痴的臭脚，还不如在这睡大觉。', prompt_speech_16k, stream=False)):
    torchaudio.save('zero_shot_{}.wav'.format(i), j['tts_speech'], cosyvoice.sample_rate)