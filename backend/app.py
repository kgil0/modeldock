from typing import Optional
from providers.runpod import RunPodProvider
from workers.provisioning import start_provisioning
from providers.manager import ProviderManager
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import requests
import sqlite3
import json
from datetime import datetime
import secrets
import string
from passlib.context import CryptContext

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://49.12.244.57:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_URL = "http://127.0.0.1:11434"
DB_PATH = "modeldock.db"
AGENT_KEY ="b3cc1786c75522a69d945625954d2a94"
provider_manager = ProviderManager()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class ChatTaskRequest(BaseModel):
    node_id: str
    model: str
    prompt: str

class DownloadModelRequest(BaseModel):
    node_id: str
    model: str

class ChatRequest(BaseModel):
    node_id: str
    model: str
    prompt: str

class NodeRequest(BaseModel):
    id: str
    name: str
    status: str
    gpu: str
    gpu_name: str | None = None
    gpu_memory_used: float | None = None
    gpu_memory_total: float | None = None
    gpu_temp: float | None = None
    gpu_util: float | None = None
    endpoint: str
    models: list[str]
    cpu_percent: float
    ram_percent: float
    disk_percent: float
    uptime_seconds: float
    claim_code: str | None = None

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str

class ClaimCodeRequest(BaseModel):
    user_id: str

class RentGpuRequest(BaseModel):
    provider: str
    gpu_id: str
    hours: int

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nodes (
            id TEXT PRIMARY KEY,
            name TEXT,
            status TEXT,
            gpu TEXT,
            endpoint TEXT,
            models TEXT,
            cpu_percent REAL,
            ram_percent REAL,
            disk_percent REAL,
            uptime_seconds REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE,
            password TEXT,
            created_at TEXT
        )
    """)

    for column in [
        "gpu_name TEXT",
        "gpu_memory_used REAL",
        "gpu_memory_total REAL",
        "gpu_temp REAL",
        "gpu_util REAL",
        "last_seen TEXT",
    ]:

        try:
            cursor.execute(f"ALTER TABLE nodes ADD COLUMN {column}")
        except sqlite3.OperationalError:
            pass

    conn.commit()
    conn.close()


def get_all_nodes(user_id: str | None = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if user_id:
        cursor.execute("SELECT * FROM nodes WHERE user_id = ?", (user_id,))
    else:
        cursor.execute("SELECT * FROM nodes")

    rows = cursor.fetchall()
    conn.close()

    nodes = []

    now = datetime.utcnow()

    for row in rows:

        last_seen = row[15]

        node_status = "offline"

        if last_seen:
            try:
                last_seen_dt = datetime.fromisoformat(last_seen)
                seconds_since_seen = (now - last_seen_dt).total_seconds()

                if seconds_since_seen <= 30:
                    node_status = "online"

                elif seconds_since_seen <= 120:
                      node_status = "stale"
            except:
                node_status = "offline"

        nodes.append({
            "id": row[0],
            "name": row[1],
            "status": node_status,
            "gpu": row[3],
            "gpu_name": row[10],
            "gpu_memory_used": row[11],
            "gpu_memory_total": row[12],
            "gpu_temp": row[13],
            "gpu_util": row[14],
            "endpoint": row[4],
            "models": json.loads(row[5]),
            "cpu_percent": row[6],
            "ram_percent": row[7],
            "disk_percent": row[8],
            "uptime_seconds": row[9],
            "last_seen": row[15],
        })

    return nodes


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ollama/status")
def ollama_status():
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        response.raise_for_status()
        return {
            "status": "connected",
            "models": response.json().get("models", [])
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }



@app.post("/chat")
def chat(request: ChatRequest):
    try:
        nodes = get_all_nodes()
        target_node = next((n for n in nodes if n["id"] == request.node_id), None)

        if not target_node:
            return {
                "status": "error",
                "message": "Node not found"
            }

        payload = {
            "model": request.model,
            "prompt": request.prompt,
            "stream": False
        }

        response = requests.post(
            f"{target_node['endpoint']}/api/generate",
            json=payload,
            timeout=120
        )

        response.raise_for_status()
        data = response.json()

        response_text = data.get("response", "")

        history = []

        try:
            with open("history.json", "r") as f:
                history = json.load(f)

        except:
            history = []

        history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "model": request.model,
            "prompt": request.prompt,
            "response": response_text
        })

        with open("history.json", "w") as f:
            json.dump(history, f, indent=2)

        return {
            "node": request.node_id,
            "model": request.model,
            "response": response_text
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@app.post("/register-node")
def register_node(node: NodeRequest, x_agent_key: str | None = Header(default=None)):

    if x_agent_key != AGENT_KEY:
        raise HTTPException(status_code=401, detail="Invalid agent key")

    conn=sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT user_id FROM nodes WHERE id = ?",
        (node.id,)
    )

    existing_node = cursor.fetchone()

    if existing_node:
        user_id = existing_node[0]

    else:
        if not node.claim_code:
            conn.close()
            raise HTTPException(
                status_code=400,
                detail="Claim code required"
            )

        cursor.execute(
            "SELECT user_id FROM claim_codes WHERE code = ? AND used = 0",
            (node.claim_code,)
        )

        result = cursor.fetchone()

        if not result:
            conn.close()
            raise HTTPException(
                status_code=400,
                detail="Invalid or used claim code"
            )

        user_id = result[0]

        cursor.execute(
            "UPDATE claim_codes SET used = 1 WHERE code = ?",
            (node.claim_code,)
        )


    cursor.execute("""
        INSERT OR REPLACE INTO nodes (
            id, name, status, gpu, endpoint, models,
            cpu_percent, ram_percent, disk_percent, uptime_seconds,
            gpu_name, gpu_memory_used, gpu_memory_total, gpu_temp, gpu_util, last_seen, user_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        node.id,
        node.name,
        node.status,
        node.gpu,
        node.endpoint,
        json.dumps(node.models),
        node.cpu_percent,
        node.ram_percent,
        node.disk_percent,
        node.uptime_seconds,
        node.gpu_name,
        node.gpu_memory_used,
        node.gpu_memory_total,
        node.gpu_temp,
        node.gpu_util,
        datetime.utcnow().isoformat(),
        user_id,
    ))

    conn.commit()
    conn.close()

    return {"status": "registered"}


