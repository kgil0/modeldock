from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import requests
import sqlite3
import json
from datetime import datetime

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


class ChatRequest(BaseModel):
    node_id: str
    model: str
    prompt: str


class NodeRequest(BaseModel):
    id: str
    name: str
    status: str
    gpu: str
    endpoint: str
    models: list[str]
    cpu_percent: float
    ram_percent: float
    disk_percent: float
    uptime_seconds: float


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

    conn.commit()
    conn.close()


def get_all_nodes():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM nodes")
    rows = cursor.fetchall()
    conn.close()

    nodes = []
    for row in rows:
        nodes.append({
            "id": row[0],
            "name": row[1],
            "status": row[2],
            "gpu": row[3],
            "endpoint": row[4],
            "models": json.loads(row[5]),
            "cpu_percent": row[6],
            "ram_percent": row[7],
            "disk_percent": row[8],
            "uptime_seconds": row[9],
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
def register_node(node: NodeRequest):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO nodes (
            id, name, status, gpu, endpoint, models,
            cpu_percent, ram_percent, disk_percent, uptime_seconds
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
    ))

    conn.commit()
    conn.close()

    return {"status": "registered"}


@app.get("/nodes")
def get_nodes():
    return get_all_nodes()

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

@app.get("/history")
def get_history():

    try:
        with open ("history.json", "r") as f:
            history = json.load(f)

        return history[::-1]

    except:
        return []
