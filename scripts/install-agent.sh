#!/bin/bash

set -e

echo "Installing ModelDock Agent..."

MODELD0CK_DIR="$HOME/modeldock-agent"
MODELDOCK_API="https://modeldock.duckdns.org/api"

mkdir -p "$MODELD0CK_DIR"

echo "Installing dependencies..."
sudo apt update
sudo apt install -y python3 python3-venv curl

echo "Creating Python environment..."
python3 -m venv "$MODELD0CK_DIR/venv"
source "$MODELD0CK_DIR/venv/bin/activate"

pip install requests psutil

echo "Creating agent..."
cat > "$MODELD0CK_DIR/agent.py" <<EOF
import time
import requests
import subprocess
import psutil
import socket

MODELDOCK_API = "$MODELDOCK_API"

NODE_ID = socket.gethostname()
NODE_NAME = socket.gethostname()
NODE_ENDPOINT = "http://127.0.0.1:11434"

boot_time = time.time()

def get_models():
    try:
        response = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
        response.raise_for_status()
        data = response.json()
        return [model["name"] for model in data.get("models", [])]
    except Exception:
        return []

def get_gpu_info():
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.used,memory.total,temperature.gpu,utilization.gpu", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        return "CPU Mode"
    except Exception:
        return "CPU Mode"

def register_node():
    payload = {
        "id": NODE_ID,
        "name": NODE_NAME,
        "status": "online",
        "gpu": get_gpu_info(),
        "endpoint": NODE_ENDPOINT,
        "models": get_models(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "ram_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
        "uptime_seconds": time.time() - boot_time,
    }

    try:
        response = requests.post(
            f"{MODELDOCK_API}/register-node",
            json=payload,
            headers={"X-Agent-Key": "b3cc1786c75522a69d945625954d2a94"},
            timeout=5,
        )
        print("Registered:", response.json())
    except Exception as e:
        print("Register failed:", e)

while True:
    register_node()
    time.sleep(10)
EOF

echo "Creating systemd service..."
sudo tee /etc/systemd/system/modeldock-agent.service > /dev/null <<EOF
[Unit]
Description=ModelDock Agent
After=network.target

[Service]
User=$USER
WorkingDirectory=$MODELD0CK_DIR
ExecStart=$MODELD0CK_DIR/venv/bin/python $MODELD0CK_DIR/agent.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable modeldock-agent
sudo systemctl restart modeldock-agent

echo "ModelDock Agent installed and running."
