{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 1,
   "metadata": {
    "executionInfo": {
     "elapsed": 8761,
     "status": "ok",
     "timestamp": 1754468664876,
     "user": {
      "displayName": "Didar Arslan",
      "userId": "04743234066270737226"
     },
     "user_tz": -180
    },
    "id": "EbLSZRy89Wcv"
   },
   "outputs": [],
   "source": [
    "!pip install flask-ngrok --quiet"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 2,
   "metadata": {
    "colab": {
     "base_uri": "https://localhost:8080/"
    },
    "executionInfo": {
     "elapsed": 323,
     "status": "ok",
     "timestamp": 1754468665202,
     "user": {
      "displayName": "Didar Arslan",
      "userId": "04743234066270737226"
     },
     "user_tz": -180
    },
    "id": "YzlzXOhX9Zn4",
    "outputId": "6ce497f7-61b7-4867-a892-51448b7cde79"
   },
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "ERROR:  accepts 1 arg(s), received 0\n"
     ]
    }
   ],
   "source": [
    "# Ngrok\n",
    "!wget -q -nc https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.zip\n",
    "!unzip -q -n ngrok-v3-stable-linux-amd64.zip\n",
    "\n",
    "# Ngrok Tokenization\n",
    "!./ngrok config add-authtoken $NGROK_AUTH_TOKEN"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {
    "executionInfo": {
     "elapsed": 58,
     "status": "ok",
     "timestamp": 1754468665261,
     "user": {
      "displayName": "Didar Arslan",
      "userId": "04743234066270737226"
     },
     "user_tz": -180
    },
    "id": "2K0xNVIl2KOw"
   },
   "outputs": [],
   "source": [
    "# NGROK Token\n",
    "NGROK_AUTH_TOKEN = \" \" # Replace with your actual Ngrok auth token"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 4,
   "metadata": {
    "executionInfo": {
     "elapsed": 175,
     "status": "ok",
     "timestamp": 1754468665435,
     "user": {
      "displayName": "Didar Arslan",
      "userId": "04743234066270737226"
     },
     "user_tz": -180
    },
    "id": "4CuDlDdc_Hil"
   },
   "outputs": [],
   "source": [
    "from flask import Flask, request, jsonify\n",
    "import threading\n",
    "from datetime import datetime\n",
    "\n",
    "app = Flask(__name__)\n",
    "\n",
    "# Basit context database\n",
    "user_context_db = {\n",
    "    \"unique_thread_id_1\": {\n",
    "        \"allowed_tools\": [\"VodafoneRAG\"],\n",
    "        \"segment\": \"VF_Customer\",\n",
    "        \"role\": \"user\"\n",
    "    },\n",
    "    \"unique_thread_id_2\": {\n",
    "        \"allowed_tools\": [\"AdditionTool\", \"SubtractionTool\", \"MultiplicationTool\", \"DivisionTool\"],\n",
    "        \"segment\": \"Math_Calculator\",\n",
    "        \"role\": \"admin\"\n",
    "    }\n",
    "}\n",
    "\n",
    "@app.route(\"/get_context\", methods=[\"POST\"])\n",
    "def get_context():\n",
    "    data = request.get_json()\n",
    "    thread_id = data.get(\"thread_id\")\n",
    "    context = user_context_db.get(thread_id, {\n",
    "        \"allowed_tools\": [],\n",
    "        \"segment\": \"general\",\n",
    "        \"role\": \"user\"\n",
    "    })\n",
    "    return jsonify(context)\n",
    "\n",
    "@app.route(\"/check_policy\", methods=[\"POST\"])\n",
    "def check_policy():\n",
    "    data = request.get_json()\n",
    "    thread_id = data.get(\"thread_id\")\n",
    "    tool_name = data.get(\"tool\")\n",
    "\n",
    "    thread_context = user_context_db.get(thread_id, {})\n",
    "    allowed_tools = thread_context.get(\"allowed_tools\", [])\n",
    "    role = thread_context.get(\"role\", \"user\")\n",
    "\n",
    "    # Just for admins audit tool\n",
    "    if tool_name == \"AuditTool\" and role != \"admin\":\n",
    "        return jsonify({\"allowed\": False})\n",
    "\n",
    "    allowed = tool_name in allowed_tools\n",
    "    return jsonify({\"allowed\": allowed})\n",
    "\n",
    "@app.route(\"/set_segment\", methods=[\"POST\"])\n",
    "def set_segment():\n",
    "    data = request.get_json()\n",
    "    thread_id = data.get(\"thread_id\")\n",
    "    new_segment = data.get(\"segment\")\n",
    "\n",
    "    if thread_id in user_context_db:\n",
    "        user_context_db[thread_id][\"segment\"] = new_segment\n",
    "        return jsonify({\"status\": \"success\", \"message\": f\"Segment updated to {new_segment} for {thread_id}\"})\n",
    "    else:\n",
    "        return jsonify({\"status\": \"error\", \"message\": \"Thread ID not found\"}), 404\n",
    "\n",
    "@app.route(\"/set_context\", methods=[\"POST\"])\n",
    "def set_context():\n",
    "    data = request.get_json()\n",
    "    thread_id = data.get(\"thread_id\")\n",
    "    segment = data.get(\"segment\", \"general\")\n",
    "    role = data.get(\"role\", \"user\")\n",
    "    allowed_tools = data.get(\"allowed_tools\", [])\n",
    "\n",
    "    user_context_db[thread_id] = {\n",
    "        \"segment\": segment,\n",
    "        \"role\": role,\n",
    "        \"allowed_tools\": allowed_tools\n",
    "    }\n",
    "\n",
    "    return jsonify({\n",
    "        \"status\": \"success\",\n",
    "        \"message\": f\"Context set for {thread_id}\",\n",
    "        \"context\": user_context_db[thread_id]\n",
    "    })\n",
    "\n",
    "@app.route(\"/set_role\", methods=[\"POST\"])\n",
    "def set_role():\n",
    "    data = request.get_json()\n",
    "    thread_id = data.get(\"thread_id\")\n",
    "    new_role = data.get(\"role\")\n",
    "\n",
    "    if thread_id in user_context_db:\n",
    "        user_context_db[thread_id][\"role\"] = new_role\n",
    "        return jsonify({\"status\": \"success\", \"message\": f\"Role updated to {new_role} for {thread_id}\"})\n",
    "    else:\n",
    "        return jsonify({\"status\": \"error\", \"message\": \"Thread ID not found\"}), 404\n",
    "\n",
    "@app.route(\"/log_tool_usage\", methods=[\"POST\"])\n",
    "def log_tool_usage():\n",
    "    data = request.get_json()\n",
    "    print(\"🧾 MCP LOG RECEIVED:\")\n",
    "    print(data)\n",
    "    return jsonify({\"status\": \"logged\"})\n",
    "\n",
    "# Flask’i arka planda çalıştır\n",
    "def run_flask():\n",
    "    app.run(port=5005)\n",
    "\n",
    "thread = threading.Thread(target=run_flask)\n",
    "thread.start()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 5,
   "metadata": {
    "colab": {
     "base_uri": "https://localhost:8080/"
    },
    "executionInfo": {
     "elapsed": 12485,
     "status": "ok",
     "timestamp": 1754468677922,
     "user": {
      "displayName": "Didar Arslan",
      "userId": "04743234066270737226"
     },
     "user_tz": -180
    },
    "id": "5QP9a3LjEZHd",
    "outputId": "23192ad8-3932-49a3-ff32-8df8e5062f32"
   },
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      " * Serving Flask app '__main__'\n",
      " * Debug mode: off\n"
     ]
    },
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "INFO:werkzeug:\u001b[31m\u001b[1mWARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.\u001b[0m\n",
      " * Running on http://127.0.0.1:5005\n",
      "INFO:werkzeug:\u001b[33mPress CTRL+C to quit\u001b[0m\n"
     ]
    },
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "MCP test server public URL: NgrokTunnel: \"https://1441f2969cd9.ngrok-free.app\" -> \"http://localhost:5005\"\n"
     ]
    }
   ],
   "source": [
    "!pip install -q pyngrok\n",
    "\n",
    "from pyngrok import ngrok\n",
    "\n",
    "# 5005 portunu aç\n",
    "public_url = ngrok.connect(5005)\n",
    "print(\"MCP test server public URL:\", public_url)"
   ]
  }
 ],
 "metadata": {
  "colab": {
   "authorship_tag": "ABX9TyOp7BQVqR21LknQoh2hJEnv",
   "provenance": []
  },
  "kernelspec": {
   "display_name": "Python 3",
   "name": "python3"
  },
  "language_info": {
   "name": "python"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 0
}
