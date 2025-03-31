document.addEventListener("DOMContentLoaded", function () {
    // 将input选择器更新为textarea
    const chatInput = document.querySelector(".chat-input textarea");
    const sendButton = document.querySelector(".fa-paper-plane");
    const micButton = document.querySelector(".fa-microphone"); // 选择已有的麦克风图标
    const chatBox = document.querySelector(".chat-box");
    const sidebar = document.querySelector(".sidebar");
    const collapseButton = document.querySelector(".collapse-button");
    const introText = document.querySelector(".intro-text");
    const welcomeText = document.querySelector(".chat-box > p");
    let chatStarted = false;
    let audioPlayer = null;
    
    // ASR API基础URL
    const asrBaseUrl = "https://007.dev.xuan.pub/api/v1";

    // 初始化textarea
    initTextarea();

    // 为现有麦克风按钮添加语音识别功能
    initVoiceRecognition();

    // 侧边栏收起与展开功能
    collapseButton.addEventListener("click", function() {
        sidebar.classList.toggle("collapsed");

        if(sidebar.classList.contains("collapsed")) {
            collapseButton.classList.remove("fa-bars");
            collapseButton.classList.add("fa-chevron-right");
        } else {
            collapseButton.classList.remove("fa-chevron-right");
            collapseButton.classList.add("fa-bars");
        }
    });

    // 新增：初始化textarea并设置自动调整高度
    function initTextarea() {
        // 设置初始高度
        adjustTextareaHeight();
        
        // 监听input事件以调整高度
        chatInput.addEventListener("input", adjustTextareaHeight);
        
        // 监听keydown事件处理Shift+Enter
        chatInput.addEventListener("keydown", function(event) {
            if (event.key === "Enter") {
                if (event.shiftKey) {
                    // Shift+Enter插入换行，不发送消息
                    // 默认行为会插入换行，不需要额外处理
                } else {
                    // 仅Enter键时发送消息并阻止换行
                    event.preventDefault();
                    sendMessage();
                }
            }
        });
    }

    // 为现有麦克风按钮初始化语音识别功能
    function initVoiceRecognition() {
        // 创建录音状态指示元素
        const recordingIndicator = document.createElement("span");
        recordingIndicator.className = "recording-indicator";
        recordingIndicator.textContent = "录音中";
        recordingIndicator.style.display = "none";
        recordingIndicator.style.marginLeft = "10px";
        recordingIndicator.style.color = "red";
        recordingIndicator.style.fontSize = "14px";
        
        // 添加指示器到输入容器
        const inputContainer = document.querySelector(".chat-input");
        inputContainer.appendChild(recordingIndicator);

        // 设置录音相关变量
        let mediaRecorder = null;
        let audioChunks = [];
        let isRecording = false;

        // 为麦克风图标添加点击事件
        micButton.addEventListener("click", function() {
            if (!isRecording) {
                startRecording();
            } else {
                stopRecording();
            }
        });

        // 开始录音函数
        async function startRecording() {
            try {
                // 检查ASR服务状态
                const statusCheck = await checkASRStatus();
                if (!statusCheck) {
                    appendMessage("ai", "语音识别服务不可用，请稍后再试。");
                    return;
                }

                // 请求麦克风权限
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                
                // 创建MediaRecorder实例
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];
                
                // 收集录音数据
                mediaRecorder.addEventListener("dataavailable", event => {
                    audioChunks.push(event.data);
                });
                
                // 录音结束时处理
                mediaRecorder.addEventListener("stop", async () => {
                    // 将录音数据合并为音频blob
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    
                    // 发送到ASR服务进行识别
                    await sendAudioForRecognition(audioBlob);
                    
                    // 停止所有音轨
                    stream.getTracks().forEach(track => track.stop());
                    
                    // 更新UI状态
                    micButton.classList.remove("fa-stop");
                    micButton.classList.add("fa-microphone");
                    recordingIndicator.style.display = "none";
                    isRecording = false;
                });
                
                // 开始录音
                mediaRecorder.start();
                isRecording = true;
                
                // 更新UI状态
                micButton.classList.remove("fa-microphone");
                micButton.classList.add("fa-stop");
                recordingIndicator.style.display = "inline";
                
            } catch (error) {
                console.error("录音错误:", error);
                appendMessage("ai", "无法访问麦克风，请检查浏览器权限设置。");
            }
        }

        // 停止录音函数
        function stopRecording() {
            if (mediaRecorder && isRecording) {
                mediaRecorder.stop();
            }
        }

        // 检查ASR服务状态
        async function checkASRStatus() {
            try {
                // 更新为正确的API端点
                const response = await fetch(`${asrBaseUrl}/asr/status`);
                const data = await response.json();
                return data.status === "ok";
            } catch (error) {
                console.error("无法连接到ASR服务:", error);
                return false;
            }
        }

        // 发送音频进行识别
        async function sendAudioForRecognition(audioBlob) {
            // 创建加载指示器
            const loadingElement = document.createElement("div");
            loadingElement.className = "asr-loading-indicator";
            loadingElement.style.alignSelf = "flex-start";
            loadingElement.style.backgroundColor = "#e0e0e0";
            loadingElement.style.color = "black";
            loadingElement.style.padding = "8px";
            loadingElement.style.borderRadius = "5px";
            loadingElement.style.margin = "10px 0";
            loadingElement.textContent = "正在识别语音";

            if (chatBox.querySelector(".chat-messages")) {
                const messagesContainer = chatBox.querySelector(".chat-messages");
                messagesContainer.appendChild(loadingElement);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }

            try {
                // 创建FormData对象
                const formData = new FormData();
                formData.append("file", audioBlob);
                
                // 更新为正确的API端点
                const response = await fetch(`${asrBaseUrl}/asr/task`, {
                    method: "POST",
                    body: formData
                });
                
                // 检查响应
                if (response.status === 201) {
                    const data = await response.json();
                    await pollASRResult(data.task_id);
                } else {
                    throw new Error("服务器返回错误: " + response.status);
                }
            } catch (error) {
                console.error("语音识别请求错误:", error);
                // 移除加载指示器
                if (chatBox.querySelector(".asr-loading-indicator")) {
                    chatBox.querySelector(".asr-loading-indicator").remove();
                }
                appendMessage("ai", "语音识别失败，请稍后再试。");
            }
        }

        // 轮询ASR结果
        async function pollASRResult(taskId) {
            try {
                // 更新为正确的API端点
                const response = await fetch(`${asrBaseUrl}/asr/task/${taskId}`);
                
                // 如果任务完成
                if (response.status === 200) {
                    const data = await response.json();
                    
                    // 移除加载指示器
                    if (chatBox.querySelector(".asr-loading-indicator")) {
                        chatBox.querySelector(".asr-loading-indicator").remove();
                    }
                    
                    // 检查识别状态
                    if (data.status === "done" && data.text) {
                        // 将识别结果填入输入框
                        chatInput.value = data.text;
                        adjustTextareaHeight();
                    } else {
                        appendMessage("ai", "语音识别失败或未识别到文字。");
                    }
                }
                // 如果任务仍在处理中
                else if (response.status === 202) {
                    // 继续轮询
                    setTimeout(() => pollASRResult(taskId), 1000);
                } 
                // 如果发生错误
                else {
                    throw new Error("获取识别结果失败: " + response.status);
                }
            } catch (error) {
                console.error("轮询ASR结果错误:", error);
                // 移除加载指示器
                if (chatBox.querySelector(".asr-loading-indicator")) {
                    chatBox.querySelector(".asr-loading-indicator").remove();
                }
                appendMessage("ai", "获取语音识别结果失败，请稍后再试。");
            }
        }
    }

    // 新增：自动调整textarea高度的函数
    function adjustTextareaHeight() {
        // 重置高度以获取正确的scrollHeight
        chatInput.style.height = "auto";
        
        // 设置新高度（有最小和最大高度限制）
        const newHeight = Math.min(Math.max(chatInput.scrollHeight, 40), 120);
        chatInput.style.height = newHeight + "px";
    }

    // 创建音频播放器
    function createAudioPlayer() {
        if (!audioPlayer) {
            audioPlayer = document.createElement("audio");
            audioPlayer.controls = true;
            audioPlayer.style.display = "none";
            document.body.appendChild(audioPlayer);
        }
        return audioPlayer;
    }

    function appendMessage(sender, message, audioPath = null) {
        // 第一次发送消息时，移除欢迎文字并调整聊天框大小
        if (!chatStarted) {
            welcomeText.style.display = "none";
            chatBox.classList.add("expanded");
            introText.style.display = "none";
            chatStarted = true;
        }

        const messageElement = document.createElement("div");
        messageElement.style.margin = "10px 0";
        messageElement.style.padding = "8px";
        messageElement.style.borderRadius = "5px";
        messageElement.style.maxWidth = "70%";
        messageElement.style.wordWrap = "break-word";

        if (sender === "user") {
            messageElement.style.alignSelf = "flex-end";
            messageElement.style.backgroundColor = "#007bff";
            messageElement.style.color = "white";
            messageElement.style.textAlign = "right";
        } else {
            messageElement.style.alignSelf = "flex-start";
            messageElement.style.backgroundColor = "#e0e0e0";
            messageElement.style.color = "black";
        }

        messageElement.textContent = message;

        // 如果有音频路径，添加播放按钮
        if (audioPath) {
            const audioButton = document.createElement("button");
            audioButton.innerHTML = '<i class="fas fa-play"></i> 播放语音';
            audioButton.style.marginTop = "5px";
            audioButton.style.border = "none";
            audioButton.style.backgroundColor = "#4CAF50";
            audioButton.style.color = "white";
            audioButton.style.padding = "5px 10px";
            audioButton.style.borderRadius = "3px";
            audioButton.style.cursor = "pointer";

            audioButton.addEventListener("click", function() {
                const player = createAudioPlayer();
                player.src = audioPath;
                player.play();
            });

            const messageContainer = document.createElement("div");
            messageContainer.appendChild(document.createTextNode(message));
            messageContainer.appendChild(document.createElement("br"));
            messageContainer.appendChild(audioButton);

            messageElement.textContent = "";
            messageElement.appendChild(messageContainer);
        }

        if (!chatBox.querySelector(".chat-messages")) {
            const messagesContainer = document.createElement("div");
            messagesContainer.classList.add("chat-messages");
            messagesContainer.style.overflowY = "auto";
            messagesContainer.style.flexGrow = "1";
            messagesContainer.style.maxHeight = "calc(100vh - 200px)"; // 调整为更大的高度
            messagesContainer.style.display = "flex";
            messagesContainer.style.flexDirection = "column";
            chatBox.insertBefore(messagesContainer, chatBox.querySelector(".chat-input"));
        }

        const messagesContainer = chatBox.querySelector(".chat-messages");
        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function sendMessage() {
        const userMessage = chatInput.value.trim();
        if (userMessage === "") return;

        appendMessage("user", userMessage);
        chatInput.value = "";
        
        // 重置textarea高度
        adjustTextareaHeight();

        // Add loading indicator
        const loadingElement = document.createElement("div");
        loadingElement.className = "loading-indicator";
        loadingElement.style.alignSelf = "flex-start";
        loadingElement.style.backgroundColor = "#e0e0e0";
        loadingElement.style.color = "black";
        loadingElement.style.padding = "8px";
        loadingElement.style.borderRadius = "5px";
        loadingElement.style.margin = "10px 0";
        loadingElement.textContent = "思考中";

        if (chatBox.querySelector(".chat-messages")) {
            const messagesContainer = chatBox.querySelector(".chat-messages");
            messagesContainer.appendChild(loadingElement);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        // 调用caht API
        fetch("http://localhost:3000/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: userMessage })
        })
        .then(response => response.json())
        .then(data => {
            // 移除加载指示器
            if (chatBox.querySelector(".loading-indicator")) {
                chatBox.querySelector(".loading-indicator").remove();
            }
    
            if (data.error) {
                appendMessage("ai", "抱歉，出现了错误: " + data.error);
            } else {
                // 关键修改：使用完整的 URL 路径
                const audioPath = data.audio_path 
                    ? `http://localhost:3000${data.audio_path}` 
                    : null;
    
                // 传递完整音频路径
                appendMessage("ai", data.reply, audioPath);
    
                // 如果存在音频自动播放（可选功能）
                if (audioPath) {
                    const player = createAudioPlayer();
                    player.src = audioPath;
                    player.play().catch(e => console.log("Auto-play prevented by browser. User interaction required."));
                }
            }
        })
        .catch(error => {
            console.error("Error:", error);
            appendMessage("ai", "抱歉，出现了错误，请稍后再试。");
        });
    }

    sendButton.addEventListener("click", sendMessage);
    // 不再需要keypress事件监听器，因为已经在initTextarea中处理了Enter键
});