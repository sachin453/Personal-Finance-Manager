
from flask import Flask, request, jsonify, render_template_string
from agents.common_tools import tools
from agents.chatbot import ChatbotAgent
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

HTML_FORM = """
<!DOCTYPE html>
<html>
<head>
    <title>Personal Finance Manager - Ask a Model</title>
</head>
<body>
    <h2>Ask a Question</h2>
    <form id="askForm">
        <label>Question:</label><br>
        <input type="text" id="question" name="question" size="50" required><br><br>
        <label>Model:</label>
        <select id="model" name="model">
            <option value="gemini-2.0-flash">Gemini 2.0 Flash</option>
            <option value="gemini-2.0-pro">Gemini 2.0 Pro</option>
            <option value="qwen">Qwen</option>
        </select><br><br>
        <button type="submit">Ask</button>
    </form>
    <h3>Answer:</h3>
    <pre id="answer"></pre>
    <script>
        document.getElementById('askForm').onsubmit = async function(e) {
            e.preventDefault();
            document.getElementById('answer').textContent = "Loading...";
            const question = document.getElementById('question').value;
            const model = document.getElementById('model').value;
            const response = await fetch('/ask', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({question, model})
            });
            const data = await response.json();
            document.getElementById('answer').textContent = data.answer || data.error;
        }
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_FORM)





@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    question = data.get("question", "")
    model = data.get("model", "gemini-2.0-flash")  # Default model

    if not question:
        return jsonify({"error": "No question provided"}), 400
    try:
        answer = "I am fine"
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)