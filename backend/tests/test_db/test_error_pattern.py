from sqlalchemy.orm import Session
from app.models.error_pattern import ErrorPattern


class TestErrorPattern:
    def test_create_pattern(self, db_session: Session):
        ep = ErrorPattern(pattern="Connection refused", solution="检查端口和防火墙")
        db_session.add(ep)
        db_session.commit()
        assert ep.id is not None
        assert ep.pattern == "Connection refused"
        assert ep.solution == "检查端口和防火墙"

    def test_default_severity(self, db_session: Session):
        ep = ErrorPattern(pattern="Timeout")
        db_session.add(ep)
        db_session.commit()
        assert ep.severity == "medium"

    def test_tags_default_empty_list(self, db_session: Session):
        ep = ErrorPattern(pattern="Error 500")
        db_session.add(ep)
        db_session.commit()
        assert ep.tags == []

    def test_timestamps_auto_set(self, db_session: Session):
        ep = ErrorPattern(pattern="Disk full")
        db_session.add(ep)
        db_session.commit()
        assert ep.created_at is not None
        assert ep.updated_at is not None
