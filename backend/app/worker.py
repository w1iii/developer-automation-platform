from database import get_cursor
from fastapi import HTTPException


class JobWorker:
    def __init__(self):
        print("connected")

    def run_job(self, job_id, user_id, conn) -> dict:
        try:
            with get_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT id, name, script_path, timeout_seconds FROM jobs WHERE id = %s AND user_id = %s;
                """,
                    (job_id, user_id),
                )

                result = cur.fetchone()
                if not result:
                    raise HTTPException(status_code=404, detail="Job not found")

                script_path = result["script_path"]
                timeout_seconds = result["timeout_seconds"]

                exec_result = self.execute_script(script_path, timeout_seconds)
                print("==========================")
                print(f"Result: {exec_result}")
                print("==========================")

            conn.commit()
            return exec_result

        except Exception as e:
            raise HTTPException(status_code=500, detail="Server Error")
            print(e)

    def execute_script(self, script_path, timeout) -> dict:
        print("executing script...")
        # subprocess module
        # return result (stdout, stderr, exit_code)
