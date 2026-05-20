from fastapi import FastAPI
from pydantic import BaseModel
import requests

app = FastAPI()

OLLAMA_URL = "http://127.0.0.1:11434"

class ChatRequest(BaseModel):
	model: str
	prompt: str

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
