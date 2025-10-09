from flask import Flask, request, jsonify, render_template_string
from agents.common_tools import tools
from agents.chatbot import ChatbotAgent
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# --- Chatbot setup ---
my_chatbot = ChatbotAgent(name="FinanceBot", tools=tools)

# --- Frontend HTML ---
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>FinanceBot - Personal Finance Assistant</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f4f6f8;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        #chat-container {
            width: 480px;
            height: 600px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
        }
        #chat-box {
            flex: 1;
            padding: 16px;
            overflow-y: auto;
            border-bottom: 1px solid #ddd;
        }
        .message {
            margin: 8px 0;
            padding: 10px 14px;
            border-radius: 10px;
            max-width: 80%;
            line-height: 1.4;
        }
        .user {
            background: #DCF8C6;
            align-self: flex-end;
        }
        .bot {
            background: #f1f0f0;
            align-self: flex-start;
        }
        #input-area {
            display: flex;
            padding: 10px;
        }
        #question {
            flex: 1;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 8px;
            outline: none;
        }
        button {
            margin-left: 8px;
            padding: 10px 16px;
            border: none;
            background: #007bff;
            color: white;
            border-radius: 8px;
            cursor: pointer;
        }
        button:hover {
            background: #0056b3;
        }
    </style>
</head>
<body>
    <div id="chat-container">
        <div id="chat-box"></div>
        <div id="input-area">
            <input type="text" id="question" placeholder="Ask something..." autocomplete="off" />
            <button onclick="sendMessage()">Send</button>
        </div>
    </div>

    <script>
        const chatBox = document.getElementById('chat-box');
        const input = document.getElementById('question');

        function appendMessage(text, sender) {
            const msg = document.createElement('div');
            msg.classList.add('message', sender);
            msg.textContent = text;
            chatBox.appendChild(msg);
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        async function sendMessage() {
            const question = input.value.trim();
            if (!question) return;
            appendMessage(question, 'user');
            input.value = '';
            appendMessage('Typing...', 'bot');

            const response = await fetch('/ask', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ question })
            });

            const data = await response.json();
            chatBox.lastChild.remove(); // remove "Typing..."
            appendMessage(data.answer || data.error || "Error", 'bot');
        }

        // Press Enter to send
        input.addEventListener('keydown', e => {
            if (e.key === 'Enter') sendMessage();
        });
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_PAGE)

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    question = data.get("question", "")
    print(f"Received question: {question}")

    if not question:
        return jsonify({"error": "No question provided"}), 400

    try:
        answer = my_chatbot.dialogue(question)
        print(f"Answer generated: {answer}")
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
