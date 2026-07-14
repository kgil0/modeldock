import secrets

from .provider import CloudProvider


class RunPodProvider(CloudProvider):
    def list_gpus(self):
        return [
            {
                "id":"runpod-rtx4090",
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

