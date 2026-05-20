import time
import requests
import subprocess

MODELD0CK_API = "http://127.0.0.1:8000"

NODE_ID = "local-node"
NODE_NAME = "Local VPS"

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
        "models": get_models(),
    }

    try:
        response = requests.post(
            f"{MODELD0CK_API}/register-node",
            json=payload,
            timeout=5,
        )
        print("Registered:", response.json())
    except Exception as e:
        print("Register failed:", e)

if __name__ == "__main__":
    while True:
        register_node()
        time.sleep(10)
