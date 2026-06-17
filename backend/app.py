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

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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

                elif seconds_since_seen <= 60:
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

    user_id = "admin"

    if node.claim_code:
        cursor.execute(
            "SELECT user_id FROM claim_codes WHERE code = ? AND used = 0",
            (node.claim_code,)
        )

        result = cursor.fetchone()

        if result:
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
    conn.close()

    if not user or not pwd_context.verify(request.password, user[2]):

        return {
            "status": "error",
            "message": "Invalid login"
        }

    return {
        "status": "ok",
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
