from flask import Flask, render_template, request, session, redirect
from flask_socketio import SocketIO, emit
import json
import os
import time
from threading import Thread

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "chuoi-bao-mat-mac-dinh") 

# Cấu hình SocketIO cho Render (sử dụng gevent)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="gevent")

MSG_FILE = "/tmp/messages.json" # Dùng /tmp để có quyền ghi trên một số server
ACC_FILE = "/tmp/accounts.json"

def init_db():
    for file_path, initial_data in [(MSG_FILE, []), (ACC_FILE, {"1": "1"})]:
        if not os.path.exists(file_path) or os.stat(file_path).st_size == 0:
            with open(file_path, "w") as f:
                json.dump(initial_data, f)

init_db()

def auto_delete_task():
    while True:
        time.sleep(30)
        try:
            with open(MSG_FILE, "r") as f:
                msgs = json.load(f)
            now = time.time()
            new_msgs = [m for m in msgs if now - m.get('time', 0) < 300]
            if len(new_msgs) != len(msgs):
                with open(MSG_FILE, "w") as f:
                    json.dump(new_msgs, f, indent=4)
        except: pass

Thread(target=auto_delete_task, daemon=True).start()

@app.route("/")
def index():
    if "user" in session: return redirect("/chat")
    return render_template("index.html") # Bạn nhớ tạo file login nhé

@app.route("/chat")
def chat():
    if "user" not in session: return redirect("/")
    try:
        with open(MSG_FILE, "r") as f: msgs = json.load(f)
    except: msgs = []
    return render_template("chat.html", username=session["user"], messages=msgs)

@socketio.on("send_message")
def handle_msg(data):
    data['time'] = time.time()
    try:
        with open(MSG_FILE, "r") as f: msgs = json.load(f)
        msgs.append(data)
        with open(MSG_FILE, "w") as f: json.dump(msgs, f, indent=4)
        emit("receive_message", data, broadcast=True)
    except: pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    socketio.run(app, host="0.0.0.0", port=port)