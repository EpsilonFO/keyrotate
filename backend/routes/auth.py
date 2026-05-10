from fastapi import APIRouter, Cookie, HTTPException, Response, status
from pydantic import BaseModel

from auth import (
    SESSION_COOKIE_NAME,
    SESSION_MAX_AGE_SECONDS,
    create_session_token,
    verify_session_token,
)
from config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginPayload(BaseModel):
    password: str


@router.post("/login")
def login(payload: LoginPayload, response: Response) -> dict:
    if payload.password != settings.app_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
    token = create_session_token()
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
        secure=settings.backend_base_url.startswith("https"),
    )
    return {"ok": True}


@router.post("/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(SESSION_COOKIE_NAME)
    return {"ok": True}


@router.get("/me")
def me(kr_session: str | None = Cookie(default=None)) -> dict:
    if not kr_session or not verify_session_token(kr_session):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return {"authenticated": True}
