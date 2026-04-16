import logging
from contextlib import asynccontextmanager
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from croniter import croniter
from database import connection_pool, get_cursor
from fastapi import FastAPI
from worker import JobWorker


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()
worker = JobWorker()


def parse_cron_schedule(cron_expr: str) -> dict:
    base_time = datetime.now()
    iter = croniter(cron_expr, base_time)
    next_run = iter.get_next(datetime)
    return {"next_run_time": next_run}


def get_db_connection():
    return connection_pool.getconn()


def run_scheduled_job(job_id: int, user_id: int, cron_expr: str):
    logger.info(f"[Scheduler] Running job {job_id} (cron: {cron_expr})")
    conn = get_db_connection()
    try:
        result = worker.run_job(job_id, user_id, conn)
        logger.info(f"[Scheduler] Job {job_id} completed: {result}")
    except Exception as e:
        logger.error(f"[Scheduler] Job {job_id} failed: {e}")
    finally:
        connection_pool.putconn(conn)


def load_jobs_from_db():
    conn = get_db_connection()
    try:
        with get_cursor(conn) as cur:
            cur.execute(
                """
                SELECT id, user_id, name, script_path, cron_schedule, is_active 
                FROM jobs WHERE is_active = TRUE
                """
            )
            jobs = cur.fetchall()

        for job in jobs:
            job_id = job["id"]
            job_key = f"job_{job_id}"

            if scheduler.get_job(job_key):
                scheduler.reschedule_job(job_key, trigger=CronTrigger.from_crontab(job["cron_schedule"]))
            else:
                scheduler.add_job(
                    run_scheduled_job,
                    trigger=CronTrigger.from_crontab(job["cron_schedule"]),
                    id=job_key,
                    args=[job_id, job["user_id"], job["cron_schedule"]],
                    replace_existing=True,
                )
            logger.info(f"[Scheduler] Loaded job: {job['name']} ({job_key})")
    finally:
        connection_pool.putconn(conn)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("[Scheduler] Starting...")
    load_jobs_from_db()
    scheduler.start()
    logger.info("[Scheduler] Started successfully")
    yield
    scheduler.shutdown()
    logger.info("[Scheduler] Stopped")


app = FastAPI(title="Job Scheduler", lifespan=lifespan)


@app.get("/health")
def health():
    jobs = scheduler.get_jobs()
    return {
        "status": "running",
        "scheduled_jobs": len(jobs),
        "next_run_times": [{"id": j.id, "next_run": str(j.next_run_time)} for j in jobs],
    }


@app.post("/reload")
def reload():
    load_jobs_from_db()
    return {"message": "Jobs reloaded"}
