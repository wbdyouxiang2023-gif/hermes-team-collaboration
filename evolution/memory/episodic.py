"""
Episodic Memory - Read-only query layer

Data source: ~/.hermes/evolution/experiences/*.jsonl
Provides structured query interface without modifying data.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from evolution.config import get_config


@dataclass
class ExperienceRecord:
    """Experience 记录封装（只读）"""
    exp_id: str
    session_id: str
    turn_id: int
    timestamp: str
    task: Dict[str, Any]
    actions: List[Dict[str, Any]]
    task_success: Optional[bool]
    user_confirmed: Optional[bool]
    reward: Optional[float]
    memory: Optional[Dict[str, Any]] = None  # V6.1: Memory Intelligence metadata

    @property
    def goal_summary(self) -> str:
        return self.task.get("goal_summary", "")

    @property
    def intent(self) -> Optional[str]:
        return self.task.get("intent")

    @property
    def tool(self) -> Optional[str]:
        if self.actions:
            return self.actions[0].get("tool")
        return None

    @property
    def is_successful(self) -> bool:
        return self.task_success is True

    @property
    def is_failed(self) -> bool:
        return self.task_success is False

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "exp_id": self.exp_id,
            "session_id": self.session_id,
            "turn_id": self.turn_id,
            "timestamp": self.timestamp,
            "task": self.task,
            "actions": self.actions,
            "task_success": self.task_success,
            "user_confirmed": self.user_confirmed,
            "reward": self.reward,
        }
        if self.memory is not None:
            d["memory"] = self.memory
        return d


def _parse_iso_timestamp(ts: str) -> Optional[datetime]:
    """安全解析 ISO 时间戳"""
    if not ts:
        return None
    try:
        cleaned = ts.rstrip("Z").replace("+00:00", "")
        # 处理带毫秒的格式
        if "." in cleaned:
            return datetime.fromisoformat(cleaned.split(".")[0])
        return datetime.fromisoformat(cleaned)
    except (ValueError, TypeError):
        return None


class EpisodicMemory:
    """情景记忆只读查询接口

    从 JSONL 文件中读取 Experience 记录，支持按 session、tool、
    success、时间范围等条件过滤。
    """

    def __init__(self, experiences_dir: Optional[Union[str, Path]] = None):
        if experiences_dir is not None:
            self._dir = Path(experiences_dir)
        else:
            self._dir = get_config().experiences_dir

        # 兼容测试数据布局：如果传入目录下有 "experiences" 子目录
        if (self._dir / "experiences").is_dir():
            self._dir = self._dir / "experiences"

    def get(self, exp_id: str) -> Optional[ExperienceRecord]:
        """按 exp_id 精确查询"""
        for record in self._iter_all():
            if record.exp_id == exp_id:
                return record
        return None

    def query(
        self,
        *,
        exp_id: Optional[str] = None,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        tool: Optional[str] = None,
        success: Optional[bool] = None,
        start_time: Optional[Union[str, datetime]] = None,
        end_time: Optional[Union[str, datetime]] = None,
        limit: Optional[int] = None,
    ) -> List[ExperienceRecord]:
        """多条件查询

        Args:
            exp_id: 精确匹配
            session_id: 按会话过滤
            task_id: 模糊匹配 goal_summary 或 user_input
            tool: 按首个工具名过滤
            success: 按成功状态过滤
            start_time: 起始时间（ISO 字符串或 datetime）
            end_time: 结束时间
            limit: 最大返回数量（None 表示不限制）
        """
        _start_dt = _parse_iso_timestamp(start_time) if isinstance(start_time, str) else start_time
        _end_dt = _parse_iso_timestamp(end_time) if isinstance(end_time, str) else end_time

        results: List[ExperienceRecord] = []
        for _, record in self._read_all_safe():
            if record is None:
                continue
            if exp_id and record.exp_id != exp_id:
                continue
            if session_id and record.session_id != session_id:
                continue
            if task_id:
                gs = record.task.get("goal_summary", "")
                ui = record.task.get("user_input", "")
                if task_id not in gs and task_id not in ui:
                    continue
            if tool and record.tool != tool:
                continue
            if success is not None and record.task_success != success:
                continue
            if _start_dt:
                ts = _parse_iso_timestamp(record.timestamp)
                if ts is not None and ts < _start_dt:
                    continue
            if _end_dt:
                ts = _parse_iso_timestamp(record.timestamp)
                if ts is not None and ts > _end_dt:
                    continue
            results.append(record)

        results.sort(key=lambda r: r.timestamp, reverse=True)
        return results[:limit] if limit is not None else results

    def recent(self, n: int = 10) -> List[ExperienceRecord]:
        """最近 N 条记录"""
        return self.query(limit=n)

    def successful(self, n: int = 10) -> List[ExperienceRecord]:
        """最近 N 条成功记录"""
        return self.query(success=True, limit=n)

    def failed(self, n: int = 10) -> List[ExperienceRecord]:
        """最近 N 条失败记录"""
        return self.query(success=False, limit=n)

    def _read_all_safe(self):
        """安全读取所有 JSONL 文件（容错）"""
        for filepath in sorted(self._dir.glob("*.jsonl")):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            yield line, self._parse_record(data)
                        except json.JSONDecodeError:
                            yield line, None
            except FileNotFoundError:
                continue

    def _iter_all(self):
        """遍历所有有效记录"""
        for _, record in self._read_all_safe():
            if record is not None:
                yield record

    @staticmethod
    def _parse_record(data: Dict[str, Any]) -> ExperienceRecord:
        """解析 JSONL 行为 ExperienceRecord"""
        task = data.get("task", {})
        actions = data.get("actions", [])
        return ExperienceRecord(
            exp_id=data["exp_id"],
            session_id=data["session_id"],
            turn_id=data["turn_id"],
            timestamp=data["timestamp"],
            task=task,
            actions=actions,
            task_success=data.get("task_success"),
            user_confirmed=data.get("user_confirmed"),
            reward=data.get("reward"),
            memory=task.get("memory"),  # V6.1
        )

    def get_stats(self) -> Dict[str, int]:
        """获取存储统计"""
        total = 0
        invalid = 0
        files = list(self._dir.glob("*.jsonl"))
        for _, record in self._read_all_safe():
            if record is None:
                invalid += 1
            else:
                total += 1
        return {
            "valid_count": total,
            "invalid_count": invalid,
            "total_records": total,
            "invalid_lines": invalid,
            "jsonl_files": len(files),
        }


__all__ = ["EpisodicMemory", "ExperienceRecord"]
