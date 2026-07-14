from abc import ABC, abstractmethod

class CloudProvider(ABC):
    @abstractmethod
    def list_gpus(self):
        pass

    @abstractmethod
    def rent_gpu(self, gpu_id, hours):
        pass

    @abstractmethod
    def stop_gpu(self, instance_id):
        pass

    @abstractmethod
    def delete_gpu(self, instance_id):
        pass
