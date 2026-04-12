from database import get_cursor, get_db
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from routers.auth import get_current_user

router = APIRouter(prefix="/jobs", tags=["jobs"])


class Jobs(BaseModel):
    id: int
    name: str
    description: str
    script_path: str
    cron_schedule: str
    timeout_seconds: int
    is_active: bool


@router.get("/")
def get_jobs(current_user=Depends(get_current_user), conn=Depends(get_db)):
    # user_id = current_user["user_id"]
    jobs = []
    with get_cursor(conn) as cur:
        # cur.execute(
        #     "SELECT id, name, description, script_path, cron_schedule, timeout_seconds, is_active FROM jobs WHERE user_id = %s",
        #     (user_id,),
        # )
        cur.execute(
            "SELECT id, name, description, script_path, cron_schedule, timeout_seconds, is_active FROM jobs WHERE user_id = 1",
        )
        data = cur.fetchall()
        for job in data:
            jobs.append(job)

        return jobs
