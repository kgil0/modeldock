import time

from workers.states import TASK_PROVISIONING
from .base import ProvisionStep


class ProvisionGpuStep(ProvisionStep):

    status = TASK_PROVISIONING

    def run(self, task):
        time.sleep(2)
