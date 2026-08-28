import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone


@pytest.fixture
def tmp_experiences_dir(tmp_path):
    """创建临时 experiences 目录，写入测试数据"""
    exp_dir = tmp_path / "experiences"
    exp_dir.mkdir()
    return exp_dir


@pytest.fixture
def sample_experiences(tmp_experiences_dir):
    """写入 5 条测试 Experience"""
    records = [
        {
            "exp_id": "test-001",
            "session_id": "sess-1",
            "turn_id": 1,
            "timestamp": "2026-01-15T10:00:00Z",
            "task": {
                "user_input": "帮我修复 Hermes 的死锁问题",
                "goal_summary": "修复死锁",
            },
            "actions": [{"tool": "bash", "function": "exec", "arguments": {"cmd": "ps aux"}, "result": {}, "tool_success": True, "seq": 1, "duration_sec": 0.5}],
            "task_success": True,
            "user_confirmed": None,
            "reward": None,
        },
        {
            "exp_id": "test-002",
            "session_id": "sess-1",
            "turn_id": 2,
            "timestamp": "2026-01-15T11:00:00Z",
            "task": {
                "user_input": "今天天气怎么样",
                "goal_summary": "问天气",
            },
            "actions": [],
            "task_success": None,
            "user_confirmed": None,
            "reward": None,
        },
        {
            "exp_id": "test-003",
            "session_id": "sess-2",
            "turn_id": 1,
            "timestamp": "2026-01-16T09:00:00Z",
            "task": {
                "user_input": "升级 OpenViking 到 0.4.16 版本",
                "goal_summary": "升级 OpenViking",
            },
            "actions": [{"tool": "bash", "function": "exec", "arguments": {"cmd": "pipx install"}, "result": {}, "tool_success": True, "seq": 1, "duration_sec": 30.0}],
            "task_success": True,
            "user_confirmed": None,
            "reward": None,
        },
        {
            "exp_id": "test-004",
            "session_id": "sess-2",
            "turn_id": 2,
            "timestamp": "2026-01-16T10:00:00Z",
            "task": {
                "user_input": "决定用方案 A 而不是方案 B 来实现缓存",
                "goal_summary": "选择方案A",
            },
            "actions": [],
            "task_success": None,
            "user_confirmed": None,
            "reward": None,
        },
        {
            "exp_id": "test-005",
            "session_id": "sess-3",
            "turn_id": 1,
            "timestamp": "2026-01-17T14:00:00Z",
            "task": {
                "user_input": "Hermes 当前状态：所有测试通过",
                "goal_summary": "项目状态正常",
            },
            "actions": [],
            "task_success": True,
            "user_confirmed": None,
            "reward": None,
        },
    ]
    filepath = tmp_experiences_dir / "2026-01-17.jsonl"
    with open(filepath, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return records
