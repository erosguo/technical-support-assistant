from sqlalchemy import text
from sqlalchemy.orm import Session


class TestDatabaseSession:
    def test_session_executes_query(self, db_session: Session):
        result = db_session.execute(text("SELECT 1 as val"))
        row = result.one()
        assert row.val == 1

    def test_session_rollback_on_exit(self, db_session: Session):
        db_session.execute(text("CREATE TEMP TABLE tmp_test (id INT)"))
        db_session.execute(text("INSERT INTO tmp_test VALUES (1)"))
        result = db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1
