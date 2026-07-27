from app.core.config import Settings


class TestSettings:
    def test_default_app_name(self):
        s = Settings()
        assert s.app_name == "Tech Support Assistant"

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("APP_NAME", "Custom Name")
        s = Settings()
        assert s.app_name == "Custom Name"

    def test_default_llm_model(self):
        s = Settings()
        assert s.llm_model == "gpt-4o-mini"

    def test_default_embedding_dimensions(self):
        s = Settings()
        assert s.embedding_dimensions == 1536
