from database import connection_pool
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from routers import auth, users
from utils.jwt import verify_token

app = FastAPI()

app.include_router(users.router)
app.include_router(auth.router)
# app.include_router(jobs.router)

EXCLUDED_ROUTES = ["/auth/login", "/auth/register", "/auth/logout"]

current_user = None


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.url.path in EXCLUDED_ROUTES:
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


@app.on_event("startup")
def startup():
    print("✅ Database pool connected")


@app.on_event("shutdown")
def shutdown():
    connection_pool.closeall()  # close all pool connections on exit
    print("🔌 Database pool closed")


@app.get("/me")
def root():
    return {"message": "API is running"}