@app.get("/nodes")
def get_nodes(user_id: str | None = None):
    return get_all_nodes(user_id)

@app.post("/chat/stream")
def chat_stream (request: ChatRequest):

    def generate():
        full_text = ""

        try:
            nodes = get_all_nodes()

            target_node = next(
                (n for n in nodes if n["id"] ==request.node_id),
                None
            )

            if not target_node:
                yield "Node not found"
                return

            payload = {
                "model": request.model,
                "prompt": request.prompt,
                "stream": True
            }

            with requests.post(
                f"{target_node['endpoint']}/api/generate",
                json=payload,
                stream=True,
                timeout=120

            ) as response:

                response.raise_for_status()

                for line in response.iter_lines():
                    if line:
                        data = json.loads(line.decode("utf-8"))
                        token = data.get("response", "")

                        if token:
                            full_text += token
                            yield token
            history = []

            try:
                with open("history.json", "r") as f:
                    history = json.load(f)
            except:
                history = []

            history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "model": request.model,
                "prompt": request.prompt,
                "response": full_text

            })

            with open("history.json", "w") as f:
                json.dump(history, f, indent=2)

        except Exception as e:
            yield f"Error: {str(e)}"

    return StreamingResponse(
        generate(),
        media_type="text/plain"
    )


@app.post("/pull-model")
def pull_model(data: dict):
    model = data.get("model")

    if not model:
        return {"error": "No model provided"}

    requests.post(
        f"{OLLAMA_URL}/api/pull",
        json={"name": model},
        timeout=36000,
    )

    return {"status": "pull started", "model": model}

@app.post("/delete-model")
def delete_model(data: dict):
    model = data.get("model")

    if not model:
        return {"error": "No model provided"}

    response = requests.delete(
        f"{OLLAMA_URL}/api/delete",
        json={"name": model},
        timeout=120,
    )

    response.raise_for_status()

    return {"status": "deleted", "model": model}

@app.get("/history")
def get_history():

    try:
        with open ("history.json", "r") as f:
            history = json.load(f)

        return history[::-1]

    except:
        return []

