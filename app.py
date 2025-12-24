from flask import Flask, request, jsonify, render_template_string
from agents.common_tools import tools
from agents.database_agent import sql_tools
from agents.chatbot import ChatbotAgent
from dotenv import load_dotenv
import os
import psycopg2
from psycopg2 import OperationalError, InterfaceError, DatabaseError
import calendar
import random
import datetime

load_dotenv()

app = Flask(__name__)

# --- Database connection ---
DB_URL = os.getenv("DATABASE_URL")  

def get_db_connection():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        return conn, cur
    except Exception as e:
        print("Database connection failed:", e)
        return None, None

conn, cur = get_db_connection()

if conn and cur:
    try:
        # Ensure table exists
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """)
        conn.commit()
    except Exception as e:
        print("Error ensuring users table exists:", e)
else:
    print("Warning: Database is not connected. App will not function properly.")

my_chatbot = ChatbotAgent(name="FinanceBot", tools=tools + sql_tools)


# --- HTML Templates ---
LOGIN_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Login - FinanceBot</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f4f6f8; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-box { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); width: 320px; text-align: center; }
        input { width: 90%; padding: 10px; margin: 8px 0; border: 1px solid #ccc; border-radius: 8px; }
        button { width:95%; padding:10px; background:#007bff; color:white; border:none; border-radius:8px; cursor:pointer; }
        button:hover { background:#0056b3; }
        .error { color:red; }
    </style>
</head>
<body class="dark">
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
        <p>Don't have an account? <a href="/signup">Sign Up</a></p>
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
        html, body { height: 100%; margin: 0; padding: 0; }
        body { font-family: Arial, sans-serif; background: #f4f6f8; height: 100vh; margin: 0; transition: background 0.3s, color 0.3s; }
        #main-layout { display: flex; height: 100vh; width: 100vw; }
        #left-panel { flex: 1 1 0%; min-width: 280px; background: #e9ecef; padding: 32px 24px; box-sizing: border-box; border-right: 1px solid #ddd; display: flex; flex-direction: column; }
        #left-panel h2 { margin-top: 0; }
        #left-panel .placeholder { color: #888; font-size: 1.1em; margin-top: 40px; text-align: center; }
        #chat-container { width: 480px; min-width: 340px; max-width: 100vw; height: 100vh; background: white; border-radius: 0 12px 12px 0; box-shadow: -4px 0 12px rgba(0,0,0,0.07); display: flex; flex-direction: column; position: relative; transition: background 0.3s, color 0.3s; }
        #chat-box { flex: 1; padding: 16px; overflow-y: auto; border-bottom: 1px solid #ddd; margin-top: 40px; }
        .message { margin: 8px 0; padding: 10px 14px; border-radius: 10px; max-width: 80%; line-height: 1.4; }
        .user { background: #DCF8C6; align-self: flex-end; }
        .bot { background: #f1f0f0; align-self: flex-start; }
        #input-area { display: flex; padding: 10px; }
        #question { flex: 1; padding: 10px; border: 1px solid #ccc; border-radius: 8px; outline: none; }
        button.send { margin-left: 8px; padding: 10px 16px; border: none; background: #007bff; color: white; border-radius: 8px; cursor: pointer; }
        button.send:hover { background: #0056b3; }
        #theme-btn { position: absolute; top: 10px; left: 10px; background: #222; color: #fff; border: none; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: 14px; z-index: 2; }
        #theme-btn.light { background: #f4f6f8; color: #222; border: 1px solid #ccc; }
        body.dark { background: #181a1b !important; color: #e0e0e0; }
        body.dark #left-panel { background: #23272b; color: #e0e0e0; border-right: 1px solid #333; }
        body.dark #chat-container { background: #181a1b; color: #e0e0e0; }
        body.dark .message.user { background: #2e7d32; color: #fff; }
        body.dark .message.bot { background: #33373a; color: #e0e0e0; }
        body.dark #input-area { background: #181a1b; }
        body.dark #question { background: #23272b; color: #e0e0e0; border: 1px solid #444; }
        body.dark button.send { background: #1565c0; }
        body.dark button.send:hover { background: #0d47a1; }
        @media (max-width: 900px) {
            #main-layout { flex-direction: column; }
            #left-panel { width: 100%; min-width: 0; border-right: none; border-bottom: 1px solid #ddd; border-radius: 0; }
            #chat-container { max-width: 100vw; min-width: 0; border-radius: 0 0 12px 12px; }
        }
    </style>
</head>
<body class="dark">
    <div id="main-layout">
        <div id="left-panel">
            <h2>Finance Data</h2>
            <div style="height: 140px;">
                <canvas id="expenseChart" style="width:100%;height:100%;"></canvas>
            </div>
            <div style="margin-top:10px; display:flex; gap:8px; align-items:center;">
                <select id="monthSelect" style="flex:1; padding:6px; font-size:13px"></select>
                <button id="monthBtn" style="padding:4px 6px; font-size:12px; height:28px;">Show</button>
            </div>
            <div style="height:120px; margin-top:8px; width:25%; align-self:flex-start;">
                <canvas id="categoryChart" style="width:100%;height:100%;"></canvas>
            </div>
        </div>
        <div id="chat-container">
            <button id="theme-btn" onclick="toggleTheme()">Light Theme</button>
            <div id="chat-box"></div>
            <div id="input-area">
                <input type="text" id="question" placeholder="Ask something..." autocomplete="off" />
                <button class="send" onclick="sendMessage()">Send</button>
            </div>
        </div>
    </div>
    <script>
        const chatBox = document.getElementById('chat-box');
        const input = document.getElementById('question');
        const themeBtn = document.getElementById('theme-btn');
        let darkMode = true;
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
        function toggleTheme() {
            darkMode = !darkMode;
            document.body.classList.toggle('dark', darkMode);
            themeBtn.textContent = darkMode ? 'Light Theme' : 'Dark Theme';
            themeBtn.classList.toggle('light', !darkMode);
            try{
                // re-render charts so they adapt to theme color changes
                const sel = document.getElementById('monthSelect');
                if(typeof renderExpensesChart === 'function') renderExpensesChart();
                if(typeof renderCategoryChart === 'function' && sel) renderCategoryChart(sel.value);
            }catch(e){console.warn('Chart re-render failed', e)}
        }
    </script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        let expenseChartInstance = null;
        let categoryChartInstance = null;

        function populateMonthSelector(labels){
            const sel = document.getElementById('monthSelect');
            sel.innerHTML = '';
            labels.forEach(lbl => {
                const opt = document.createElement('option');
                opt.value = lbl;
                opt.textContent = lbl;
                sel.appendChild(opt);
            });
        }

        async function renderExpensesChart(){
            try{
                const res = await fetch('/expenses-data');
                const data = await res.json();
                populateMonthSelector(data.labels);
                const ctx = document.getElementById('expenseChart').getContext('2d');
                if(expenseChartInstance) expenseChartInstance.destroy();
                const isDark = document.body.classList.contains('dark');
                const lineColor = isDark ? '#ffffff' : 'rgba(54, 162, 235, 1)';
                const fillColor = isDark ? 'rgba(255,255,255,0.15)' : 'rgba(54, 162, 235, 0.2)';
                expenseChartInstance = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: 'Total Expenses (last 12 months)',
                            data: data.values,
                            fill: false,
                            tension: 0.3,
                            pointRadius: 4,
                            pointHoverRadius:6,
                            backgroundColor: fillColor,
                            borderColor: lineColor,
                            borderWidth: 3
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { display: false, labels: { font: { size: 12 }, color: isDark ? '#fff' : '#222' } } },
                        scales: {
                            x: { display: true, ticks: { color: isDark ? '#fff' : '#222', font: { size: 12 } }, grid: { color: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)' } },
                            y: { beginAtZero: true, ticks: { maxTicksLimit: 4, color: isDark ? '#fff' : '#222', font: { size: 12 } }, grid: { color: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)' } }
                        }
                    }
                });

                // default to the latest month
                const latest = data.labels[data.labels.length - 1];
                document.getElementById('monthSelect').value = latest;
                renderCategoryChart(latest);

            }catch(err){
                console.error('Failed to load expenses data', err);
            }
        }

        async function renderCategoryChart(label){
            try{
                const res = await fetch('/expenses-category-data?label=' + encodeURIComponent(label));
                const d = await res.json();
                const ctx = document.getElementById('categoryChart').getContext('2d');
                if(categoryChartInstance) categoryChartInstance.destroy();
                const colors = [
                    '#4e79a7','#f28e2b','#e15759','#76b7b2','#59a14f','#edc949','#b07aa1'
                ];
                const isDark = document.body.classList.contains('dark');
                const palette = isDark ? ['#9ad0ff','#ffd59a','#ff9a9a','#9ae2d6','#a8f0a0','#ffe79a','#d6b3e6'] : colors;
                categoryChartInstance = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: d.labels,
                        datasets: [{
                            data: d.values,
                            backgroundColor: palette.slice(0, d.labels.length),
                            borderColor: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)',
                            borderWidth: 1,
                            barThickness: 14
                        }]
                    },
                    options: {
                        indexAxis: 'y',
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: {
                            x: { beginAtZero: true, ticks: { maxTicksLimit: 4, color: isDark ? '#fff' : '#222', font: { size: 12 } }, grid: { color: isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)' } },
                            y: { ticks: { autoSkip: false, color: isDark ? '#fff' : '#222', font: { size: 12 } } }
                        }
                    }
                });
            }catch(err){
                console.error('Failed to load category data', err);
            }
        }

        window.addEventListener('load', () => {
            renderExpensesChart();
            document.getElementById('monthBtn').addEventListener('click', ()=>{
                const sel = document.getElementById('monthSelect');
                renderCategoryChart(sel.value);
            });
        });
    </script>
</body>
</html>
"""

