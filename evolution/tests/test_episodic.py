from evolution.memory.episodic import EpisodicMemory, ExperienceRecord


class TestEpisodicMemory:
    def test_query_all(self, tmp_experiences_dir, sample_experiences):
        em = EpisodicMemory(tmp_experiences_dir)
        results = em.query()
        assert len(results) == 5

    def test_query_by_session(self, tmp_experiences_dir, sample_experiences):
        em = EpisodicMemory(tmp_experiences_dir)
        results = em.query(session_id="sess-1")
        assert len(results) == 2

    def test_query_by_success(self, tmp_experiences_dir, sample_experiences):
        em = EpisodicMemory(tmp_experiences_dir)
        results = em.query(success=True)
        assert len(results) == 3  # test-001, test-003, test-005

    def test_query_by_task_id(self, tmp_experiences_dir, sample_experiences):
        em = EpisodicMemory(tmp_experiences_dir)
        results = em.query(task_id="死锁")
        assert len(results) == 1
        assert results[0].exp_id == "test-001"

    def test_recent_limit(self, tmp_experiences_dir, sample_experiences):
        em = EpisodicMemory(tmp_experiences_dir)
        results = em.recent(3)
        assert len(results) == 3

    def test_get_by_id(self, tmp_experiences_dir, sample_experiences):
        em = EpisodicMemory(tmp_experiences_dir)
        rec = em.get("test-003")
        assert rec is not None
        assert rec.session_id == "sess-2"

    def test_get_missing(self, tmp_experiences_dir, sample_experiences):
        em = EpisodicMemory(tmp_experiences_dir)
        rec = em.get("nonexistent")
        assert rec is None

    def test_experience_record_properties(self, tmp_experiences_dir, sample_experiences):
        em = EpisodicMemory(tmp_experiences_dir)
        rec = em.get("test-001")
        assert rec.is_successful
        assert not rec.is_failed
        assert rec.tool == "bash"
        assert "死锁" in rec.goal_summary

    def test_stats(self, tmp_experiences_dir, sample_experiences):
        em = EpisodicMemory(tmp_experiences_dir)
        stats = em.get_stats()
        assert stats["valid_count"] == 5
        assert stats["invalid_count"] == 0
        assert stats["jsonl_files"] == 1

    def test_invalid_jsonl_line(self, tmp_experiences_dir):
        filepath = tmp_experiences_dir / "2026-01-18.jsonl"
        with open(filepath, "w") as f:
            f.write('{"bad json\n')
            f.write('{"exp_id": "ok", "session_id": "s", "turn_id": 1, "timestamp": "2026-01-18T00:00:00Z", "task": {"user_input": "x"}, "actions": []}\n')
        em = EpisodicMemory(tmp_experiences_dir)
        stats = em.get_stats()
        assert stats["valid_count"] == 1
        assert stats["invalid_count"] == 1