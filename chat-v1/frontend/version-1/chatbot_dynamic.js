document.addEventListener("DOMContentLoaded", function () {
    const chatInput = document.querySelector(".chat-input input");
    const sendButton = document.querySelector(".fa-paper-plane");
    const chatBox = document.querySelector(".chat-box");
    const newChatButton = document.querySelector(".button:first-of-type");

    function appendMessage(sender, message) {
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

        if (!chatBox.querySelector(".chat-messages")) {
            const messagesContainer = document.createElement("div");
            messagesContainer.classList.add("chat-messages");
            messagesContainer.style.overflowY = "auto";
            messagesContainer.style.flexGrow = "1";
            messagesContainer.style.maxHeight = "25vh";
            messagesContainer.style.display = "flex";
            messagesContainer.style.flexDirection = "column";
            chatBox.appendChild(messagesContainer);
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
                appendMessage("ai", data.reply);
            }
        })
        .catch(error => {
            console.error("Error:", error);
            // Remove loading indicator
            if (chatBox.querySelector(".loading-indicator")) {
                chatBox.querySelector(".loading-indicator").remove();
            }
            appendMessage("ai", "抱歉，出现了错误，请稍后再试。");
        });
    }

    // Add reset conversation functionality
    function resetConversation() {
        // Clear UI
        if (chatBox.querySelector(".chat-messages")) {
            chatBox.querySelector(".chat-messages").innerHTML = "";
        }

        // Reset backend conversation history
        fetch("http://localhost:3000/api/reset", {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        })
        .then(response => response.json())
        .then(data => {
            console.log("Conversation reset:", data);
            // Optional: Show a notification that conversation was reset
            if (!chatBox.querySelector(".chat-messages")) {
                const messagesContainer = document.createElement("div");
                messagesContainer.classList.add("chat-messages");
                messagesContainer.style.overflowY = "auto";
                messagesContainer.style.flexGrow = "1";
                messagesContainer.style.maxHeight = "25vh";
                messagesContainer.style.display = "flex";
                messagesContainer.style.flexDirection = "column";
                chatBox.appendChild(messagesContainer);
            }
            appendMessage("ai", "开始新对话！");
        })
        .catch(error => {
            console.error("Error resetting conversation:", error);
        });
    }

    sendButton.addEventListener("click", sendMessage);
    chatInput.addEventListener("keypress", function (event) {
        if (event.key === "Enter") {
            sendMessage();
        }
    });

    // Add event listener for new chat button
    if (newChatButton) {
        newChatButton.addEventListener("click", resetConversation);
    }
});