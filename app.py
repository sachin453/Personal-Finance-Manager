from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
from agents.common_tools import tools
from agents.chatbot import ChatbotAgent
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")  # required for session

# Credentials (you can store in .env)
USERNAME = os.getenv("CHATBOT_USER", "admin")
PASSWORD = os.getenv("CHATBOT_PASS", "1234")

my_chatbot = ChatbotAgent(name="FinanceBot", tools=tools)

# --- HTML Templates ---
LOGIN_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Login - FinanceBot</title>
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
        .login-box {
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            width: 320px;
            text-align: center;
        }
        input {
            width: 90%;
            padding: 10px;
            margin: 8px 0;
            border: 1px solid #ccc;
            border-radius: 8px;
        }
        button {
            width: 95%;
            padding: 10px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
        }
        button:hover { background: #0056b3; }
        .error { color: red; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>FinanceBot Login</h2>
        <form method="POST" action="/login">
            <input type="text" name="username" placeholder="Username" required><br>
            <input type="password" name="password" placeholder="Password" required><br>
            <button type="submit">Login</button>
        </form>
        {% if error %}
            <p class="error">{{ error }}</p>
        {% endif %}
    </div>
</body>
</html>
"""

CHAT_PAGE = """
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
            position: relative;
        }
        #logout-btn {
            position: absolute;
            top: 10px;
            right: 10px;
            background: #dc3545;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
        }
        #chat-box {
            flex: 1;
            padding: 16px;
            overflow-y: auto;
            border-bottom: 1px solid #ddd;
            margin-top: 40px;
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
        button.send {
            margin-left: 8px;
            padding: 10px 16px;
            border: none;
            background: #007bff;
            color: white;
            border-radius: 8px;
            cursor: pointer;
        }
        button.send:hover {
            background: #0056b3;
        }
    </style>
</head>
<body>
    <div id="chat-container">
        <button id="logout-btn" onclick="window.location.href='/logout'">Logout</button>
        <div id="chat-box"></div>
        <div id="input-area">
            <input type="text" id="question" placeholder="Ask something..." autocomplete="off" />
            <button class="send" onclick="sendMessage()">Send</button>
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

        input.addEventListener('keydown', e => {
            if (e.key === 'Enter') sendMessage();
        });
    </script>
</body>
</html>
"""

# --- Routes ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == USERNAME and password == PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("home"))
        else:
            return render_template_string(LOGIN_PAGE, error="Invalid credentials.")
    return render_template_string(LOGIN_PAGE)

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))

@app.route("/")
def home():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template_string(CHAT_PAGE)

@app.route("/ask", methods=["POST"])
def ask():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    question = data.get("question", "")
    if not question:
        return jsonify({"error": "No question provided"}), 400

    try:
        answer = my_chatbot.dialogue(question)
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