@app.post("/register")
def register(request: RegisterRequest):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE email = ?",
        (request.email,)
    )

    existing_user = cursor.fetchone()

    if existing_user:
        conn.close()

        return {
            "status": "error",
            "message": "User already exists"
        }

    password_hash = pwd_context.hash(request.password)

    user_id = secrets.token_hex(8)

    cursor.execute(
        """

        INSERT INTO users (
            id,
            email,
            password,
            created_at
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            user_id,
            request.email,
            password_hash,
            datetime.utcnow().isoformat()
        )
      )
    conn.commit()
    conn.close()

    return {
        "status": "ok",
        "user_id": user_id
    }

@app.post("/login")
def login(request: LoginRequest):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, email, password FROM users WHERE email = ?",
        (request.email,)
    )

    user = cursor.fetchone()

    if not user or not pwd_context.verify(request.password, user[2]):
        conn.close()
        return {
            "status": "error",
            "message": "Invalid login"
        }

    token = secrets.token_hex(32)

    cursor.execute(
        "INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)",
        (token, user[0], datetime.utcnow().isoformat())
    )

    conn.commit()
    conn.close()

    return {
        "status": "ok",
        "token": token,
        "user": {
            "id": user[0],
            "email": user[1]
        }
    }

@app.post("/generate-claim-code")
def generate_claim_code(request: ClaimCodeRequest):
    alphabet = string.ascii_uppercase + string.digits
    part1= "".join(secrets.choice(alphabet) for _ in range(4))
    part2= "".join(secrets.choice(alphabet) for _ in range(4))

    code = f"MD-{part1}-{part2}"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO claim_codes (code, user_id, created_at) VALUES (?, ?, ?)",
        (code, request.user_id, datetime.utcnow().isoformat())
    )

    conn.commit()
    conn.close()

    return {
        "status": "ok",
        "code": code,
        "user_id": request.user_id
    }

@app.delete("/node/{node_id}")
def delete_node(node_id: str, user_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM nodes WHERE id = ? AND user_id = ?",
        (node_id, user_id)
    )

    deleted = cursor.rowcount

    conn.commit()
    conn.close()

    if deleted == 0:
        raise HTTPException(
            status_code=404,
            detail="Node not found"
        )

    return {
        "status": "deleted",
        "node_id": node_id
    }

@app.post("/tasks/download-model")
def create_download_model_task(request: DownloadModelRequest):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    task_id = secrets.token_hex(8)
    now = datetime.utcnow().isoformat()

    cursor.execute(
        """

        INSERT INTO tasks (
            id, node_id, type, payload, status, result, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            task_id,
            request.node_id,
            "download_model",
            json.dumps({"model": request.model}),
            "pending",
            "",
            now,
            now,
        )
    )

    conn.commit()
    conn.close()

    return {
        "status": "created",
        "task_id": task_id
    }


