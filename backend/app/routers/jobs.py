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


class UpdateJob(BaseModel):
    name: str | None = None
    description: str | None = None
    script_path: str | None = None
    cron_schedule: str | None = None
    timeout_seconds: int | None = None
    is_active: bool | None = None
    description: str | None = None
    script_path: str | None = None
    cron_schedule: str | None = None
    timeout_seconds: int | None = None
    is_active: bool | None = None


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


@router.put("/update/{job_id}")
def update_job(
    request: UpdateJob,
    job_id: int,
    current_user=Depends(get_current_user),
    conn=Depends(get_db),
):
    user_id = current_user["user_id"]

    with get_cursor(conn) as cur:
        try:
            # Check if job exists and belongs to user
            cur.execute(
                "SELECT id FROM jobs WHERE user_id = %s AND id = %s", (user_id, job_id)
            )
            check_job = cur.fetchall()
            if not check_job:
                raise HTTPException(status_code=404, detail="Job not found")

            # Collect fields to update
            update_fields = {}
            if request.name is not None:
                update_fields["name"] = request.name
            if request.description is not None:
                update_fields["description"] = request.description
            if request.script_path is not None:
                update_fields["script_path"] = request.script_path
            if request.cron_schedule is not None:
                update_fields["cron_schedule"] = request.cron_schedule
            if request.timeout_seconds is not None:
                update_fields["timeout_seconds"] = request.timeout_seconds
            if request.is_active is not None:
                update_fields["is_active"] = request.is_active

            if not update_fields:
                raise HTTPException(
                    status_code=400, detail="No fields provided for update"
                )

            # Build dynamic UPDATE query
            set_clause = ", ".join([f"{field} = %s" for field in update_fields.keys()])
            values = list(update_fields.values()) + [user_id, job_id]
            query = f"UPDATE jobs SET {set_clause} WHERE user_id = %s AND id = %s"

            cur.execute(query, values)
            if cur.rowcount == 0:
                raise HTTPException(
                    status_code=404, detail="Job not found or no changes made"
                )
            conn.commit()

            return JSONResponse(content={"message": "Job updated successfully"})

        except Exception as e:
            conn.rollback()
            raise HTTPException(
                status_code=500, detail=f"Failed to update job: {str(e)}"
            )


@router.delete("/delete/{job_id}")
def delete_job(
    job_id: int, current_user=Depends(get_current_user), conn=Depends(get_db)
):
    user_id = current_user["user_id"]

    with get_cursor(conn) as cur:
        try:
            cur.execute(
                "SELECT id FROM jobs WHERE user_id = %s AND id = %s", (user_id, job_id)
            )

            check_job = cur.fetchall()
            if not check_job:
                raise HTTPException(status_code=400, detail="Job not found")

            cur.execute(
                "DELETE FROM jobs WHERE user_id = %s AND id = %s", (user_id, job_id)
            )
            conn.commit()

            return JSONResponse(content={"message": "Job deleted"})

        except Exception as e:
            conn.rollback()
            raise HTTPException(
                status_code=500, detail=f"Failed to delete job: {str(e)}"
            )


@router.post("/execute/{job_id}")
def execute_job(job_id: int, current_user=Depends(get_current_user), conn=Depends(get_db)):
    from worker import JobWorker

    user_id = current_user["user_id"]
    job_worker = JobWorker()

    try:
        result = job_worker.run_job(job_id, user_id, conn)
        if result.get("status") == "error":
            raise HTTPException(status_code=404, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
