from evolution.memory.intelligence import MemoryIntelligence, MemoryType, MemoryStatus


class TestMemoryIntelligence:
    def setup_method(self):
        self.intel = MemoryIntelligence()

    def test_technical_solution(self):
        d = self.intel.evaluate({"task": {"user_input": "帮我修复 Herm     es 的死锁问题"}})
        assert d.memory_type == MemoryType.TECHNICAL_SOLUTION
        assert d.should_store is True
        assert d.importance > 0.8

    def test_temporary_chat(self):
        d = self.intel.evaluate({"task": {"user_input": "你好"}})
        assert d.memory_type == MemoryType.TEMPORARY
        assert d.should_store is False

    def test_decision(self):
        d = self.intel.evaluate({"task": {"user_input": "我们一致同意保持现有架构不变"}})
        assert d.memory_type == MemoryType.DECISION
        assert d.should_store is True

    def test_goal(self):
        d = self.intel.evaluate({"task": {"user_input": "接下来的计划和里程碑安排"}})
        assert d.memory_type == MemoryType.GOAL

    def test_fact(self):
        d = self.intel.evaluate({"task": {"user_input": "Hermes 的架构是基于插件系统的"}})
        assert d.memory_type == MemoryType.FACT

    def test_project_scope(self):
        d = self.intel.evaluate({"task": {"user_input": "修复 Evolution 的 bug"}})
        assert d.scope == "project"

    def test_general_scope(self):
        d = self.intel.evaluate({"task": {"user_input": "我喜欢简洁的代码风格"}})
        assert d.scope == "general"

    def test_stability_temporary_words(self):
        d = self.intel.evaluate({"task": {"user_input": "今天修复了一个 bug"}})
        assert d.stability < 0.8

    def test_duplicate_detection(self):
        # Chinese text without spaces: \w+ matches continuous CJK as one token
        # Use space-separated words for predictable tokenization
        existing = [{"task": {"user_input": "hermes deadlock fix process complete"}, "exp_id": "e1"}]
        candidate = {"task": {"user_input": "hermes deadlock fix process done"}, "exp_id": "e2"}
        result = self.intel.detect_duplicate(candidate, existing)
        assert result["duplicate"] is True

    def test_importance_range(self):
        d = self.intel.evaluate({"task": {"user_input": "部署上线"}})
        assert 0.0 <= d.importance <= 1.0
        assert 0.0 <= d.stability <= 1.0
