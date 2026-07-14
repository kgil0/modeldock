from workers.steps.provision import ProvisionGpuStep
from workers.steps.boot import WaitForBootStep
from workers.steps.ssh import WaitForSshStep
from workers.steps.install_agent import InstallAgentStep
from workers.steps.claim import ClaimNodeStep
from workers.steps.running import MarkRunningStep


PIPELINE = [
    ProvisionGpuStep(),
    WaitForBootStep(),
    WaitForSshStep(),
    InstallAgentStep(),
    ClaimNodeStep(),
    MarkRunningStep(),
]
