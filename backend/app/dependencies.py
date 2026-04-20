from functools import wraps
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from schemas.auth import Role
from utils.jwt import verify_token


security = HTTPBearer()


class CurrentUser:
    def __init__(self, user_id: int, username: str, role: Role = Role.USER):
        self.user_id = user_id
        self.username = username
        self.role = role


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> CurrentUser:
    try:
        payload = verify_token(credentials.credentials)
        role = Role(payload.get("role", "user"))
        return CurrentUser(
            user_id=payload["user_id"],
            username=payload["username"],
            role=role,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


def require_role(allowed_roles: list[Role]):
    def decorator(func):
        @wraps(func)
        async def wrapper(current_user: CurrentUser = Depends(get_current_user), *args, **kwargs):
            if current_user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions",
                )
            return func(current_user=current_user, *args, **kwargs)
        return wrapper
    return decorator


AdminOnly = require_role([Role.ADMIN])
UserOrAdmin = require_role([Role.ADMIN, Role.USER])