import os
from pathlib import Path

from croniter import croniter
from pydantic import BaseModel, Field, field_validator


class JobResponse(BaseModel):
    id: int
    name: str
    description: str | None
    script_path: str
    cron_schedule: str
    timeout_seconds: int
    is_active: bool

    class Config:
        from_attributes = True


class AddJobRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    script_path: str = Field(..., max_length=500)
    cron_schedule: str = Field(..., max_length=100)
    timeout_seconds: int = Field(default=300, ge=1, le=3600)
    is_active: bool = Field(default=False)

    @field_validator("cron_schedule")
    @classmethod
    def validate_cron(cls, v: str) -> str:
        try:
            croniter(v)
        except Exception:
            raise ValueError("Invalid cron expression")
        return v

    @field_validator("script_path")
    @classmethod
    def validate_script_path(cls, v: str) -> str:
        if os.path.isabs(v):
            raise ValueError("Script path must be relative, not absolute")

        if ".." in v:
            raise ValueError("Script path cannot contain parent directory references")

        if not v.endswith(".sh"):
            raise ValueError("Only .sh shell scripts are allowed")

        base_dir = Path(__file__).parent.parent / "scripts"
        full_path = base_dir / v
        if not full_path.exists():
            raise ValueError(f"Script file not found: {v}")

        return v


class UpdateJobRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    script_path: str | None = Field(None, max_length=500)
    cron_schedule: str | None = Field(None, max_length=100)
    timeout_seconds: int | None = Field(None, ge=1, le=3600)
    is_active: bool | None = None

    @field_validator("cron_schedule")
    @classmethod
    def validate_cron(cls, v: str | None) -> str | None:
        if v is None:
            return v
        try:
            croniter(v)
        except Exception:
            raise ValueError("Invalid cron expression")
        return v

    @field_validator("script_path")
    @classmethod
    def validate_script_path(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if os.path.isabs(v):
            raise ValueError("Script path must be relative, not absolute")
        if ".." in v:
            raise ValueError("Script path cannot contain parent directory references")
        if not v.endswith(".sh"):
            raise ValueError("Only .sh shell scripts are allowed")
        base_dir = Path(__file__).parent.parent / "scripts"
        full_path = base_dir / v
        if not full_path.exists():
            raise ValueError(f"Script file not found: {v}")
        return v


class ExecuteJobRequest(BaseModel):
    job_id: int = Field(..., gt=0)