from database import connection_pool
from fastapi import FastAPI
from routers import auth, users

app = FastAPI()

app.include_router(users.router)
app.include_router(auth.router)
# app.include_router(jobs.router)


@app.on_event("startup")
def startup():
    print("✅ Database pool connected")


@app.on_event("shutdown")
def shutdown():
    connection_pool.closeall()  # close all pool connections on exit
    print("🔌 Database pool closed")


@app.get("/")
def root():
    return {"message": "API is running"}
