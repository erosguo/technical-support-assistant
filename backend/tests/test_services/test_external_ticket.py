import pytest
from sqlalchemy.orm import Session

from app.services.external_ticket import (
    ExternalTicketProvider,
    get_external_ticket_config,
    sync_ticket_to_external,
)
from app.services.ticket import create_ticket


class TestExternalTicket:
    def test_sync_ticket_to_jira(self, db_session: Session):
        ticket = create_ticket(
            session=db_session,
            title="服务器宕机",
            description="生产环境无响应",
            priority="high",
        )
        result = sync_ticket_to_external(
            session=db_session,
            ticket_id=ticket.id,
            provider=ExternalTicketProvider.JIRA,
            config={},
        )
        assert result["status"] == "synced"
        assert result["provider"] == "JIRA"
        assert result["external_id"]
        assert result["external_id"].startswith("jira-")

    def test_sync_ticket_to_zendesk(self, db_session: Session):
        ticket = create_ticket(
            session=db_session,
            title="登录失败",
            description="用户无法登录系统",
            priority="urgent",
        )
        result = sync_ticket_to_external(
            session=db_session,
            ticket_id=ticket.id,
            provider=ExternalTicketProvider.ZENDESK,
            config={},
        )
        assert result["status"] == "synced"
        assert result["provider"] == "ZENDESK"
        assert result["external_id"]
        assert result["external_id"].startswith("zendesk-")

    def test_sync_ticket_not_found(self, db_session: Session):
        with pytest.raises(ValueError):
            sync_ticket_to_external(
                session=db_session,
                ticket_id="nonexistent-id",
                provider=ExternalTicketProvider.JIRA,
                config={},
            )

    def test_sync_ticket_to_unknown_provider(self, db_session: Session):
        ticket = create_ticket(
            session=db_session,
            title="未知提供商",
            description="desc",
        )
        with pytest.raises(ValueError):
            sync_ticket_to_external(
                session=db_session,
                ticket_id=ticket.id,
                provider="UNKNOWN_PROVIDER",
                config={},
            )

    def test_get_external_ticket_config_jira(self, db_session: Session):
        config = get_external_ticket_config(
            session=db_session, provider=ExternalTicketProvider.JIRA
        )
        assert config
        assert "base_url" in config
