"""
MemoryContextBuilder - Convert retrieval results to LLM context text

Enforces size limits, field whitelist, deduplication, and truncation.
V6.1 integrates Memory Activation, uses effective_score for sorting.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional

from evolution.memory.memory_activation import activate_memories
from evolution.config import get_config


@dataclass
class BuilderConfig:
    """Context Builder 配置"""
    max_results: int = 5
    max_chars_per_field: int = 500
    max_total_chars: int = 2000
    min_score: float = 0.3


class MemoryContextBuilder:
    """安全地将检索结果转换为 LLM 上下文

    流程：
    1. Memory Activation 软降权
    2. 按 exp_id 去重（保留最高 effective_score）
    3. 按 min_score 过滤（使用原始 score）
    4. 按 effective_score + timestamp 排序
    5. 截断到 max_results + max_total_chars
    6. 格式化为文本
    """

    def __init__(self, config: Optional[BuilderConfig] = None):
        self.config = config or BuilderConfig()

    def build(self, results: List[Any], query: Optional[str] = None) -> str:
        """构建上下文文本

        Args:
            results: MemoryResult 列表
            query: 用户查询（用于 Activation，None 则跳过）

        Returns:
            格式化的上下文文本，无结果返回空串
        """
        if not results:
            return ""

        # V6.1 Memory Activation
        selected = results
        if query is not None:
            try:
                selected = activate_memories(query, results)
            except Exception:
                selected = results

        # 去重：按 exp_id 保留最高 effective_score
        unique: dict[str, Any] = {}
        for r in selected:
            effective = getattr(r, "activation_effective_score", r.score)
            existing = unique.get(r.experience.exp_id)
            if existing is None or effective > getattr(existing, "activation_effective_score", existing.score):
                unique[r.experience.exp_id] = r

        # 过滤（使用原始 score）+ 排序（使用 effective_score）
        filtered = [r for r in unique.values() if r.score >= self.config.min_score]
        filtered.sort(
            key=lambda r: (
                getattr(r, "activation_effective_score", r.score),
                r.experience.timestamp,
            ),
            reverse=True,
        )
        top = filtered[: self.config.max_results]

        if not top:
            return ""

        # 构建文本
        parts: list[str] = []
        total = 0
        for idx, r in enumerate(top, 1):
            exp = r.experience
            goal = _trunc(
                exp.goal_summary or exp.task.get("user_input", "")[:100],
                self.config.max_chars_per_field,
            )
            summary = _trunc(
                exp.task.get("goal_summary", "") or exp.intent or "",
                self.config.max_chars_per_field,
            )
            ts = _format_timestamp(exp.timestamp)

            block = (
                f"[历史经验 {idx}]\n"
                f"任务：{goal}\n"
                f"结果：{summary}\n"
                f"时间：{ts}\n"
                f"置信度：{r.score:.2f}\n"
            )
            if total + len(block) > self.config.max_total_chars:
                break
            parts.append(block)
            total += len(block)

        return "\n\n".join(parts).strip()


# ==================== Helpers ====================


def _trunc(text: str, max_len: int) -> str:
    """安全截断"""
    if not text:
        return ""
    return text[: max_len - 3] + "..." if len(text) > max_len else text


def _format_timestamp(ts: Any) -> str:
    """格式化时间戳"""
    if isinstance(ts, str) and "T" in ts:
        return ts.replace("T", " ").rstrip("Z")
    return str(ts)


__all__ = ["MemoryContextBuilder", "BuilderConfig"]
