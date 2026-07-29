from sqlalchemy.orm import Session
from app.services.ticket import create_ticket, get_ticket, list_tickets, update_ticket


class TestTicketService:
    def test_create_ticket(self, db_session: Session):
        ticket = create_ticket(
            session=db_session,
            title="服务器宕机",
            description="生产环境无响应",
            priority="critical",
        )
        assert ticket.id is not None
        assert ticket.title == "服务器宕机"
        assert ticket.status == "open"
        assert ticket.priority == "critical"

    def test_get_ticket_by_id(self, db_session: Session):
        created = create_ticket(session=db_session, title="测试", description="desc")
        fetched = get_ticket(session=db_session, ticket_id=created.id)
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.title == "测试"

    def test_get_ticket_not_found(self, db_session: Session):
        fetched = get_ticket(session=db_session, ticket_id="nonexistent")
        assert fetched is None

    def test_list_tickets(self, db_session: Session):
        create_ticket(session=db_session, title="工单A", description="descA")
        create_ticket(session=db_session, title="工单B", description="descB")
        tickets = list_tickets(session=db_session)
        assert len(tickets) >= 2

    def test_list_tickets_filter_by_status(self, db_session: Session):
        create_ticket(session=db_session, title="开放", description="d")
        t2 = create_ticket(session=db_session, title="关闭", description="d")
        update_ticket(session=db_session, ticket_id=t2.id, status="closed")
        open_tickets = list_tickets(session=db_session, status="open")
        assert all(t.status == "open" for t in open_tickets)

    def test_update_ticket_status(self, db_session: Session):
        ticket = create_ticket(session=db_session, title="更新测试", description="d")
        updated = update_ticket(
            session=db_session, ticket_id=ticket.id, status="in_progress"
        )
        assert updated.status == "in_progress"

    def test_update_ticket_assignee(self, db_session: Session):
        ticket = create_ticket(session=db_session, title="分配测试", description="d")
        updated = update_ticket(
            session=db_session, ticket_id=ticket.id, assigned_to="张三"
        )
        assert updated.assigned_to == "张三"
