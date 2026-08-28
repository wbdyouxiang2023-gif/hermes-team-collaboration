from unittest.mock import MagicMock

from evolution.memory.memory_activation import activate_memories
from evolution.memory.retriever import MemoryResult
from evolution.memory.episodic import ExperienceRecord


def _make_result(exp_id, score, memory=None):
    exp = MagicMock(spec=ExperienceRecord)
    exp.exp_id = exp_id
    exp.memory = memory
    return MemoryResult(
        experience=exp,
        score=score,
        semantic_score=score,
        exact_score=0.0,
        retrieval_method="hybrid",
    )


class TestMemoryActivation:
    def test_should_store_false_soft_penalty(self):
        candidates = [
            _make_result("a", 0.9, {"should_store": False, "type": "temporary", "importance": 0.1}),
            _make_result("b", 0.5, {"should_store": True, "type": "fact", "importance": 0.7}),
        ]
        result = activate_memories("query", candidates, soft_penalty_factor=0.5)
        assert len(result) == 2
        # b should be first (effective 0.5 > 0.45)
        assert result[0].experience.exp_id == "b"
        assert result[0].activation_effective_score == 0.5
        assert result[1].activation_effective_score == 0.45

    def test_score_not_modified(self):
        mr = _make_result("a", 0.8, {"should_store": False})
        original_score = mr.score
        activate_memories("q", [mr])
        assert mr.score == original_score

    def test_no_memory_compat(self):
        mr = _make_result("a", 0.7, None)
        result = activate_memories("q", [mr])
        assert len(result) == 1
        assert result[0].activation_effective_score == 0.7

    def test_empty_candidates(self):
        assert activate_memories("q", []) == []

    def test_max_candidates(self):
        candidates = [_make_result(f"r{i}", 0.8 - i * 0.1) for i in range(5)]
        result = activate_memories("q", candidates, max_candidates=2)
        assert len(result) == 2
