# ChatBot（心语智友）

## 一、环境配置与项目安装

### 0. 项目克隆

- Git
    
    克隆项目文件中不包含模型文件与CosyVoice项目文件，我们并未修改CosyVoice项目文件内容。
    
    ```bash
    git clone https://github.com/xs-H/Chatbot.git
    ```
    

### 1. 创建虚拟环境

- 版本控制：python==3.10
    
    ```bash
    conda create -n CHATBOT python==3.10
    conda activate CHATBOT
    ```
    

### 2. 安装 torch 、torchvision (0.20.1+cu124)、torchaudio

- 版本控制：torch ≤ 2.5.1+cu124，否则无法安装适配的torchvision
    
    ```bash
    # 快捷安装 使用 WHL 文件
    pip install torch-2.5.1+cu124-cp310-cp310-win_arm64.whl
    # torchvision torchaudio 安装
    pip install torchvision==0.20.1+cu124 torchaudio==2.5.1+cu124 --index-url https://download.pytorch.org/whl/cu124 
    ```
    

### 3. 安装 pynini 、Cython

- 版本控制：pynini==2.1.5，Cython==3.0.12
    
    ```bash
    conda intall -y -c conda-forge pynini==2.1.5
    
    pip install Cython==3.0.12
    ```
    

### 4. 安装 其他依赖项

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
    
- onnxruntime-gpu 版本需要与cuda与cuDNN兼容（环境中不可同时存在onnxruntime-gpu和onnxruntime）
    
    ```bash
    pip install onnxruntime-gpu==1.18.0
    ```
    
- 系统路径添加（TTS-Cosyvoice）否则无法成功导入CosyVoice类：
    
    ```python
    import sys
    sys.path.append('./COSYVoice')
    sys.path.append('./COSYVoice/third_party/Matcha-TTS/matcha')
    ```
    

## 二、模型文件获取与配置

### 1. LLM

- 使用 qwen-7B 微调（Llama-Factory）模型，模型文件列表如下：（.safetensors）
    
    ```bash
    # 模型文件大小 14.1GB
    QWEN2.5-7B
        added_tokens.json
        config.json
        generation_config.json
        merges.txt
        model-00001-of-00003.safetensors
        model-00002-of-00003.safetensors
        model-00003-of-00003.safetensors
        model.safetensors.index.json
        Modelfile
        special_tokens_map.json
        tokenizer.json
        tokenizer_config.json
        vocab.json
    ```
    
- 1.  基于模型文件直接生成 Ollama 模型
    
    ```bash
    # Ollama 环境变量配置
    OLLAMA_MODELS -> D:\Model
    OLLAMA_POST -> 11434
    # Modelfile 文件存放于上述模型文件目录下 可直接编辑修改提示词和模型参数
    ollama create qwen-role-lora -f to/path/Modelfile
    # 测试
    ollama run qwen-role-lora
    ```
    
- 2. 使用 llama.cpp 转化模型格式（可选）
    
    ```bash
    # 克隆 llama.cpp 项目
    git clone https://github.com/ggerganov/llama.cpp
    cd llama.cpp
    # 配置项目环境
    conda create -n 环境名 
    conda activate 环境名
    pip install -r requirements.txt  # 安装依赖
    make  # 编译 llama.cpp
    
    # 转化
    python convert.py \
        --input "model-00001-of-00003.safetensors" \  # 只需指定第一个分片
        --output "output-model.gguf" \  # 输出的 GGUF 文件名
        --vocab-dir "to/path/tokenizer" \  # 如果 tokenizer文件 与 safetensors文件不在同一目录，则需指定
        --model-type "llama"  # 模型架构（如 llama, gpt-neox, starcoder 等）
    # 量化（该功能不一定可用）
    ./quantize model.fp16.gguf model.q4_k_m.gguf Q4_K_M
    # 创建
    ollama create qwen-role-lora -f to/path/Modelfile
    ```
    
