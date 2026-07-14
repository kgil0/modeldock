from dataclasses import dataclass, field


@dataclass
class TaskContext:
    task_id: str

    status: str = ""

    provider: str = ""

    instance_id: str = ""

    gpu_id: str = ""

    hours: int = 0

    ssh_host: str = ""

    ssh_user: str = ""

    claim_code: str = ""

    node_id: str = ""

    metadata: dict = field(default_factory=dict)
