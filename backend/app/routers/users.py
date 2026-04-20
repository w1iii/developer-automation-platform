from database import get_cursor, get_db
from dependencies import AdminOnly
from fastapi import APIRouter, Depends, HTTPException
from schemas.auth import Role
from schemas.users import CreateUserRequest, UserResponse
from utils.logging import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", dependencies=[Depends(AdminOnly)])
def get_users(conn=Depends(get_db)):
    try:
        with get_cursor(conn) as cur:
            cur.execute("SELECT id, username, role, created_at FROM users")
            data = cur.fetchall()
            users = [
                UserResponse(
                    id=row["id"],
                    username=row["username"],
                    role=Role(row.get("role", "user")),
                    created_at=row["created_at"],
                )
                for row in data
            ]
            return {"users": [u.model_dump() for u in users]}
    except Exception as e:
        logger.error(f"Get users error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{user_id}")
def get_user(user_id: int, conn=Depends(get_db)):
    with get_cursor(conn) as cur:
        cur.execute(
            "SELECT id, username, role, created_at FROM users WHERE id = %s", (user_id,)
        )
        data = cur.fetchone()
        if not data:
            raise HTTPException(status_code=404, detail="User not found")
        return UserResponse(
            id=data["id"],
            username=data["username"],
            role=Role(data.get("role", "user")),
            created_at=data["created_at"],
        ).model_dump()


@router.post("/", dependencies=[Depends(AdminOnly)])
def create_user(body: CreateUserRequest, conn=Depends(get_db)):
    import bcrypt

    password_hash = bcrypt.hashpw(body.password.encode("utf-8"), bcrypt.gensalt())
    with get_cursor(conn) as cur:
        cur.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s) RETURNING id",
            (body.username, password_hash.decode("utf-8"), body.role.value),
        )
        new_id = cur.fetchone()["id"]
        conn.commit()
    logger.info(f"User {body.username} created by admin")
    return {"id": new_id, "username": body.username}


@router.delete("/{user_id}", dependencies=[Depends(AdminOnly)])
def delete_user(user_id: int, conn=Depends(get_db)):
    with get_cursor(conn) as cur:
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
    logger.info(f"User {user_id} deleted by admin")
    return {"message": f"User {user_id} deleted"}
