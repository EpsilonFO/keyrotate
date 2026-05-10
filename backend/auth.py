from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from fastapi import Cookie, HTTPException, status

from config import settings

SESSION_COOKIE_NAME = "kr_session"
SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 30  # 30 days
ROTATION_TOKEN_MAX_AGE_SECONDS = 60 * 60 * 24 * 30  # 30 days

_session_serializer = URLSafeTimedSerializer(settings.secret_key, salt="session")
_rotation_serializer = URLSafeTimedSerializer(settings.secret_key, salt="rotation")


def create_session_token() -> str:
    return _session_serializer.dumps({"sub": "default"})


def verify_session_token(token: str) -> bool:
    try:
        _session_serializer.loads(token, max_age=SESSION_MAX_AGE_SECONDS)
        return True
    except (BadSignature, SignatureExpired):
        return False


def require_auth(kr_session: str | None = Cookie(default=None)) -> None:
    if not kr_session or not verify_session_token(kr_session):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


def create_rotation_token(key_id: int, threshold: int) -> str:
    return _rotation_serializer.dumps({"key_id": key_id, "threshold": threshold})


def verify_rotation_token(token: str) -> dict | None:
    try:
        return _rotation_serializer.loads(token, max_age=ROTATION_TOKEN_MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired):
        return None
