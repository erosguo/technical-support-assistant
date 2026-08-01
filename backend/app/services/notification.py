"""IM notification integration (F22).

Sends notifications to instant-messaging providers (Feishu, DingTalk, Slack).
No real HTTP calls are performed yet — a mock success response is returned so
escalation flows can be exercised end-to-end.
"""

from datetime import datetime, timezone
from enum import Enum


class NotificationProvider(str, Enum):
    FEISHU = "FEISHU"
    DINGTALK = "DINGTALK"
    SLACK = "SLACK"


def _resolve_provider(provider) -> NotificationProvider:
    if isinstance(provider, NotificationProvider):
        return provider
    try:
        return NotificationProvider(provider)
    except ValueError as exc:
        raise ValueError(f"Unknown notification provider: {provider}") from exc


def format_message(provider, title: str, content: str) -> dict:
    """Build the provider-specific message payload."""
    prov = _resolve_provider(provider)
    body = f"{title}\n{content}"
    if prov == NotificationProvider.FEISHU:
        return {"msg_type": "text", "content": {"text": body}}
    if prov == NotificationProvider.DINGTALK:
        return {"msgtype": "text", "text": {"content": body}}
    # SLACK
    return {"text": body}


def send_notification(provider, webhook_url: str, title: str, content: str) -> dict:
    """Send a notification to an IM provider.

    Formats the message per provider and returns a mock success response. No
    real HTTP call is made.
    """
    prov = _resolve_provider(provider)
    payload = format_message(prov, title, content)
    sent_at = datetime.now(timezone.utc).isoformat()
    return {
        "success": True,
        "provider": prov.value,
        "sent_at": sent_at,
        "payload": payload,
    }


def notify_escalation(
    provider,
    webhook_url: str,
    ticket_title: str,
    ticket_description: str,
) -> dict:
    """Convenience wrapper: notify an IM channel about an escalated ticket."""
    return send_notification(
        provider=provider,
        webhook_url=webhook_url,
        title=ticket_title,
        content=ticket_description,
    )
