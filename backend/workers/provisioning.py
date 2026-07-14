from workers.context import TaskContext
from workers.pipeline import PIPELINE
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
    for step in PIPELINE:
        time.sleep(2)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT result
            FROM tasks
            WHERE id=?
            """,
            (task_id,),
        )

        row = cursor.fetchone()
        current_result = json.loads(row[0]) if row and row[0] else {}

        context = TaskContext(
            task_id=task_id,
            status=current_result.get("status",""),
            provider=current_result.get("provider",""),
            instance_id=current_result.get("instance_id",""),
            gpu_id=current_result.get("gpu_id",""),
            hours=current_result.get("hours",0),
        )

        context.metadata = current_result

        step.run(context)

        context.status = step.status
        context.metadata["status"] = step.status

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
                step.status,
                datetime.utcnow().isoformat(),
                json.dumps(context.metadata),
                task_id,
            ),
        )

        conn.commit()
        conn.close()
