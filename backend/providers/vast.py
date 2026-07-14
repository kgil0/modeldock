import secrets

from .provider import CloudProvider


class VastProvider(CloudProvider):
    def list_gpus(self):
        return [
            {
                 "id": "vast-h100",
                 "provider": "Vast.ai",
                 "gpu": "H100",
                 "vram": "80 GB HBM",
                 "price": 3.10,
                 "currency": "EUR",
                 "region": "EU",
                 "available": False,
            }
         ]

    def rent_gpu(self, gpu_id, hours):
        return {
            "provider": "Vast.ai",
            "instance_id": f"va-{secrets.token_hex(4)}",
            "gpu_id": gpu_id,
            "hours": hours,
            "status": "starting",
        }

    def stop_gpu(self, instance_id):
        return {"status": "stopped"}

    def delete_gpu(self, instance_id):
        return {"status": "deleted"}
