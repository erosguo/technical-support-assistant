from sqlalchemy.orm import Session
from app.models.error_pattern import ErrorPattern
from app.services.diagnosis import match_errors

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


class TestErrorMatcher:
    def test_exact_pattern_match(self, db_session: Session):
        ep = ErrorPattern(
            pattern="Connection refused",
            solution="检查端口和防火墙",
            severity="high",
        )
        db_session.add(ep)
        db_session.commit()

        results = match_errors(db_session, "Connection refused on port 8080")
        assert len(results) >= 1
        assert results[0]["pattern"] == "Connection refused"
        assert results[0]["solution"] == "检查端口和防火墙"

    def test_regex_pattern_match(self, db_session: Session):
        ep = ErrorPattern(pattern=r"ERR_\d{5}", solution="参考错误代码手册")
        db_session.add(ep)
        db_session.commit()

        results = match_errors(db_session, "System error: ERR_12345 occurred")
        assert len(results) >= 1
        assert results[0]["pattern"] == r"ERR_\d{5}"

    def test_no_match_returns_empty(self, db_session: Session):
        ep = ErrorPattern(pattern="Disk full", solution="清理磁盘空间")
        db_session.add(ep)
        db_session.commit()

        results = match_errors(db_session, "Everything is working fine")
        assert results == []

    def test_multiple_matches_sorted_by_severity(self, db_session: Session):
        for p in [
            ErrorPattern(pattern="error", severity="low"),
            ErrorPattern(pattern="critical", severity="critical"),
            ErrorPattern(pattern="warning", severity="medium"),
        ]:
            db_session.add(p)
            db_session.flush()
        db_session.commit()

        results = match_errors(db_session, "critical error warning")
        severities = [r["severity"] for r in results]
        assert severities == sorted(severities, key=lambda s: SEVERITY_ORDER[s])

    def test_match_case_insensitive(self, db_session: Session):
        ep = ErrorPattern(pattern="timeout", solution="增加超时设置")
        db_session.add(ep)
        db_session.commit()

        results = match_errors(db_session, "Connection Timeout Error")
        assert len(results) >= 1

    def test_match_returns_metadata(self, db_session: Session):
        ep = ErrorPattern(
            pattern="OOM",
            solution="增加内存",
            severity="critical",
            category="system",
            tags=["memory", "linux"],
        )
        db_session.add(ep)
        db_session.commit()

        results = match_errors(db_session, "OOM killer triggered")
        r = results[0]
        assert r["category"] == "system"
        assert r["tags"] == ["memory", "linux"]
