from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from database import connection_pool
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routers import auth, jobs, users
from utils.jwt import verify_token
from utils.logging import setup_logger

logger = setup_logger(__name__)

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

app = FastAPI()
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded: {exc.detail}"},
    )


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    excluded = ["/auth/login", "/auth/register", "/auth/logout", "/health", "/ready", "/docs", "/openapi.json"]
    if request.url.path in excluded or request.url.path.startswith("/docs"):
        return await call_next(request)

    token = request.headers.get("Authorization")

    if not token or not token.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})

    try:
        payload = verify_token(token.split(" ")[1])
        request.state.user = payload
    except Exception:
        return JSONResponse(status_code=401, content={"detail": "Invalid Token"})

    return await call_next(request)


def rate_limit_exceeded_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please try again later."},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:5000",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(users.router)
app.include_router(auth.router)
app.include_router(jobs.router)


@app.on_event("startup")
def startup():
    logger.info("Database pool connected")


@app.on_event("shutdown")
def shutdown():
    connection_pool.closeall()
    logger.info("Database pool closed")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    return {"status": "ready", "database": "connected"}
