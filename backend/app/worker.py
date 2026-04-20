import subprocess
from datetime import datetime
from pathlib import Path

from database import get_cursor

SCRIPTS_DIR = Path(__file__).parent / "scripts/"


class JobWorker:
    def run_job(self, job_id: int, user_id: int, conn) -> dict:
        with get_cursor(conn) as cur:
            cur.execute(
                """
                SELECT id, name, script_path, timeout_seconds, is_active 
                FROM jobs WHERE id = %s AND user_id = %s;
                """,
                (job_id, user_id),
            )

            job = cur.fetchone()
            if not job:
                return {"status": "error", "message": "Job not found"}

            if not job["is_active"]:
                return {"status": "error", "message": "Job is not active"}

            script_path_str = job["script_path"].lstrip("/")
            script_path = SCRIPTS_DIR / script_path_str
            print(SCRIPTS_DIR)
            timeout_seconds = job["timeout_seconds"] or 300

            cur.execute(
                """
                INSERT INTO job_executions (job_id, status, started_at)
                VALUES (%s, 'running', %s)
                RETURNING id;
                """,
                (job_id, datetime.utcnow()),
            )
            execution = cur.fetchone()
            execution_id = execution["id"]

            result = self.execute_script(str(script_path), timeout_seconds)

            status = "completed" if result["exit_code"] == 0 else "failed"
            if result["timeout"]:
                status = "timeout"

            cur.execute(
                """
                UPDATE job_executions
                SET status = %s,
                    ended_at = %s,
                    stdout = %s,
                    stderr = %s,
                    exit_code = %s
                WHERE id = %s;
                """,
                (
                    status,
                    datetime.utcnow(),
                    result["stdout"],
                    result["stderr"],
                    result["exit_code"],
                    execution_id,
                ),
            )

            conn.commit()

            return {
                "execution_id": execution_id,
                "status": status,
                "exit_code": result["exit_code"],
                "timeout": result["timeout"],
            }

    def execute_script(self, script_path: str, timeout: int) -> dict:
        try:
            result = subprocess.run(
                [script_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=True,
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "timeout": False,
            }
        except subprocess.TimeoutExpired as e:
            return {
                "stdout": e.stdout.decode() if e.stdout else "",
                "stderr": e.stderr.decode() if e.stderr else "",
                "exit_code": 124,
                "timeout": True,
            }
        except FileNotFoundError:
            return {
                "stdout": "",
                "stderr": f"Script not found: {script_path}",
                "exit_code": 127,
                "timeout": False,
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": f"Script error: {e}",
                "exit_code": 1,
                "timeout": False,
            }
