from sqlalchemy.orm import Session
from app.models.ticket import Ticket


class TestTicket:
    def test_create_ticket(self, db_session: Session):
        ticket = Ticket(title="服务器宕机", description="生产环境服务器无响应")
        db_session.add(ticket)
        db_session.commit()
        assert ticket.id is not None
        assert ticket.title == "服务器宕机"
        assert ticket.description == "生产环境服务器无响应"

    def test_default_status(self, db_session: Session):
        ticket = Ticket(title="测试工单", description="描述")
        db_session.add(ticket)
        db_session.commit()
        assert ticket.status == "open"

    def test_default_priority(self, db_session: Session):
        ticket = Ticket(title="测试工单", description="描述")
        db_session.add(ticket)
        db_session.commit()
        assert ticket.priority == "medium"

    def test_timestamps_auto_set(self, db_session: Session):
        ticket = Ticket(title="测试", description="test")
        db_session.add(ticket)
        db_session.commit()
        assert ticket.created_at is not None
        assert ticket.updated_at is not None

    def test_assignee_optional(self, db_session: Session):
        ticket = Ticket(title="未分配", description="无负责人")
        db_session.add(ticket)
        db_session.commit()
        assert ticket.assigned_to is None
