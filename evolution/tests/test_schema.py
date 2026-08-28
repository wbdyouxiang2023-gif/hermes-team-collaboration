from evolution.schema import Experience, Task, Action


class TestSchema:
    def test_create(self):
        exp = Experience.create(
            session_id="sess-1",
            turn_id=1,
            user_input="test input",
            goal_summary="test goal",
        )
        assert exp.exp_id
        assert exp.session_id == "sess-1"
        assert exp.turn_id == 1
        assert exp.task.user_input == "test input"
        assert exp.evolution_version == "6.1"
        assert len(exp.actions) == 0

    def test_add_action(self):
        exp = Experience.create("s", 1, "input", "goal")
        exp.add_action(1, "bash", "exec", {"cmd": "ls"}, {"output": "file1"}, True, 0.1)
        assert len(exp.actions) == 1
        assert exp.actions[0].tool == "bash"
        assert exp.actions[0].tool_success is True

    def test_to_dict(self):
        exp = Experience.create("s", 1, "input", "goal")
        d = exp.to_dict()
        assert d["session_id"] == "s"
        assert "task" in d
        assert d["evolution_version"] == "6.1"
