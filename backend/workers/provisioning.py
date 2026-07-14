import json
import sqlite3
import threading
import time
from datetime import datetime

DB_PATH = "modeldock.db"


def start_provisioning(task_id: str):
    thread = threading.Thread(
        target=_provision,
        args=(task_id,),
        daemon=True,
    )
    thread.start()


def _provision(task_id: str):
    # Symulacja uruchamiania GPU
    time.sleep(5)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE tasks
        SET
            status=?,
            updated_at=?,
            result=?
        WHERE id=?
        """,
        (
            "running",
            datetime.utcnow().isoformat(),
            json.dumps({
                "status": "running"
            }),
            task_id,
        ),
    )

    conn.commit()
    conn.close()
