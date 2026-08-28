"""
Experience Schema — 纯数据结构，无外部依赖

定义经验记录的核心数据模型：
- Action: 单次工具调用
- Task: 任务信息
- Experience: 一次完整的经验记录（一个 turn）
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid


@dataclass
class Action:
    """单次工具调用记录"""
    seq: int
    tool: str
    function: str
    arguments: Dict[str, Any]
    result: Dict[str, Any]
    tool_success: bool
    duration_sec: float


@dataclass
class Task:
    """任务信息（来自用户消息）"""
    user_input: str
    intent: Optional[str] = None
    goal: Optional[str] = None
    goal_summary: str = ""


@dataclass
class Experience:
    """一次完整的经验记录（一个 turn）"""
    # 必须参数
    exp_id: str
    session_id: str
    turn_id: int
    timestamp: str
    task: Task
    actions: List[Action]

    # 可选参数
    evolution_version: str = "6.1"
    hermes_version: Optional[str] = None
    task_success: Optional[bool] = None
    user_confirmed: Optional[bool] = None
    reward: Optional[float] = None
    context: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "exp_id": self.exp_id,
            "session_id": self.session_id,
            "turn_id": self.turn_id,
            "timestamp": self.timestamp,
            "evolution_version": self.evolution_version,
            "hermes_version": self.hermes_version,
            "task": asdict(self.task),
            "actions": [asdict(a) for a in self.actions],
            "task_success": self.task_success,
            "user_confirmed": self.user_confirmed,
            "reward": self.reward,
            "context": self.context or {},
        }

    @classmethod
    def create(
        cls,
        session_id: str,
        turn_id: int,
        user_input: str,
        goal_summary: str = "",
        **kwargs: Any,
    ) -> Experience:
        """工厂方法：快速创建 Experience"""
        valid_keys = {"task_success", "user_confirmed", "reward", "context", "hermes_version"}
        filtered = {k: v for k, v in kwargs.items() if k in valid_keys}
        return cls(
            exp_id=str(uuid.uuid4()),
            session_id=session_id,
            turn_id=turn_id,
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            task=Task(
                user_input=user_input,
                intent=kwargs.get("intent"),
                goal=kwargs.get("goal"),
                goal_summary=goal_summary,
            ),
            actions=[],
            **filtered,
        )

    def add_action(
        self,
        seq: int,
        tool: str,
        function: str,
        arguments: Dict[str, Any],
        result: Dict[str, Any],
        tool_success: bool,
        duration_sec: float,
    ) -> None:
        """追加一条 Action"""
        self.actions.append(
            Action(
                seq=seq,
                tool=tool,
                function=function,
                arguments=arguments,
                result=result,
                tool_success=tool_success,
                duration_sec=duration_sec,
            )
        )


__all__ = ["Action", "Task", "Experience"]
