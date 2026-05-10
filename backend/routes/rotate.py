from datetime import date, datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from auth import verify_rotation_token
from config import settings
from db import get_session
from models import APIKey
from providers import PROVIDERS

router = APIRouter(tags=["rotate"])

templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


@router.get("/rotate/{token}", response_class=HTMLResponse)
def rotation_page(token: str, request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    payload = verify_rotation_token(token)
    if not payload:
        raise HTTPException(status_code=400, detail="Invalid or expired link")
    key = session.get(APIKey, payload["key_id"])
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    suggested_date = (date.today() + timedelta(days=90)).isoformat()
    provider_name = PROVIDERS.get(key.provider, {}).get("name", key.provider)
    return templates.TemplateResponse(
        request,
        "rotate.html",
        {
            "key": key,
            "provider_name": provider_name,
            "token": token,
            "suggested_date": suggested_date,
        },
    )


@router.post("/rotate/{token}", response_class=HTMLResponse)
def confirm_rotation(
    token: str,
    request: Request,
    new_expires_at: date = Form(...),
    session: Session = Depends(get_session),
) -> HTMLResponse:
    payload = verify_rotation_token(token)
    if not payload:
        raise HTTPException(status_code=400, detail="Invalid or expired link")
    key = session.get(APIKey, payload["key_id"])
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    key.expires_at = new_expires_at
    key.last_rotated_at = datetime.utcnow()
    key.notified_thresholds = ""
    key.status = "active"
    session.add(key)
    session.commit()
    session.refresh(key)
    return templates.TemplateResponse(
        request,
        "rotated.html",
        {"key": key, "app_base_url": settings.app_base_url},
    )
