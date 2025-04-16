# frontend_v2
- 新增了头像，后续加入图片即可
- 开始对话后聊天框自动覆盖全屏
- 左侧边栏可以展开与回收

## 接入语音成功
- 大模型回复后可自动播放语音
- 注意：新的js文件"add files via upload"直接复制更改即可，其他内容不做改变

# frontend_v3
更改tts模型后，更改了新的js文件，调用新的api：tts_api,chat_api，其他内容不做改变

# frontend_v4
- **优化css**
- **成功加入tts与asr**
### 安装 其他依赖项

- 版本控制：requirements.txt
    
    ```bash
    pip install -r to/path/requirements.txt
    ```
    

### 5. 注意事项

- transformers 版本过高导致 使用 HuggingFaceEmbendings 拉取编码模型报错：**Should have a `model_type` key in its config.json……**
    
    ```bash
    # 解决方式 下载模型至本地 4GB
    cd chatbot-v1/backend/chat_backend
    git lfs install
    git clone https://huggingface.co/GanymedeNil/text2vec-large-chinese
    # 在 rag.py 中修改 
    MODEL_NAME = "./text2vec-large-chinese"
    self.model = HuggingFaceEmbeddings(model_name=MODEL_NAME)
    ```
    
- CosyVoice项目克隆与模型文件下载，项目克隆完成后为项目进行更名“CosyVoice”→”COSYVoice”，避免调用错误
    
    ```bash
    cd chatbot-v1/backend/tts_backend
    git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git
    git submodule update --init --recursive
    # 在 CHATBOT 环境下启动 python
    输入 python 并回车
    >>from modelscope import snapshot_download
    # SDK 模型文件下载（about 30min）
    snapshot_download('iic/CosyVoice2-0.5B', local_dir='pretrained_models/CosyVoice2-0.5B')
    snapshot_download('iic/CosyVoice-300M', local_dir='pretrained_models/CosyVoice-300M')
    snapshot_download('iic/CosyVoice-300M-25Hz', local_dir='pretrained_models/CosyVoice-300M-25Hz')
    snapshot_download('iic/CosyVoice-300M-SFT', local_dir='pretrained_models/CosyVoice-300M-SFT')
    snapshot_download('iic/CosyVoice-300M-Instruct', local_dir='pretrained_models/CosyVoice-300M-Instruct')
    snapshot_download('iic/CosyVoice-ttsfrd', local_dir='pretrained_models/CosyVoice-ttsfrd')
    ```
    
- faiss 包安装，gpu 版本仅支持 linux，windows系统下直接安装 cpu 版本
    
    ```bash
    # linux cuda=12.x
    pip install faiss-gpu==1.7.3
    # windows
    pip install faiss-cpu
    ```
