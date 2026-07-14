import secrets
from .provider import CloudProvider


class TensorDockProvider(CloudProvider):
    def list_gpus(self):
        return [
            {
                 "id": "tensordock-a100",
                 "provider": "TensorDock",
                 "gpu": "A100",
                 "vram": "80 GB",
                 "price": 1.80,
                 "currency": "EUR",
                 "region": "US",
                 "available": True,
            }
        ]

    def rent_gpu(self, gpu_id, hours):
        return {
            "provider": "TensorDock",
            "instance_id": f"td-{secrets.token_hex(4)}",
            "gpu_id": gpu_id,
            "hours": hours,
            "status": "starting",
        }

    def stop_gpu(self, instance_id):
        return {"status": "stopped"}

    def delete_gpu(self, instance_id):
        return {"status": "deleted"}
