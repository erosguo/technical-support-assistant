"""Tests for F24: LLM Response Quality Evaluation."""

import asyncio

from app.services.quality_eval import QualityScore, evaluate_batch, evaluate_response


class MockQualityLLM:
    """Mock LLM that returns a canned string for chat()."""

    def __init__(self, response_text: str):
        self._response = response_text

    async def chat(self, messages: list[dict], **kwargs) -> str:
        return self._response


class TestQualityScore:
    def test_quality_score_overall_is_average(self):
        score = QualityScore(relevance=4, accuracy=5, completeness=3, clarity=4)
        assert score.overall == (4 + 5 + 3 + 4) / 4
        assert score.overall == 4.0


class TestEvaluateResponse:
    def test_evaluate_response_without_llm(self):
        score = asyncio.run(evaluate_response("query", "response", llm=None))
        assert score.relevance == 3
        assert score.accuracy == 3
        assert score.completeness == 3
        assert score.clarity == 3
        assert score.overall == 3.0

    def test_evaluate_response_with_mock_llm(self):
        llm = MockQualityLLM("relevance:4,accuracy:5,completeness:3,clarity:4")
        score = asyncio.run(evaluate_response("query", "response", llm=llm))
        assert score.relevance == 4
        assert score.accuracy == 5
        assert score.completeness == 3
        assert score.clarity == 4
        assert score.overall == 4.0

    def test_evaluate_response_handles_malformed_llm(self):
        llm = MockQualityLLM("garbage")
        score = asyncio.run(evaluate_response("query", "response", llm=llm))
        assert score.relevance == 3
        assert score.accuracy == 3
        assert score.completeness == 3
        assert score.clarity == 3
        assert score.overall == 3.0


class TestEvaluateBatch:
    def test_evaluate_batch(self):
        responses = [
            {"query": "q1", "response": "r1"},
            {"query": "q2", "response": "r2"},
        ]
        scores = asyncio.run(evaluate_batch(responses, llm=None))
        assert len(scores) == 2
        assert all(isinstance(s, QualityScore) for s in scores)
        assert all(s.overall == 3.0 for s in scores)
