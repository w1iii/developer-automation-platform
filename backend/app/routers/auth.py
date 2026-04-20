import bcrypt
from database import get_cursor, get_db
from fastapi import APIRouter, Depends, HTTPException

from dependencies import get_current_user
from schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from utils.jwt import create_access_token
from utils.logging import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, conn=Depends(get_db)):
    try:
        with get_cursor(conn) as cur:
            cur.execute(
                "SELECT id, username, role, password_hash FROM users WHERE username = %s;",
                (body.username,),
            )
            data = cur.fetchone()
            if not data:
                logger.warning(f"Login failed: user not found - {body.username}")
                raise HTTPException(status_code=401, detail="Invalid credentials")

            valid_password = bcrypt.checkpw(
                body.password.encode("utf-8"), data["password_hash"].encode("utf-8")
            )
            if not valid_password:
                logger.warning(f"Login failed: invalid password - {body.username}")
                raise HTTPException(status_code=401, detail="Invalid credentials")

        role = data.get("role", "user")
        token = create_access_token(data["id"], body.username, role)

        logger.info(f"User {body.username} logged in successfully")
        return TokenResponse(
            message="Login successful",
            user_id=data["id"],
            access_token=f"Bearer {token}",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/register")
def register(body: RegisterRequest, conn=Depends(get_db)):
    try:
        password_hash = bcrypt.hashpw(body.password.encode("utf-8"), bcrypt.gensalt())
        with get_cursor(conn) as cur:
            cur.execute(
                "INSERT INTO users(username, password_hash, role) VALUES (%s, %s, %s) RETURNING id;",
                (body.username, password_hash.decode("utf-8"), "user"),
            )
            data = cur.fetchone()
            conn.commit()

        logger.info(f"User {body.username} registered successfully")
        return {
            "message": "Registration successful",
            "user_id": data["id"],
        }
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/logout")
def logout(current_user=Depends(get_current_user)):
    logger.info(f"User {current_user.username} logged out")
    return {"message": f"{current_user.username} logged out"}