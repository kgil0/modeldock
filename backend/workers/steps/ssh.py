import time

from workers.states import TASK_WAITING_FOR_SSH
from .base import ProvisionStep


class WaitForSshStep(ProvisionStep):
    status = TASK_WAITING_FOR_SSH

    def run(self, task):
        time.sleep(2)
