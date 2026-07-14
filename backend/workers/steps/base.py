from abc import ABC, abstractmethod




class ProvisionStep(ABC):

    @abstractmethod
    def run(self, task):
        pass