@app.route('/expenses-data')
def expenses_data():
    # Return last-12-month labels and totals by querying `transactions` table.
    try:
        conn_local, cur_local = ensure_db()
        if conn_local is None or cur_local is None:
            raise Exception("DB connection not available")

        today = datetime.date.today()
        # compute earliest month start (first day of month 11 months ago)
        months = []
        month_starts = []
        for i in range(11, -1, -1):
            m = today.month - i
            y = today.year
            while m <= 0:
                m += 12
                y -= 1
            month_starts.append(datetime.date(y, m, 1))
            months.append(f"{calendar.month_abbr[m]} {y}")

        earliest = month_starts[0]

        # Exclude internal transfers (category 'self transfer') from expense totals
        query = """
            SELECT date_trunc('month', date) AS month, SUM(ABS(amount)) AS total
            FROM transactions
            WHERE date >= %s AND lower(coalesce(category, '')) NOT IN ('self transfer','transfers')
            GROUP BY month
            ORDER BY month
        """
        cur_local.execute(query, (earliest,))
        rows = cur_local.fetchall() or []

        totals_by_month = {}
        for r in rows:
            month_dt = r[0]
            # month_dt may be datetime.datetime; convert to date and set day=1
            if hasattr(month_dt, 'date'):
                month_key = month_dt.date().replace(day=1)
            else:
                month_key = month_dt.replace(day=1)
            totals_by_month[month_key] = float(r[1] or 0)

        values = [totals_by_month.get(ms, 0.0) for ms in month_starts]
        return jsonify({"labels": months, "values": values})

    except Exception as e:
        # Fallback to dummy data if DB is unavailable or query fails
        today = datetime.date.today()
        labels = []
        for i in range(11, -1, -1):
            month = today.month - i
            year = today.year
            while month <= 0:
                month += 12
                year -= 1
            labels.append(f"{calendar.month_abbr[month]} {year}")
        values = [random.randint(500, 2500) for _ in range(12)]
        return jsonify({"labels": labels, "values": values})


