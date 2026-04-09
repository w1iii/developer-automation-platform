import asyncpg
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def read_root():
    result = await connect_db()
    name = result[0]["name"]
    return {"Hello": name}


async def connect_db():
    conn = await asyncpg.connect(
        host="localhost", database="dev_auto", user="wii", password=""
    )
    result = await conn.fetch("SELECT * FROM users;")
    await conn.close()
    return result
