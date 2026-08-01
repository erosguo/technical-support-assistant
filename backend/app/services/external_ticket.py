"""External ticket integration (F21).

Synchronizes internal tickets to external ticketing providers (Jira, Zendesk,
Service Now). No real HTTP calls are performed yet — a mock external id is
returned so the rest of the pipeline can be exercised end-to-end.
"""

from enum import Enum

from sqlalchemy.orm import Session

from app.models.ticket import Ticket


class ExternalTicketProvider(str, Enum):
    JIRA = "JIRA"
    ZENDESK = "ZENDESK"
    SERVICENOW = "SERVICENOW"


# Simple in-memory provider config (no DB model needed for the MVP).
EXTERNAL_TICKET_CONFIGS: dict[ExternalTicketProvider, dict] = {
    ExternalTicketProvider.JIRA: {
        "base_url": "https://example.atlassian.net",
        "project_key": "SUP",
    },
    ExternalTicketProvider.ZENDESK: {
        "base_url": "https://example.zendesk.com",
        "subdomain": "support",
    },
    ExternalTicketProvider.SERVICENOW: {
        "base_url": "https://example.service-now.com",
        "table": "incident",
    },
}


def _resolve_provider(provider) -> ExternalTicketProvider:
    if isinstance(provider, ExternalTicketProvider):
        return provider
    try:
        return ExternalTicketProvider(provider)
    except ValueError as exc:
        raise ValueError(f"Unknown external ticket provider: {provider}") from exc


def get_external_ticket_config(session: Session, provider) -> dict:
    """Return the static config dict for ``provider``.

    ``session`` is accepted for API symmetry with other services and future
    DB-backed config; the current implementation reads from an in-memory dict.
    """
    prov = _resolve_provider(provider)
    return EXTERNAL_TICKET_CONFIGS.get(prov, {}).copy()


def _build_payload(provider: ExternalTicketProvider, ticket: Ticket) -> dict:
    if provider == ExternalTicketProvider.JIRA:
        return {
            "fields": {
                "summary": ticket.title,
                "description": ticket.description,
                "priority": ticket.priority,
            }
        }
    if provider == ExternalTicketProvider.ZENDESK:
        return {
            "subject": ticket.title,
            "comment": ticket.description,
            "priority": ticket.priority,
        }
    # ServiceNow incident table format.
    return {
        "short_description": ticket.title,
        "description": ticket.description,
        "priority": ticket.priority,
    }


def sync_ticket_to_external(
    session: Session,
    ticket_id: str,
    provider,
    config: dict | None = None,
) -> dict:
    """Sync an internal ticket to an external provider.

    Reads the ticket from the database, maps it to the provider-specific
    payload, and returns a mock ``external_id``. No real HTTP call is made.
    """
    prov = _resolve_provider(provider)

    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        raise ValueError(f"Ticket not found: {ticket_id}")

    payload = _build_payload(prov, ticket)

    # Mock external id — in production this would come from the provider API.
    external_id = f"{prov.value.lower()}-{ticket.id}"

    return {
        "external_id": external_id,
        "provider": prov.value,
        "status": "synced",
        "payload": payload,
    }
