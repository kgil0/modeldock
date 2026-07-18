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

    def _graphql(self, query, variables=None):
        response = requests.post(
            "https://api.runpod.io/graphql",
            headers=self._headers(),
            json={
                "query": query,
                "variables": variables or {},
            },
            timeout=20,
        )

        try:
            result = response.json()
        except ValueError:
            raise RuntimeError(
                f"RunPod GraphQL returned HTTP {response.status_code} "
                "with an invalid JSON response"
            )

        if not response.ok or result.get("errors"):
            details = result.get("errors", result)
            raise RuntimeError(
                f"RunPod GraphQL error ({response.status_code}): {details}"
            )

        return result["data"]


    def list_gpus(self):
        query = """
        query GpuCatalog($priceInput: GpuLowestPriceInput!) {
          gpuTypes {
            id
            displayName
            memoryInGb
            secureCloud
            communityCloud
            lowestPrice(input: $priceInput) {
              stockStatus
              uninterruptablePrice
              availableGpuCounts
            }
          }
        }
        """

        data = self._graphql(
            query,
            {
                "priceInput": {
                    "gpuCount": 1
                }
            },
        )

        return data["gpuTypes"]

    def create_pod_payload(
        self,
        name="modeldock-test",
        gpu_type_id="NVIDIA GeForce RTX 4090",
        image_name="runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04",
    ):
        return {
            "name": name,
            "imageName": image_name,
            "gpuTypeIds": [gpu_type_id],
            "gpuCount": 1,
            "containerDiskInGb": 50,
            "volumeInGb": 20,
            "ports": [
                "11434/http",
                "22/tcp"
            ],
            "env": {
                "MODELDOCK": "true"
            }
        }


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
