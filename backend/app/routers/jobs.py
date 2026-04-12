from database import get_cursor, get_db
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
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


class AddJob(BaseModel):
    name: str
    description: str | None = None
    script_path: str
    cron_schedule: str
    timeout_seconds: int | None = 300
    is_active: bool | None = True


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


@router.post("/add")
def add_job(body: AddJob, current_user=Depends(get_current_user), conn=Depends(get_db)):
    user_id = current_user["user_id"]
    job_name = body.name
    job_description = body.description
    script_path = body.script_path
    cron_schedule = body.cron_schedule
    timeout_seconds = body.timeout_seconds
    is_active = False

    with get_cursor(conn) as cur:
        try:
            cur.execute(
                "SELECT id FROM jobs WHERE user_id = %s AND name = %s",
                (user_id, job_name),
            )
            check_dup = cur.fetchall()
            if check_dup:
                raise HTTPException(status_code=409, detail="Job Duplicate")
                return JSONResponse(status=409, content={"message": "Job Duplicate"})

            cur.execute(
                """
                    INSERT INTO jobs (user_id, name, description, script_path, cron_schedule, timeout_seconds, is_active) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """,
                (
                    user_id,
                    job_name,
                    job_description,
                    script_path,
                    cron_schedule,
                    timeout_seconds,
                    is_active,
                ),
            )
            new_job_id = cur.fetchone()["id"]
            conn.commit()
            return {"message": "Job added successfully", "job_id": new_job_id}
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to add job: {str(e)}")
