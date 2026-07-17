import os
import secrets

import requests
from dotenv import load_dotenv

from .provider import CloudProvider


load_dotenv()

RUNPOD_API_URL = "https://rest.runpod.io/v1"


class RunPodProvider(CloudProvider):
    def __init__(self):
        self.api_key = os.getenv("RUNPOD_API_KEY", "")

    def _headers(self):
        if not self.api_key:
            raise RuntimeError("RUNPOD_API_KEY is not configured")

        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def list_pods(self):
        response = requests.get(
            f"{RUNPOD_API_URL}/pods",
            headers=self._headers(),
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    def list_gpus(self):
        return [
            {
                "id": "runpod-rtx4090",
                "provider": "runpod",
                "gpu": "RTX4090",
                "vram": "24 GB",
                "price": 0.45,
                "currency": "EUR",
                "region": "EU",
                "available": True,
            }
        ]

    def rent_gpu(self, gpu_id, hours):
        return {
            "provider": "runpod",
            "instance_id": f"rp-{secrets.token_hex(4)}",
            "gpu_id": gpu_id,
            "hours": hours,
            "status": "starting",
        }

    def stop_gpu(self, instance_id):
        return {
            "provider": "runpod",
            "instance_id": instance_id,
            "status": "stopped",
        }

    def delete_gpu(self, instance_id):
        return {
            "provider": "runpod",
            "instance_id": instance_id,
            "status": "deleted",
        }