@app.get("/agent/tasks")
def get_agent_tasks(node_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, type, payload
        FROM tasks
        WHERE node_id = ? AND status = 'pending'
        ORDER BY created_at ASC
        LIMIT 1
        """,
        (node_id,)
    )

    task = cursor.fetchone()

    if not task:
        conn.close()
        return {"task": None}

    task_id, task_type, payload = task

    cursor.execute(
        "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
        ("running", datetime.utcnow().isoformat(), task_id)
    )

    conn.commit()
    conn.close()

    return {
        "task": {
            "id": task_id,
            "type": task_type,
            "payload": json.loads(payload)
        }
    }

@app.post("/agent/tasks/{task_id}/complete")
def complete_agent_task(task_id: str, result: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE tasks SET status = ?, result = ?, updated_at = ? WHERE id = ?",
        (
            "finished",
            json.dumps(result),
            datetime.utcnow().isoformat(),
            task_id,
        )
    )

    conn.commit()
    conn.close()

    return {
        "status": "finished",
        "task_id": task_id
    }

@app.post("/tasks/chat")
def create_chat_task(request: ChatTaskRequest):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    task_id = secrets.token_hex(8)
    now = datetime.utcnow().isoformat()

    cursor.execute(
        """

        INSERT INTO tasks (
            id,node_id,type,payload,status,result,created_at,updated_at
        )
        VALUES (?,?,?,?,?,?,?,?)
        """,
        (
            task_id,
            request.node_id,
            "chat",
            json.dumps({
                "model": request.model,
                "prompt": request.prompt,
            }),
            "pending",
            "",
            now,
            now,
        )
    )

    conn.commit()
    conn.close()

    return {
        "task_id": task_id,
        "status": "created",
    }

@app.get("/tasks/{task_id}")
def get_task(task_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """

        SELECT
            id,
            node_id,
            type,
            payload,
            status,
            result,
            created_at,
            updated_at
        FROM tasks
        WHERE id=?
        """,
        (task_id,),
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(404)

    task = dict(row)

    if task["payload"]:
        task["payload"] = json.loads(task["payload"])

    if task["result"]:
        task["result"] = json.loads(task["result"])

    return task

@app.get("/tasks")
def list_tasks(limit: int = 50):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """

        SELECT
            id,
            node_id,
            type,
            payload,
            status,
            result,
            created_at,
            updated_at
        FROM tasks
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    )

    rows = cursor.fetchall()
    conn.close()

    tasks = []

    for row in rows:
        item = dict(row)

        if item["payload"]:
            try:
                item["payload"] = json.loads(item["payload"])
            except Exception:
                pass

        if item["result"]:
            try:
                item["result"] = json.loads(item["result"])
            except Exception:
                pass

        tasks.append(item)

    return {
        "tasks": tasks
    }

@app.get("/nodes")
def get_nodes():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM nodes
        ORDER BY last_seen DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    nodes = []

    for row in rows:
        item = dict(row)

        if item.get("models"):
            try:
                item["models"] = json.loads(item["models"])
            except Exception:
                item["models"] = []

        nodes.append(item)
    return {
        "nodes": nodes
    }

@app.get("/models/catalog")
def get_models_catalog():
    try:
        with open("models_catalog.json", "r") as f:
            models = json.load(f)

        return {
            "models": models
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.get("/cloud-gpus")
def cloud_gpus():

    return {
        "gpus": provider_manager.list_all_gpus()
    }

@app.post("/rent-gpu")
def rent_gpu(request: RentGpuRequest):
    task_id = secrets.token_hex(8)
    now = datetime.utcnow().isoformat()

    instance = provider_manager.rent_gpu(
        request.provider,
        request.gpu_id,
        request.hours,
    )

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO tasks (
            id,
            node_id,
            type,
            payload,
            status,
            result,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            task_id,
            None,
            "rent_gpu",
            json.dumps({
                "provider": request.provider,
                "gpu_id": request.gpu_id,
                "hours": request.hours,
            }),
            "starting",
            json.dumps(instance),
            now,
            now,
        ),
    )

    conn.commit()
    conn.close()

    start_provisioning(task_id)

    return {
        "task_id": task_id,
        "status": "starting",
        "instance": instance,
    }

@app.get("/runpod/pods")
def runpod_pods():
    provider = RunPodProvider()

    try:
        return {
            "success": True,
            "pods": provider.list_pods()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/runpod/gpus")
def runpod_gpus(
    min_vram: int = 0,
    max_price: Optional[float] = None,
):
    try:
        raw_gpus = RunPodProvider().list_gpus()
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
        }

    gpus = []

    for gpu in raw_gpus:
        lowest_price = gpu.get("lowestPrice") or {}
        price = lowest_price.get("uninterruptablePrice")
        vram = gpu.get("memoryInGb") or 0

        if price is None:
            continue

        if vram < min_vram:
            continue

        if max_price is not None and price > max_price:
            continue

        gpus.append({
            "gpu_id": gpu["id"],
            "name": gpu["displayName"],
            "vram_gb": vram,
            "price_per_hour": price,
            "stock_status": lowest_price.get("stockStatus"),
            "secure_cloud": gpu.get("secureCloud", False),
            "community_cloud": gpu.get("communityCloud", False),
        })

    gpus.sort(key=lambda item: item["price_per_hour"])

    return {
        "success": True,
        "count": len(gpus),
        "gpus": gpus,
    }
