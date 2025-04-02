# cosyvoice安装及使用说明

### 环境准备

*clone and install*

```bash
git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git
# If you failed to clone submodule due to network failures, please run following command until success
cd CosyVoice
# 如果因为网络问题克隆子模块失败了，请运行下面的命令直到成功完整克隆
git submodule update --init --recursive
```

*虚拟环境搭建（这里的pip install -r命令以及后面的模型下载都默认以及cd进入CosyVoice文件夹）* 

```bash
conda create -n cosyvoice -y python=3.10
conda activate cosyvoice
# pynini is required by WeTextProcessing, use conda to install it as it can be executed on all platform.
conda install -y -c conda-forge pynini==2.1.5
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com

# If you encounter sox compatibility issues 这里可以不用管
# ubuntu
sudo apt-get install sox libsox-dev
# centos
sudo yum install sox sox-devel
```

*模型下载*

```python
# SDK模型下载
from modelscope import snapshot_download
snapshot_download('iic/CosyVoice2-0.5B', local_dir='pretrained_models/CosyVoice2-0.5B')
snapshot_download('iic/CosyVoice-300M', local_dir='pretrained_models/CosyVoice-300M')
snapshot_download('iic/CosyVoice-300M-25Hz', local_dir='pretrained_models/CosyVoice-300M-25Hz')
snapshot_download('iic/CosyVoice-300M-SFT', local_dir='pretrained_models/CosyVoice-300M-SFT')
snapshot_download('iic/CosyVoice-300M-Instruct', local_dir='pretrained_models/CosyVoice-300M-Instruct')
snapshot_download('iic/CosyVoice-ttsfrd', local_dir='pretrained_models/CosyVoice-ttsfrd')
```

> 这里的操作是在命令行在该环境下进入python交互，然后逐行输入



*ttsfrd包(在Linux上使用这个可以获得更好的文本归一化表现，如果不安装也没事，就会使用默认的WeTextProcessing)*

```bash
cd pretrained_models/CosyVoice-ttsfrd/ # 这是上面模型下载模块中的最后一行下载的
unzip resource.zip -d .
pip install ttsfrd_dependency-0.1-py3-none-any.whl
pip install ttsfrd-0.4.2-cp310-cp310-linux_x86_64.whl
```



### 使用部分

##### 步骤一

```python
import sys
sys.path.append(r"E:\CosyVoice\third_party\Matcha-TTS")
sys.path.append("E:\CosyVoice")
from cosyvoice.cli.cosyvoice import CosyVoice, CosyVoice2
from cosyvoice.utils.file_utils import load_wav
import torchaudio
import matcha
```

> 第二第三行的目的，是为了python查找包的时候，能找到我们安装的CosyVoice和附属的Matcha-TTS。所以这里的地址需要根据你安装的位置进行灵活更改，不能直接用我这里写的。

##### 步骤二

```python
cosyvoice = CosyVoice2(
    r"E:\CosyVoice\pretrained_models\CosyVoice2-0.5B", 
    load_jit=False, # 是否加载JIT编译加速
    load_trt=False, # 是否加载TensorRT加速
    fp16=False # 设置为True可以减少显存占用，但是效果下降
)
```

> 这里是实例化一个模型对象，注意一般来说这个只需要运行一次，重复运行会导致实例化第二个第三个...从而浪费显存。

##### 步骤三

```python
cosyvoice = CosyVoice2(r"E:\CosyVoice\pretrained_models\CosyVoice2-0.5B", load_jit=False, load_trt=False, fp16=False)

# zero_shot usage 这里只显示语音克隆的使用方法
prompt_speech_16k = load_wav(r"E:\OneDrive\桌面\入党申请书\nz.mp3", 16000)# 这是参考音频

# 这下面有两段文字，第一个是想要生成对应音频的文本。第二个是参考音频的文本，也就是参考音频说了什么。
for i, j in enumerate(cosyvoice.inference_zero_shot('我是哪吒，我想要把你胖揍一顿。我现在在西电读大学。', '拜个屁的师我什么都不学！修炼了出去捧那些白痴的臭脚，还不如在这睡大觉。', prompt_speech_16k, stream=False)):
    torchaudio.save('zero_shot_{}.wav'.format(i), j['tts_speech'], cosyvoice.sample_rate)
```

> 这里注意的是，如果句子比较长，模型会自动分成几段生成。从而产生例如'zero_shot_0''zero_shot_1'这样两个或更多文件。播放的时候需要注意。
>
> 你也可以直接在每一个循环里直接播放该块生成的音频，不用等全部生成完再播放。