"""
Memory Activation V6.1 - Lightweight selection and soft penalty

Preserves original retrieval score. Uses V6 metadata for soft penalty/sorting.
Adds activation_effective_score attribute without modifying MemoryResult.score.
"""

from __future__ import annotations

from typing import Any, List, Optional


def activate_memories(
    query: str,
    candidates: List[Any],
    *,
    soft_penalty_factor: float = 0.5,
    max_candidates: Optional[int] = None,
    enable_debug: bool = False,
) -> List[Any]:
    """V6.1 Memory Activation — 轻量级选择层

    保持原始 retrieval score 不变，仅基于 V6 metadata 进行软降权/排序。

    Args:
        query: 用户查询
        candidates: Retriever 返回的 MemoryResult 列表
        soft_penalty_factor: should_store=False 时的降权因子 (0~1, 默认 0.5)
        max_candidates: 最大返回数量（None 不限制）
        enable_debug: 附加调试信息到 activation_reason 属性

    Returns:
        激活后的候选列表，按 activation_effective_score 降序
    """
    if not candidates:
        return []

    activated = []
    for mr in candidates:
        exp = getattr(mr, "experience", None)
        base_score = getattr(mr, "score", 0.0)

        if exp is None:
            mr.activation_effective_score = base_score
            activated.append(mr)
            continue

        memory = getattr(exp, "memory", None) or {}
        should_store = memory.get("should_store", True)

        # 软降权：should_store=False 时降低有效分数
        if not should_store:
            effective_score = base_score * soft_penalty_factor
        else:
            effective_score = base_score

        mr.activation_effective_score = effective_score

        if enable_debug:
            mr.activation_reason = (
                f"should_store={should_store}, type={memory.get('type')}, "
                f"importance={memory.get('importance')}, scope={memory.get('scope')}"
            )
        activated.append(mr)

    activated.sort(
        key=lambda mr: getattr(mr, "activation_effective_score", mr.score),
        reverse=True,
    )

    if max_candidates is not None:
        activated = activated[:max_candidates]

    return activated


__all__ = ["activate_memories"]
