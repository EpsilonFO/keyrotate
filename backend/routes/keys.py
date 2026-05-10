from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from auth import require_auth
from db import get_session
from models import APIKey
from providers import PROVIDERS, default_rotation_url

router = APIRouter(prefix="/api", tags=["keys"], dependencies=[Depends(require_auth)])


class KeyCreate(BaseModel):
    name: str
    provider: str
    expires_at: date
    rotation_url: Optional[str] = None
    notify_days_before: str = "14,7,1"
    notify_channel: str = "email"
    notes: Optional[str] = None


class KeyUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    expires_at: Optional[date] = None
    rotation_url: Optional[str] = None
    notify_days_before: Optional[str] = None
    notify_channel: Optional[str] = None
    notes: Optional[str] = None


class RotatePayload(BaseModel):
    new_expires_at: date


@router.get("/providers")
def list_providers() -> list[dict]:
    return [{"id": k, "name": v["name"], "rotation_url": v["rotation_url"]} for k, v in PROVIDERS.items()]


@router.get("/keys")
def list_keys(session: Session = Depends(get_session)) -> list[APIKey]:
    return list(session.exec(select(APIKey).order_by(APIKey.expires_at)).all())


@router.post("/keys", status_code=201)
def create_key(payload: KeyCreate, session: Session = Depends(get_session)) -> APIKey:
    if payload.provider not in PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unknown provider '{payload.provider}'")
    key = APIKey(
        name=payload.name,
        provider=payload.provider,
        expires_at=payload.expires_at,
        rotation_url=payload.rotation_url or default_rotation_url(payload.provider),
        notify_days_before=payload.notify_days_before,
        notify_channel=payload.notify_channel,
        notes=payload.notes,
    )
    session.add(key)
    session.commit()
    session.refresh(key)
    return key


@router.get("/keys/{key_id}")
def get_key(key_id: int, session: Session = Depends(get_session)) -> APIKey:
    key = session.get(APIKey, key_id)
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    return key


@router.patch("/keys/{key_id}")
def update_key(key_id: int, payload: KeyUpdate, session: Session = Depends(get_session)) -> APIKey:
    key = session.get(APIKey, key_id)
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(key, field, value)
    session.add(key)
    session.commit()
    session.refresh(key)
    return key


@router.delete("/keys/{key_id}", status_code=204)
def delete_key(key_id: int, session: Session = Depends(get_session)) -> None:
    key = session.get(APIKey, key_id)
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    session.delete(key)
    session.commit()


@router.post("/keys/{key_id}/rotate")
def rotate_key(key_id: int, payload: RotatePayload, session: Session = Depends(get_session)) -> APIKey:
    key = session.get(APIKey, key_id)
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    key.expires_at = payload.new_expires_at
    key.last_rotated_at = datetime.utcnow()
    key.notified_thresholds = ""
    key.status = "active"
    session.add(key)
    session.commit()
    session.refresh(key)
    return key
