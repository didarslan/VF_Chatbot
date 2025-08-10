!pip install flask-ngrok --quiet

# Ngrok
!wget -q -nc https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.zip
!unzip -q -n ngrok-v3-stable-linux-amd64.zip

# Ngrok Tokenization
!./ngrok config add-authtoken $NGROK_AUTH_TOKEN

# NGROK Token
NGROK_AUTH_TOKEN = " " # Replace with your actual ngrok auth token

from flask import Flask, request, jsonify
import threading
from datetime import datetime

app = Flask(__name__)

# Basit context database
user_context_db = {
    "unique_thread_id_1": {
        "allowed_tools": ["VodafoneRAG"],
        "segment": "VF_Customer",
        "role": "user"
    },
    "unique_thread_id_2": {
        "allowed_tools": ["AdditionTool", "SubtractionTool", "MultiplicationTool", "DivisionTool"],
        "segment": "Math_Calculator",
        "role": "admin"
    }
}

@app.route("/get_context", methods=["POST"])
def get_context():
    data = request.get_json()
    thread_id = data.get("thread_id")
    context = user_context_db.get(thread_id, {
        "allowed_tools": [],
        "segment": "general",
        "role": "user"
    })
    return jsonify(context)

@app.route("/check_policy", methods=["POST"])
def check_policy():
    data = request.get_json()
    thread_id = data.get("thread_id")
    tool_name = data.get("tool")

    thread_context = user_context_db.get(thread_id, {})
    allowed_tools = thread_context.get("allowed_tools", [])
    role = thread_context.get("role", "user")

    # Just for admins audit tool
    if tool_name == "AuditTool" and role != "admin":
        return jsonify({"allowed": False})

    allowed = tool_name in allowed_tools
    return jsonify({"allowed": allowed})

@app.route("/set_segment", methods=["POST"])
def set_segment():
    data = request.get_json()
    thread_id = data.get("thread_id")
    new_segment = data.get("segment")

    if thread_id in user_context_db:
        user_context_db[thread_id]["segment"] = new_segment
        return jsonify({"status": "success", "message": f"Segment updated to {new_segment} for {thread_id}"})
    else:
        return jsonify({"status": "error", "message": "Thread ID not found"}), 404

@app.route("/set_context", methods=["POST"])
def set_context():
    data = request.get_json()
    thread_id = data.get("thread_id")
    segment = data.get("segment", "general")
    role = data.get("role", "user")
    allowed_tools = data.get("allowed_tools", [])

    user_context_db[thread_id] = {
        "segment": segment,
        "role": role,
        "allowed_tools": allowed_tools
    }

    return jsonify({
        "status": "success",
        "message": f"Context set for {thread_id}",
        "context": user_context_db[thread_id]
    })

@app.route("/set_role", methods=["POST"])
def set_role():
    data = request.get_json()
    thread_id = data.get("thread_id")
    new_role = data.get("role")

    if thread_id in user_context_db:
        user_context_db[thread_id]["role"] = new_role
        return jsonify({"status": "success", "message": f"Role updated to {new_role} for {thread_id}"})
    else:
        return jsonify({"status": "error", "message": "Thread ID not found"}), 404

@app.route("/log_tool_usage", methods=["POST"])
def log_tool_usage():
    data = request.get_json()
    print("🧾 MCP LOG RECEIVED:")
    print(data)
    return jsonify({"status": "logged"})

# Flask’i arka planda çalıştır
def run_flask():
    app.run(port=5005)

thread = threading.Thread(target=run_flask)
thread.start()

!pip install -q pyngrok

from pyngrok import ngrok

# 5005 portunu aç
public_url = ngrok.connect(5005)
print("MCP test server public URL:", public_url)