function toggleChatbot() {
            const chatbot = document.getElementById('chatbot');
            chatbot.classList.toggle('visible');
        }

function sendPrompt() {
            const input = document.getElementById("userInput");
            const prompt = input.value.trim();
            if (!prompt) return;

            const chatBox = document.getElementById("chatBox");

            // Add user message
            const userMsg = document.createElement("div");
            userMsg.className = "chat-message user";
            userMsg.innerText = prompt;
            chatBox.appendChild(userMsg);

            input.value = "";

            // Show loading...
            const botMsg = document.createElement("div");
            botMsg.className = "chat-message bot";
            botMsg.innerText = "Generating image...";
            chatBox.appendChild(botMsg);

            fetch("/generate_image", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ prompt })
            })
            .then(response => response.json())
            .then(data => {
                botMsg.innerHTML = `<img src="${data.image_url}" alt="Generated Image" class="generated-image">`;
                chatBox.scrollTop = chatBox.scrollHeight;
            });
        }
