from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from pydantic import BaseModel
import requests

app = FastAPI()

app.add_middleware(
	CORSMiddleware,
	allow_origins=["http://49.12.244.57:3000"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

OLLAMA_URL = "http://127.0.0.1:11434"

nodes = []

class ChatRequest(BaseModel):
	model: str
	prompt: str

class NodeRequest(BaseModel):
	id: str
	name: str
	status: str
	gpu: str
	models: list[str]

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
		payload = {
			"model": request.model,
			"prompt": request.prompt,
			"stream": False
		}

		response = requests.post(
			f"{OLLAMA_URL}/api/generate",
			json=payload,
			timeout=120
		)
		response.raise_for_status()

		data = response.json()

		return {
			"model": request.model,
			"response": data.get("response","")
		}
	except Exception as e:
		return {
			"status": "error",
			"message": str(e)
		}

@app.post("/register-node")
def register_node(node: NodeRequest):
	global nodes

	existing = next((n for n in nodes if n["id"] ==node.id), None)

	if existing:
		existing.update(node.dict())
	else:
		nodes.append(node.dict())
	return {"status": "registered"}

@app.get("/nodes")
def get_nodes():
	return nodes
