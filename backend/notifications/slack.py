import logging

import httpx

from config import settings

logger = logging.getLogger(__name__)


def send_slack(key_name: str, provider_name: str, days_left: int, rotation_url: str | None, mark_rotated_url: str) -> None:
    if not settings.slack_webhook_url:
        logger.info("[slack stub] key=%s days_left=%s", key_name, days_left)
        return

    text = f":key: *{provider_name}* key `{key_name}` expires in *{days_left} day{'s' if days_left != 1 else ''}*."
    blocks: list[dict] = [
        {"type": "section", "text": {"type": "mrkdwn", "text": text}},
    ]
    actions: list[dict] = []
    if rotation_url:
        actions.append({"type": "button", "text": {"type": "plain_text", "text": f"Rotate on {provider_name}"}, "url": rotation_url})
    actions.append({"type": "button", "text": {"type": "plain_text", "text": "I rotated it"}, "url": mark_rotated_url, "style": "primary"})
    blocks.append({"type": "actions", "elements": actions})

    try:
        response = httpx.post(settings.slack_webhook_url, json={"text": text, "blocks": blocks}, timeout=10.0)
        response.raise_for_status()
        logger.info("Slack sent: %s", text)
    except httpx.HTTPError as exc:
        logger.error("Failed to send Slack: %s", exc)
