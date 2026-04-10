import bcrypt
from database import get_cursor, get_db
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from utils.jwt import create_access_token

# from datetime import datetime, timedelta

router = APIRouter(prefix="/users", tags=["users"])


class User(BaseModel):
    username: str
    password: str


@router.post("/login")
async def login(body: User, conn=Depends(get_db)):
    try:
        username = body.username
        password = body.password
        print("Logging in...")
        with get_cursor(conn) as cur:
            cur.execute(
                "SELECT id, username, password_hash FROM users WHERE username = %s;",
                (username,),
            )
            data = cur.fetchone()
            if not data:
                raise HTTPException(status_code=401, detail="Invalid credentials")
                return "No user found."

            valid_password = bcrypt.checkpw(
                password.encode("utf-8"), data["password_hash"].encode("utf-8")
            )
            if not valid_password:
                raise HTTPException(status_code=401, detail="Invalid credentials")
                return "Invalid Credentials"

        # Create Token (utils/jwt.py)
        token = create_access_token(data["id"], username)

        return {
            "message": "Login successful",
            "user_id": data["id"],
            "access_token": f"Bearer {token}",
        }
    except Exception:
        raise
        print("Server Error")


@router.post("/register")
def register(body: User, conn=Depends(get_db)):
    try:
        username = body.username
        password = body.password
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        with get_cursor(conn) as cur:
            cur.execute(
                "INSERT INTO users(username, password_hash) VALUES (%s, %s) RETURNING id;",
                (username, password_hash.decode("utf-8")),
            )
            data = cur.fetchone()
            print(data)
            conn.commit()

        return {
            "message": "Registration successful",
            "user_id": data["id"],
        }
    except Exception:
        raise
    finally:
        conn.close()