@app.route('/expenses-category-data')
def expenses_category_data():
    # Return category-wise totals for the selected month by querying `transactions` table.
    label = request.args.get('label', '')
    try:
        # parse label like 'Sep 2025'
        if label:
            try:
                start_dt = datetime.datetime.strptime(label, '%b %Y').date().replace(day=1)
            except Exception:
                # fallback: use latest month
                today = datetime.date.today()
                start_dt = datetime.date(today.year, today.month, 1)
        else:
            today = datetime.date.today()
            start_dt = datetime.date(today.year, today.month, 1)

        # compute next month start
        if start_dt.month == 12:
            end_dt = datetime.date(start_dt.year + 1, 1, 1)
        else:
            end_dt = datetime.date(start_dt.year, start_dt.month + 1, 1)

        conn_local, cur_local = ensure_db()
        if conn_local is None or cur_local is None:
            raise Exception("DB connection not available")

        # Exclude internal transfers and return top 5 categories by total
        query = """
            SELECT category, SUM(ABS(amount))::float AS total
            FROM transactions
            WHERE date >= %s AND date < %s AND lower(coalesce(category, '')) NOT IN ('self-transfer','transfers' ,'money received')
            GROUP BY category
            ORDER BY total DESC
            LIMIT 5
        """
        cur_local.execute(query, (start_dt, end_dt))
        rows = cur_local.fetchall() or []

        if rows:
            labels = [r[0] for r in rows]
            values = [float(r[1] or 0) for r in rows]
            return jsonify({"labels": labels, "values": values})
        else:
            # no data for month; return empty categories
            return jsonify({"labels": [], "values": []})

    except Exception as e:
        # fallback to previous dummy behavior
        categories = ['Housing', 'Food', 'Transport', 'Utilities', 'Entertainment', 'Healthcare', 'Other']
        seed = sum(ord(c) for c in label) if label else None
        if seed:
            random.seed(seed)
        values = [random.randint(50, 1200) for _ in categories]
        return jsonify({"labels": categories, "values": values})

