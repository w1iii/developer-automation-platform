from database import get_cursor, get_db
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from dependencies import CurrentUser, get_current_user
from schemas.jobs import AddJobRequest, ExecuteJobRequest, JobResponse, UpdateJobRequest
from utils.logging import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/")
def get_jobs(current_user: CurrentUser = Depends(get_current_user), conn=Depends(get_db)):
    try:
        with get_cursor(conn) as cur:
            cur.execute(
                """
                SELECT id, name, description, script_path, cron_schedule, timeout_seconds, is_active 
                FROM jobs WHERE user_id = %s
                """,
                (current_user.user_id,),
            )
            data = cur.fetchall()
            jobs = [JobResponse(**job) for job in data]
            return [j.model_dump() for j in jobs]
    except Exception as e:
        logger.error(f"Get jobs error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/add")
def add_job(body: AddJobRequest, current_user: CurrentUser = Depends(get_current_user), conn=Depends(get_db)):
    try:
        with get_cursor(conn) as cur:
            cur.execute(
                "SELECT id FROM jobs WHERE user_id = %s AND name = %s",
                (current_user.user_id, body.name),
            )
            check_dup = cur.fetchall()
            if check_dup:
                raise HTTPException(status_code=409, detail="Job with this name already exists")

            cur.execute(
                """
                    INSERT INTO jobs (user_id, name, description, script_path, cron_schedule, timeout_seconds, is_active) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """,
                (
                    current_user.user_id,
                    body.name,
                    body.description,
                    body.script_path,
                    body.cron_schedule,
                    body.timeout_seconds,
                    body.is_active,
                ),
            )
            new_job_id = cur.fetchone()["id"]
            conn.commit()

        logger.info(f"Job {body.name} created by user {current_user.user_id}")
        return {"message": "Job added successfully", "job_id": new_job_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add job error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/update/{job_id}")
def update_job(
    request: UpdateJobRequest,
    job_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    conn=Depends(get_db),
):
    try:
        with get_cursor(conn) as cur:
            cur.execute(
                "SELECT id FROM jobs WHERE user_id = %s AND id = %s",
                (current_user.user_id, job_id),
            )
            check_job = cur.fetchone()
            if not check_job:
                raise HTTPException(status_code=404, detail="Job not found")

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
                raise HTTPException(status_code=400, detail="No fields provided for update")

            set_clause = ", ".join([f"{field} = %s" for field in update_fields.keys()])
            values = list(update_fields.values()) + [current_user.user_id, job_id]
            query = f"UPDATE jobs SET {set_clause} WHERE user_id = %s AND id = %s"

            cur.execute(query, values)
            conn.commit()

        logger.info(f"Job {job_id} updated by user {current_user.user_id}")
        return JSONResponse(content={"message": "Job updated successfully"})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update job error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/delete/{job_id}")
def delete_job(job_id: int, current_user: CurrentUser = Depends(get_current_user), conn=Depends(get_db)):
    try:
        with get_cursor(conn) as cur:
            cur.execute(
                "SELECT id FROM jobs WHERE user_id = %s AND id = %s",
                (current_user.user_id, job_id),
            )
            check_job = cur.fetchone()
            if not check_job:
                raise HTTPException(status_code=404, detail="Job not found")

            cur.execute(
                "DELETE FROM jobs WHERE user_id = %s AND id = %s",
                (current_user.user_id, job_id),
            )
            conn.commit()

        logger.info(f"Job {job_id} deleted by user {current_user.user_id}")
        return JSONResponse(content={"message": "Job deleted"})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete job error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/execute")
def execute_job(request: ExecuteJobRequest, current_user: CurrentUser = Depends(get_current_user), conn=Depends(get_db)):
    from worker import JobWorker

    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, user_id, script_path FROM jobs WHERE id = %s AND user_id = %s",
            (request.job_id, current_user.user_id),
        )
        job = cur.fetchone()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        job_worker = JobWorker()
        result = job_worker.run_job(request.job_id, current_user.user_id, conn)

        if result.get("status") == "error":
            raise HTTPException(status_code=404, detail=result.get("message"))

        logger.info(f"Job {request.job_id} executed by user {current_user.user_id}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Execute job error: {e}")
        raise HTTPException(status_code=500, detail=str(e))