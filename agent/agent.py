import time
import requests
import subprocess
import psutil

MODELD0CK_API = "http://127.0.0.1:8000"

NODE_ID = "local-node"
NODE_NAME = "Local VPS"
CLAIM_CODE = "MD-F6HU-3UFR"

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
            [
                "nvidia-smi",
                "--query-gpu=name,memory.used,memory.total,temperature.gpu,utilization.gpu",
                "--format=csv,noheader"
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0 and result.stdout.strip():
            parts = [p.strip() for p in result.stdout.strip().split(",")]

            return {
                "gpu": parts[0],
                "gpu_name": parts[0],
                "gpu_memory_used": float(parts[1]),
                "gpu_memory_total": float(parts[2]),
                "gpu_temp": float(parts[3]),
                "gpu_util": float(parts[4]),
            }

        return {
            "gpu": "CPU Mode",
            "gpu_name": None,
            "gpu_memory_used": None,
            "gpu_memory_total": None,
            "gpu_temp": None,
            "gpu_util": None,
       }

    except Exception:
        return {
            "gpu": "CPU Mode",
            "gpu_name": None,
            "gpu_memory_used": None,
            "gpu_memory_total": None,
            "gpu_temp": None,
            "gpu_util": None,
        }

def get_metrics():
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "ram_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
        "uptime_seconds": time.time() - boot_time,
    }

def get_task():
    try:
        response = requests.get(
            f"{MODELD0CK_API}/agent/tasks",
            params={"node_id": NODE_ID},
            timeout=5,
        )

        response.raise_for_status()

        data = response.json()

        return data.get("task")
    except Exception:
        return None

def complete_task(task_id, result):
    try:
        requests.post(
            f"{MODELD0CK_API}/agent/tasks/{task_id}/complete",
            json=result,
            timeout=10,
        )
    except Exception as e:
        print("Complete failed:", e)

def execute_task(task):
    if not task:
        return

    if task["type"] == "download_model":
        model = task["payload"]["model"]

        print("Downloading:", model)

        result = subprocess.run(
            ["ollama", "pull", model],
            capture_output=True,
            text=True,
        )

        complete_task(
            task["id"],
            {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            },
        )

    elif task["type"] == "chat":
        model = task["payload"]["model"]
        prompt = task["payload"]["prompt"]

        response = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=600,
        )

        complete_task(
            task["id"],
            response.json(),
        )

def register_node():
    global CLAIM_CODE
    metrics = get_metrics()
    gpu_info = get_gpu_info()

    payload = {
        "id": NODE_ID,
        "name": NODE_NAME,
        "status": "online",
        "claim_code": CLAIM_CODE,
	"endpoint": "http://127.0.0.1:11434",
        "gpu": gpu_info["gpu"],
        "gpu_name": gpu_info["gpu_name"],
        "gpu_memory_used": gpu_info["gpu_memory_used"],
        "gpu_memory_total": gpu_info["gpu_memory_total"],
        "gpu_temp": gpu_info["gpu_temp"],
        "gpu_util": gpu_info["gpu_util"],
        "models": get_models(),
        "cpu_percent": metrics["cpu_percent"],
        "ram_percent": metrics["ram_percent"],
        "disk_percent": metrics["disk_percent"],
        "uptime_seconds": metrics["uptime_seconds"],
    }

    try:
        response = requests.post(
            f"{MODELD0CK_API}/register-node",
            json=payload,
            headers={"X-Agent-Key": "b3cc1786c75522a69d945625954d2a94"},
            timeout=5,
        )

        data = response.json()
        print("Registered:", data)

        if data.get("status") == "registered":
            CLAIM_CODE = None

    except Exception as e:
        print("Register failed:", e)

if __name__ == "__main__":
    while True:
        register_node()

        task = get_task()

        execute_task(task)

        time.sleep(10)