SIGNUP_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Sign Up - FinanceBot</title>
    <style>
        body { font-family: Arial; display:flex; justify-content:center; align-items:center; height:100vh; background:#f4f6f8; }
        .signup-box { background:white; padding:30px; border-radius:12px; box-shadow:0 4px 12px rgba(0,0,0,0.1); width:320px; text-align:center; }
        input { width:90%; padding:10px; margin:8px 0; border:1px solid #ccc; border-radius:8px; }
        button { width:95%; padding:10px; background:#28a745; color:white; border:none; border-radius:8px; cursor:pointer; }
        button:hover { background:#218838; }
        .error { color:red; }
    </style>
</head>
<body>
    <div class="signup-box">
        <h2>Create Account</h2>
        <form method="POST" action="/signup">
            <input type="text" name="username" placeholder="Username" required><br>
            <input type="password" name="password" placeholder="Password" required><br>
            <button type="submit">Sign Up</button>
        </form>
        {% if error %}<p class="error">{{ error }}</p>{% endif %}
        {% if success %}<p style="color:green">{{ success }}</p>{% endif %}
        <p><a href="/login">Already have an account? Login</a></p>
    </div>
</body>
</html>
"""

def ensure_db():
    global conn, cur
    try:
        if conn is None or cur is None or conn.closed != 0:
            conn, cur = get_db_connection()
        else:
            # Test connection
            cur.execute("SELECT 1;")
    except (OperationalError, InterfaceError, DatabaseError):
        conn, cur = get_db_connection()
    return conn, cur

# --- Routes ---
@app.route("/signup", methods=["GET", "POST"])
def signup():
    return "Sign up is disabled.", 403

@app.route("/login", methods=["GET", "POST"])
def login():
    return "Login is disabled.", 403

@app.route("/logout")
def logout():
    return "Logout is disabled.", 403

@app.route("/")
def home():
    return render_template_string(CHAT_PAGE)

@app.route("/ask", methods=["POST"])
def ask():
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