- 3. 使用Ollama对模型文件进行量化（可选 · 建议）
    
    参考官方文档：（https://github.com/ollama/ollama/blob/main/docs/import.md）
    
    ```bash
    # 创建 Modelfile 文件（或修改原 Modelfile）
    FROM path/to/模型文件名.gguf
    # ollama 量化指令
    ollama create --quantize q4_K_M qwen-role-Q4 -f path/to/Modelfile
    ollama create --quantize q8_0 qwen-role-Q8 -f path/to/Modelfile
    ```
    

### 2. TTS（https://github.com/FunAudioLLM/CosyVoice）

- 采用 cosyvoice2-0.5B，模型文件列表如下：
    
    ```bash
    COSYVOICE2-0.5B
    |   .msc
    |   .mv
    |   campplus.onnx
    |   configuration.json
    |   cosyvoice2.yaml
    |   flow.cache.pt
    |   flow.decoder.estimator.fp32.onnx
    |   flow.encoder.fp16.zip
    |   flow.encoder.fp32.zip
    |   flow.pt
    |   hift.pt
    |   llm.pt
    |   README.md
    |   speech_tokenizer_v2.on
    |   
    +---._____temp
    +---asset
    |       dingding.png
    |       
    \---CosyVoice-BlankEN
            config.json
            generation_config.json
            merges.txt
            model.safetensors
            tokenizer_config.json
            vocab.json
    ```
    
- 模型文件获取
    
    ```bash
    # SDK模型下载
    from modelscope import snapshot_download
    snapshot_download('iic/CosyVoice2-0.5B', local_dir='pretrained_models/CosyVoice2-0.5B')
    snapshot_download('iic/CosyVoice-300M', local_dir='pretrained_models/CosyVoice-300M')
    snapshot_download('iic/CosyVoice-300M-SFT', local_dir='pretrained_models/CosyVoice-300M-SFT')
    snapshot_download('iic/CosyVoice-300M-Instruct', local_dir='pretrained_models/CosyVoice-300M-Instruct')
    snapshot_download('iic/CosyVoice-ttsfrd', local_dir='pretrained_models/CosyVoice-ttsfrd')
    ```
    

## 三、启动项目（网页版）

### 1. start LLM and TTS

- 运行 start.py
    
    ```bash
    cd to/path/Chatbot
    python start.py
    ```
    

### 2. start ASR（可选）

- Docker
    
    ```bash
    cd backend/asr_backend/docker
    docker compose up -d
    docker compose logs -f
    ```
    

## 四、网页功能介绍

- 示例：哪吒
    
    ![屏幕截图 2025-04-17 101127.png](attachment:bbac353d-49e4-4759-aabf-700aea9e82c8:屏幕截图_2025-04-17_101127.png)
    
1. 语音输入：自动语音识别（ASR）功能已完成封装，若需要使用该功能，须运行Docker镜像。用户可使用ASR功能进行多语种输入（点击右下角-麦克风图标，完成语音输入后点击终止图标，即可自动实现语音转文本）
2. 聊天对话：与常见LLM相同，模型支持多语种对话，用户可按照resource/database目录下的角色知识库构建示例自行构建任意角色的文本资料，注意：需要删除原知识库文件，否则无法自动构建知识库。修改backend/chat_backend/chat.py中的如下内容，可更换语言模型，模型名需要与Ollama list中的模型列表名保持一致。
    
    ```bash
    # self.model_name = 'qwen-role-lora:latest' # FP16 16GB 显存
    # self.model_name = 'qwen-role-Q5:latest' # Q5_K_M 6GB 显存
    self.model_name = 'qwen-role-Q8:latest' # Q8_0 10GB 显存
    ```
    
3. 语音合成：生成回复内容后，自动完成语音合成，并播放合成语音，合成语音高度拟合《哪吒：魔童降世》中的角色原声。用户可替换resource/voice目录下的角色参考音频，并修改tts_api中的参考音频路径与参考文本。
