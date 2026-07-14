import time

from workers.states import TASK_CLAIMING
from .base import ProvisionStep


class ClaimNodeStep(ProvisionStep):
    status = TASK_CLAIMING

    def run(self, task):
        time.sleep(2)
