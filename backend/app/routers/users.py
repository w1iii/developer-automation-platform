from database import get_cursor, get_db
from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["users"])


class CreateUser(BaseModel):
    username: str
    password_hash: str


@router.get("/")
def get_users(conn=Depends(get_db)):
    users = []
    with get_cursor(conn) as cur:
        cur.execute("SELECT id, username, created_at FROM users")
        data = cur.fetchall()
        for user in data:
            users.append(user["username"])
        return users


@router.get("/{user_id}")
def get_user(user_id: int, conn=Depends(get_db)):
    with get_cursor(conn) as cur:
        cur.execute(
            "SELECT id, username, created_at FROM users WHERE id = %s", (user_id,)
        )
        data = cur.fetchone()
        user_id = data["id"]
        username = data["username"]
        return {"id": user_id, "name": username}


@router.post("/")
def create_user(body: CreateUser, conn=Depends(get_db)):
    with get_cursor(conn) as cur:
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id",
            (body.username, body.password_hash),
        )
        new_id = cur.fetchone()["id"]
        conn.commit()
        return {"id": new_id, "username": body.username}


@router.delete("/{user_id}")
def delete_user(user_id: int, conn=Depends(get_db)):
    with get_cursor(conn) as cur:
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        return {"message": f"User {user_id} deleted"}
