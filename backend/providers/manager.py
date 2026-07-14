from .runpod import RunPodProvider
from .tensordock import TensorDockProvider
from .vast import VastProvider


class ProviderManager:
    def __init__(self):
        self.providers = [
            RunPodProvider(),
            TensorDockProvider(),
            VastProvider(),
        ]

    def list_all_gpus(self):
        gpus = []

        for provider in self.providers:
            try:
                gpus.extend(provider.list_gpus())
            except Exception as e:
                print(f"Provider error: {e}")

        return gpus

    def rent_gpu(self, provider_name, gpu_id, hours):
        for provider in self.providers:
            name = provider.__class__.__name__.lower()

            if provider_name.lower() in name:
                return provider.rent_gpu(gpu_id, hours)

        raise ValueError(f"Unknown provider: {provider_name}")
