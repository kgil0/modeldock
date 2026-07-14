import time

from workers.states import TASK_INSTALLING_AGENT
from .base import ProvisionStep


class InstallAgentStep(ProvisionStep):
    status = TASK_INSTALLING_AGENT

    def run(self, task):
        time.sleep(2)
