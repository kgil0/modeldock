import time

from workers.states import TASK_BOOTING
from .base import ProvisionStep


class WaitForBootStep(ProvisionStep):
    status = TASK_BOOTING

    def run(self, task):
        time.sleep(2)
