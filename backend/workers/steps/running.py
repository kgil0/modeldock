from workers.states import TASK_RUNNING
from .base import ProvisionStep


class MarkRunningStep(ProvisionStep):
    status = TASK_RUNNING

    def run(self, task):
        pass
