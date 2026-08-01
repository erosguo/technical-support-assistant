"""F24: LLM Response Quality Evaluation.

Scores an LLM-generated response against the original query on four
dimensions (1-5 scale): relevance, accuracy, completeness, clarity.
``overall`` is the arithmetic mean of the four scores.
"""

import re
from dataclasses import dataclass

_DIMENSIONS = ("relevance", "accuracy", "completeness", "clarity")


@dataclass
class QualityScore:
    relevance: int
    accuracy: int
    completeness: int
    clarity: int

    @property
    def overall(self) -> float:
        return (self.relevance + self.accuracy + self.completeness + self.clarity) / 4


def _default_score() -> QualityScore:
    return QualityScore(relevance=3, accuracy=3, completeness=3, clarity=3)


def _parse_scores(text: str) -> QualityScore:
    """Extract the four dimension scores from an LLM reply.

    Falls back to default scores (all 3) when the reply is malformed or any
    dimension is missing/out of the 1-5 range.
    """
    scores: dict[str, int] = {}
    for key in _DIMENSIONS:
        match = re.search(rf"{key}\s*:\s*(\d+)", text, re.IGNORECASE)
        if match:
            value = int(match.group(1))
            if 1 <= value <= 5:
                scores[key] = value
    if len(scores) != len(_DIMENSIONS):
        return _default_score()
    return QualityScore(**scores)


async def evaluate_response(query: str, response: str, llm=None) -> QualityScore:
    """Score ``response`` against ``query``.

    When ``llm`` is ``None`` (e.g. in tests) default neutral scores are
    returned without calling any external service.
    """
    if llm is None:
        return _default_score()
    prompt = [
        {
            "role": "system",
            "content": (
                "You are a response quality evaluator. Score the given response on "
                "4 dimensions using a 1-5 scale: relevance, accuracy, completeness, "
                "clarity. Reply ONLY in this exact format: "
                "relevance:N,accuracy:N,completeness:N,clarity:N"
            ),
        },
        {
            "role": "user",
            "content": f"Query: {query}\n\nResponse: {response}\n\nProvide the scores.",
        },
    ]
    result = await llm.chat(prompt)
    return _parse_scores(result)


async def evaluate_batch(responses: list[dict], llm=None) -> list[QualityScore]:
    """Score a batch of ``{"query": ..., "response": ...}`` items."""
    results: list[QualityScore] = []
    for item in responses:
        score = await evaluate_response(item["query"], item["response"], llm)
        results.append(score)
    return results
