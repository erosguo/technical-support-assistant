"""DiagnosisFlow model tests — Phase 2 Task 2.7."""


class TestDiagnosisFlow:
    def test_create_flow(self, db_session):
        from app.models.diagnosis_flow import DiagnosisFlow

        flow = DiagnosisFlow(
            name="SSL 诊断流程",
            description="SSL 证书问题诊断",
            steps=[{"id": "s1", "title": "检查证书有效期", "next_step": "s2"}],
        )
        db_session.add(flow)
        db_session.commit()

        loaded = db_session.get(DiagnosisFlow, str(flow.id))
        assert loaded is not None
        assert loaded.name == "SSL 诊断流程"
        assert len(loaded.steps) == 1
        assert loaded.steps[0]["id"] == "s1"

    def test_flow_default_version(self, db_session):
        from app.models.diagnosis_flow import DiagnosisFlow

        flow = DiagnosisFlow(
            name="Test Flow",
            steps=[{"id": "s1", "title": "Step 1"}],
        )
        db_session.add(flow)
        db_session.commit()

        assert flow.version == 1

    def test_flow_default_active(self, db_session):
        from app.models.diagnosis_flow import DiagnosisFlow

        flow = DiagnosisFlow(
            name="Active Flow",
            steps=[{"id": "s1", "title": "Step 1"}],
        )
        db_session.add(flow)
        db_session.commit()

        assert flow.is_active is True

    def test_flow_steps_json_complex(self, db_session):
        from app.models.diagnosis_flow import DiagnosisFlow

        steps = [
            {
                "id": "s1",
                "title": "收集信息",
                "conditions": [{"field": "error_code", "op": "eq", "value": "SSL001"}],
                "next_step": "s2",
            },
            {"id": "s2", "title": "检查证书", "conditions": [], "next_step": "s3"},
            {"id": "s3", "title": "修复问题", "next_step": None},
        ]
        flow = DiagnosisFlow(name="Complex Flow", steps=steps)
        db_session.add(flow)
        db_session.commit()

        loaded = db_session.get(DiagnosisFlow, str(flow.id))
        assert len(loaded.steps) == 3
        assert loaded.steps[0]["conditions"][0]["value"] == "SSL001"
        assert loaded.steps[2]["next_step"] is None
