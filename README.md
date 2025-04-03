# Chatbot——tts
## v1
### 增添内容

1.后端API集成:
将wav_generate.py中的TTS功能集成到api.py中
添加了音频文件生成和提供下载的API端点
对大模型回复的文本进行语音合成，并保存为WAV文件

2.前端交互:
添加了音频播放功能
在聊天消息中添加了"播放语音"按钮
创建了隐藏的音频播放器来播放生成的语音

### 工作流程
- 用户在前端界面输入问题并发送
- 前端发送请求到后端API
- API将用户问题传递给大模型并获取文本回复
- API使用TTS模型将文本回复转换为语音并保存为WAV文件
- API返回文本回复和音频文件路径给前端
- 前端显示文本回复并提供音频播放按钮
- 用户可以点击按钮播放AI回复的语音

### 如何运行
具体内容请参照tts分支，chat.py以及rag.py所需环境请参照主分支

## v2
### 后端更新
- 加入了新的api：tts_api, chat_api
- 换用模型后加入了cosy_voice.py

### 如何运行
具体内容参照tts分支中的cosyvoice部分
