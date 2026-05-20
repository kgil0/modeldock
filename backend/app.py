from fastapi import FastAPI
import requests

app = FastAPI()

OLLAMA_URL = "http://127.0.0.1:11434"

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
