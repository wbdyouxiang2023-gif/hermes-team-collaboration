"""
Memory Retriever — 统一检索层

整合 EpisodicMemory（精确过滤）和 SemanticMemory（向量检索），
支持 exact / semantic / hybrid 三种检索模式。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

import numpy as np

from evolution.config import get_config
from evolution.memory.episodic import EpisodicMemory, ExperienceRecord
from evolution.memory.semantic import SemanticMemory


@dataclass
class MemoryResult:
    """检索结果"""
    experience: ExperienceRecord
    score: float                    # 最终融合分数 (0.0 ~ 1.0)
    semantic_score: float           # BGE cosine similarity
    exact_score: float              # exact match signal (0.0 或 1.0)
    retrieval_method: str           # "exact" / "semantic" / "hybrid" / "fallback_exact"

    # V6.1 Activation 层会动态添加此属性
    activation_effective_score: float = 0.0


class MemoryRetriever:
    """统一记忆检索器

    整合情景记忆（精确过滤）和语义记忆（向量检索），
    支持三种模式：

    - exact: 仅使用 EpisodicMemory 精确过滤
    - semantic: 仅使用 SemanticMemory 向量检索
    - hybrid: 先过滤候选，再语义排序，再融合 exact signal（默认）
    """

    def __init__(
        self,
        episodic: EpisodicMemory,
        semantic: SemanticMemory,
        semantic_weight: float = 0.8,
        exact_weight: float = 0.2,
    ):
        self.episodic = episodic
        self.semantic = semantic
        self.semantic_weight = semantic_weight
        self.exact_weight = exact_weight

        if semantic_weight < 0 or exact_weight < 0:
            raise ValueError("Weights must be non-negative")
        if semantic_weight == 0 and exact_weight == 0:
            raise ValueError("At least one weight must be > 0")

    # ==================== Public API ====================

    def retrieve(
        self,
        query: str = "",
        *,
        mode: str = "hybrid",
        top_k: int = 5,
        exp_id: Optional[str] = None,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        tool: Optional[str] = None,
        success: Optional[bool] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> List[MemoryResult]:
        """统一检索接口

        Args:
            query: 自然语言查询（用于语义检索）
            mode: "exact" | "semantic" | "hybrid"
            top_k: 返回最大数量
            exp_id/session_id/task_id/tool/success/start_time/end_time: 过滤条件

        Returns:
            List[MemoryResult] 按 score DESC, timestamp DESC 排序
        """
        if mode not in ("exact", "semantic", "hybrid"):
            raise ValueError(f"Invalid mode: {mode}. Must be: exact, semantic, hybrid")
        if top_k <= 0:
            return []

        filters = {
            "exp_id": exp_id,
            "session_id": session_id,
            "task_id": task_id,
            "tool": tool,
            "success": success,
            "start_time": start_time,
            "end_time": end_time,
        }

        if mode == "exact":
            return self._retrieve_exact(filters, top_k)
        elif mode == "semantic":
            return self._retrieve_semantic(query, filters, top_k)
        else:
            return self._retrieve_hybrid(query, filters, top_k)

    def get_stats(self) -> Dict[str, Any]:
        """获取检索器统计"""
        return {
            "version": "6.1",
            "supported_modes": ["exact", "semantic", "hybrid"],
            "episodic": self.episodic.get_stats(),
            "semantic": self.semantic.get_stats(),
            "retriever": {
                "semantic_weight": self.semantic_weight,
                "exact_weight": self.exact_weight,
            },
        }

    # ==================== Exact ====================

    def _retrieve_exact(self, filters: Dict[str, Any], top_k: int) -> List[MemoryResult]:
        records = self.episodic.query(
            exp_id=filters.get("exp_id"),
            session_id=filters.get("session_id"),
            task_id=filters.get("task_id"),
            tool=filters.get("tool"),
            success=filters.get("success"),
            start_time=filters.get("start_time"),
            end_time=filters.get("end_time"),
            limit=top_k,
        )
        return [
            MemoryResult(
                experience=rec,
                score=1.0,
                semantic_score=0.0,
                exact_score=1.0,
                retrieval_method="exact",
            )
            for rec in records
        ]

    # ==================== Semantic ====================

    def _retrieve_semantic(
        self, query: str, filters: Dict[str, Any], top_k: int
    ) -> List[MemoryResult]:
        if not query.strip():
            return []

        if not self.semantic.vectors_path.exists() or not self.semantic.metadata_path.exists():
            raise FileNotFoundError(
                "Semantic index not found. Build it first with semantic.index()."
            )

        try:
            vectors = np.load(self.semantic.vectors_path)
            with open(self.semantic.metadata_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load semantic index: {e}")

        if vectors.ndim != 2:
            raise ValueError("Vectors array must be 2D")
        if len(meta.get("items", [])) != vectors.shape[0]:
            raise ValueError("Metadata items count does not match vectors shape")
        if vectors.shape[0] == 0:
            return []

        # 确定候选集合
        if self._has_any_filter(filters):
            candidate_exp_ids: Set[str] = {
                rec.exp_id
                for rec in self.episodic.query(
                    exp_id=filters.get("exp_id"),
                    session_id=filters.get("session_id"),
                    task_id=filters.get("task_id"),
                    tool=filters.get("tool"),
                    success=filters.get("success"),
                    start_time=filters.get("start_time"),
                    end_time=filters.get("end_time"),
                    limit=None,
                )
            }
        else:
            candidate_exp_ids = {item["exp_id"] for item in meta["items"]}

        if not candidate_exp_ids:
            return []

        # 映射 exp_id -> vector index
        exp_id_to_idx = {item["exp_id"]: idx for idx, item in enumerate(meta["items"])}
        candidate_indices = [exp_id_to_idx[eid] for eid in candidate_exp_ids if eid in exp_id_to_idx]
        if not candidate_indices:
            return []

        candidate_vectors = vectors[candidate_indices]
        candidate_exp_ids_list = [
            meta["items"][idx]["exp_id"] for idx in candidate_indices
        ]

        # Query embedding
        try:
            query_vec = np.array(self.semantic.embed_query(query), dtype=np.float32)
        except Exception as e:
            raise RuntimeError(f"Failed to embed query: {e}")

        # Cosine similarity
        norms = np.linalg.norm(candidate_vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1e-10, norms)
        sims = (candidate_vectors @ query_vec) / (norms.flatten() * np.linalg.norm(query_vec))

        semantic_scores = dict(zip(candidate_exp_ids_list, sims.astype(float)))

        # 构建 temp results with exact signal
        temp_results: Dict[str, Dict[str, float]] = {
            exp_id: {"semantic_score": score, "exact_score": 0.0}
            for exp_id, score in semantic_scores.items()
        }
        self._add_exact_signal(temp_results, query, filters)

        # Build final results
        final_results = []
        for exp_id in candidate_exp_ids_list:
            sem_score = semantic_scores.get(exp_id, 0.0)
            exact_score = temp_results[exp_id]["exact_score"]
            rec = self.episodic.get(exp_id)
            if rec is not None:
                final_results.append(
                    MemoryResult(
                        experience=rec,
                        score=float(sem_score),
                        semantic_score=float(sem_score),
                        exact_score=exact_score,
                        retrieval_method="semantic",
                    )
                )

        final_results.sort(key=lambda r: (r.semantic_score, r.experience.timestamp), reverse=True)
        return final_results[:top_k]

    # ==================== Hybrid ====================

    def _retrieve_hybrid(
        self, query: str, filters: Dict[str, Any], top_k: int
    ) -> List[MemoryResult]:
        # 1. 过滤候选
        candidate_records = self.episodic.query(
            exp_id=filters.get("exp_id"),
            session_id=filters.get("session_id"),
            task_id=filters.get("task_id"),
            tool=filters.get("tool"),
            success=filters.get("success"),
            start_time=filters.get("start_time"),
            end_time=filters.get("end_time"),
            limit=None,
        )
        candidate_exp_ids: Set[str] = {rec.exp_id for rec in candidate_records}
        if not candidate_exp_ids:
            return []

        # 2. 检查 semantic index
        if not self.semantic.vectors_path.exists() or not self.semantic.metadata_path.exists():
            return self._fallback_exact(candidate_records, top_k)

        try:
            vectors = np.load(self.semantic.vectors_path)
            with open(self.semantic.metadata_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
        except Exception:
            return self._fallback_exact(candidate_records, top_k)

        if vectors.ndim != 2 or len(meta.get("items", [])) != vectors.shape[0]:
            return self._fallback_exact(candidate_records, top_k)

        # 3. 映射候选到向量索引
        exp_id_to_idx = {item["exp_id"]: idx for idx, item in enumerate(meta["items"])}
        candidate_indices = [exp_id_to_idx[eid] for eid in candidate_exp_ids if eid in exp_id_to_idx]
        if not candidate_indices:
            return self._fallback_exact(candidate_records, top_k)

        candidate_vectors = vectors[candidate_indices]
        candidate_exp_ids_list = [
            meta["items"][idx]["exp_id"] for idx in candidate_indices
        ]

        # 4. Query embedding
        if not query.strip():
            return self._fallback_exact(candidate_records, top_k)
        try:
            query_vec = np.array(self.semantic.embed_query(query), dtype=np.float32)
        except Exception:
            return self._fallback_exact(candidate_records, top_k)

        # 5. 计算 semantic scores
        norms = np.linalg.norm(candidate_vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1e-10, norms)
        query_norm = np.linalg.norm(query_vec)
        if query_norm == 0:
            sims = np.zeros(len(candidate_exp_ids_list), dtype=np.float32)
        else:
            sims = (candidate_vectors @ query_vec) / (norms.flatten() * query_norm)

        # 6. 融合
        temp_results: Dict[str, Dict[str, float]] = {}
        for exp_id, sim in zip(candidate_exp_ids_list, sims):
            temp_results[exp_id] = {"semantic_score": float(sim), "exact_score": 0.0}

        self._add_exact_signal(temp_results, query, filters)

        final_results = []
        for exp_id, scores in temp_results.items():
            sem = scores["semantic_score"]
            exact = scores["exact_score"]
            final_score = self.semantic_weight * sem + self.exact_weight * exact
            rec = self.episodic.get(exp_id)
            if rec is not None:
                final_results.append(
                    MemoryResult(
                        experience=rec,
                        score=final_score,
                        semantic_score=sem,
                        exact_score=exact,
                        retrieval_method="hybrid",
                    )
                )

        final_results.sort(key=lambda r: (r.score, r.experience.timestamp), reverse=True)
        return final_results[:top_k]

    # ==================== Fallback ====================

    def _fallback_exact(
        self, records: List[ExperienceRecord], top_k: int
    ) -> List[MemoryResult]:
        return [
            MemoryResult(
                experience=rec,
                score=1.0,
                semantic_score=0.0,
                exact_score=1.0,
                retrieval_method="fallback_exact",
            )
            for rec in records[:top_k]
        ]

    # ==================== Helpers ====================

    @staticmethod
    def _has_any_filter(filters: Dict[str, Any]) -> bool:
        return any(v is not None for v in filters.values())

    def _add_exact_signal(
        self,
        results_dict: Dict[str, Dict[str, float]],
        query: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> None:
        """向候选添加 exact_score=1.0（query 文本命中或 exp_id 精确匹配）"""
        query_lower = query.lower().strip() if query and query.strip() else ""
        exp_id_filter = (filters or {}).get("exp_id")

        for exp_id in results_dict:
            rec = self.episodic.get(exp_id)
            if rec is None:
                continue
            if query_lower:
                goal = (rec.goal_summary or "").lower()
                user_input = (rec.task.get("user_input", "") if rec.task else "").lower()
                if query_lower in (goal + " " + user_input):
                    results_dict[exp_id]["exact_score"] = 1.0
                    continue
            if exp_id_filter and exp_id == exp_id_filter:
                results_dict[exp_id]["exact_score"] = 1.0


__all__ = ["MemoryRetriever", "MemoryResult"]
