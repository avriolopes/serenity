import os
from flask import Flask, render_template, request, jsonify, session
import requests
from chat_formatter import format_for_chat
from flask_cors import CORS

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-change-me")

CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

API_URL = "https://router.huggingface.co/novita/v3/openai/chat/completions"
HF_API_KEY = os.getenv("HF_API_KEY", "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")
HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"}

SYSTEM_PROMPT = (
    "You are Serenity, a compassionate AI mental health assistant. "
    "Use plain, human language. Avoid markdown and headings. "
    "Write short paragraphs with clear lists when needed. "
    "Encourage professional help or crisis resources if risk is present."
    "Do not incluse em Dashes"
)

def get_history():
    return session.get("history", [])

def save_history(history):
    if len(history) > 40:
        history = history[-40:]
    session["history"] = history
    session.modified = True

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/history")
def history():
    return jsonify({"history": get_history()})

@app.route("/reset", methods=["POST"])
def reset():
    session.pop("history", None)
    return jsonify({"ok": True})

@app.route("/chat", methods=["POST"])
def chat():
    user_message = (request.json or {}).get("message", "").strip()
    if not user_message:
        return jsonify({"reply": "I am here and listening."})

    history = get_history()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history + [
        {"role": "user", "content": user_message}
    ]

    payload = {"model": "deepseek/deepseek-v3-0324", "messages": messages}

    try:
        r = requests.post(API_URL, headers=HEADERS, json=payload, timeout=60)
        r.raise_for_status()
        raw_reply = r.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        raw_reply = "Sorry, there was an error. Please try again."

    print("-"*100)
    print("This is the raw reply: ", raw_reply)
    print("-"*100)
    reply = format_for_chat(raw_reply)
    print("-"*100)
    print("This is the reply: ", reply)
    print("-"*100)

    history.extend([
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": raw_reply},
    ])
    save_history(history)

    return jsonify({"reply": raw_reply})

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    app.run(host=host, port=port, debug=True, threaded=True)