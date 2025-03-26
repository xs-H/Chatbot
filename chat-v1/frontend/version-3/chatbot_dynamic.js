document.addEventListener("DOMContentLoaded", function () {
    // 将input选择器更新为textarea
    const chatInput = document.querySelector(".chat-input textarea");
    const sendButton = document.querySelector(".fa-paper-plane");
    const chatBox = document.querySelector(".chat-box");
    const sidebar = document.querySelector(".sidebar");
    const collapseButton = document.querySelector(".collapse-button");
    const introText = document.querySelector(".intro-text");
    const welcomeText = document.querySelector(".chat-box > p");
    let chatStarted = false;
    let audioPlayer = null;

    // 初始化textarea
    initTextarea();

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
        loadingElement.textContent = "思考中...";

        if (chatBox.querySelector(".chat-messages")) {
            const messagesContainer = chatBox.querySelector(".chat-messages");
            messagesContainer.appendChild(loadingElement);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        // 调用后端 API
        fetch("http://localhost:3000/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: userMessage })
        })
        .then(response => response.json())
        .then(data => {
            // Remove loading indicator
            if (chatBox.querySelector(".loading-indicator")) {
                chatBox.querySelector(".loading-indicator").remove();
            }

            if (data.error) {
                appendMessage("ai", "抱歉，出现了错误: " + data.error);
            } else {
                // 传递音频路径给 appendMessage 函数
                appendMessage("ai", data.reply, data.audio_path);

                // 如果存在音频自动播放（可选功能）
                if (data.audio_path) {
                    const player = createAudioPlayer();
                    player.src = data.audio_path;
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