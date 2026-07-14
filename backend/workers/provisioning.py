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
    for status in PIPELINE:
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

        current_result["status"] = status

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
                status,
                datetime.utcnow().isoformat(),
                json.dumps(current_result),
                task_id,
            ),
        )

        conn.commit()
        conn.close()
