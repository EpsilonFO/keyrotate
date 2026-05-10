import logging
from typing import Any

import httpx

from config import settings

logger = logging.getLogger(__name__)


def render_email(key_name: str, provider_name: str, days_left: int, rotation_url: str | None, mark_rotated_url: str) -> tuple[str, str]:
    subject = f"🔑 Your {provider_name} key '{key_name}' expires in {days_left} day{'s' if days_left != 1 else ''}"
    rotate_section = (
        f'<a href="{rotation_url}" style="display:inline-block;padding:12px 20px;background:#1d3a8a;color:#fff;border-radius:6px;text-decoration:none;margin-right:8px">Rotate on {provider_name}</a>'
        if rotation_url
        else ""
    )
    html = f"""
    <div style="font-family:Inter,system-ui,sans-serif;max-width:560px;margin:0 auto;padding:32px;color:#1a1a1a">
      <h1 style="font-family:'Cormorant Garamond',Georgia,serif;font-size:32px;margin:0 0 16px;color:#1d3a8a">Key expiration reminder</h1>
      <p style="font-size:16px;line-height:1.6">Your <strong>{provider_name}</strong> API key <strong>"{key_name}"</strong> will expire in <strong>{days_left} day{'s' if days_left != 1 else ''}</strong>.</p>
      <p style="font-size:16px;line-height:1.6">Rotate it now and update your secrets so nothing breaks.</p>
      <div style="margin:24px 0">
        {rotate_section}
        <a href="{mark_rotated_url}" style="display:inline-block;padding:12px 20px;background:#c75d3a;color:#fff;border-radius:6px;text-decoration:none">I rotated it</a>
      </div>
      <p style="font-size:13px;color:#666;line-height:1.6">After you rotate the key, click "I rotated it" to set the new expiration date. The reminder schedule will reset.</p>
    </div>
    """
    return subject, html


def send_email(to: str, subject: str, html: str) -> None:
    if not settings.resend_api_key:
        logger.info("[email stub] to=%s subject=%s", to, subject)
        logger.info("[email stub] html=%s", html)
        return

    key_prefix = settings.resend_api_key[:8] + "..."
    logger.info("Sending via Resend with key prefix=%s from=%s", key_prefix, settings.resend_from)

    response = httpx.post(
        "https://api.resend.com/emails",
        json={"from": settings.resend_from, "to": [to], "subject": subject, "html": html},
        headers={"Authorization": f"Bearer {settings.resend_api_key}"},
        timeout=10.0,
    )
    if not response.is_success:
        logger.error("Resend %s response: %s", response.status_code, response.text)
        response.raise_for_status()
    logger.info("Email sent to %s: %s", to, subject)
