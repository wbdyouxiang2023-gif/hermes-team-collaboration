"""
Semantic Memory — 隔离式语义检索

基于 BGE 向量模型，将 Experience 的 goal_summary + user_input 编码为向量，
支持余弦相似度检索。

索引持久化到 cache/vectors.npy + cache/metadata.json，
使用原子写入（tmpfile + os.replace）保证一致性。
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from evolution.config import get_config
from evolution.memory.episodic import EpisodicMemory, ExperienceRecord


class SemanticMemory:
    """语义记忆：向量编码 + 相似度检索"""

    def __init__(
        self,
        episodic_memory: EpisodicMemory,
        embedding_model: str = "BAAI/bge-small-zh-v1.5",
        cache_dir: Optional[Path] = None,
        local_model_path: Optional[Path] = None,
    ):
        self.episodic = episodic_memory
        self.model_name = embedding_model
        self._model = None
        self._embedding_dim: Optional[int] = None

        config = get_config()
        self.bge_local_path = local_model_path or config.embedding_local_path
        self.cache_dir = cache_dir or config.cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.vectors_path = self.cache_dir / "vectors.npy"
        self.metadata_path = self.cache_dir / "metadata.json"

    def ensure_model(self) -> None:
        """延迟加载 BGE 模型（首次调用时加载）"""
        if self._model is not None:
            return
        from sentence_transformers import SentenceTransformer

        model_path = str(self.bge_local_path)
        if not Path(model_path).exists():
            raise FileNotFoundError(f"Local BGE model not found: {model_path}")
        self._model = SentenceTransformer(model_path)
        self._embedding_dim = self._model.get_embedding_dimension()

    def embed_text(self, text: str) -> List[float]:
        """编码单条文本"""
        self.ensure_model()
        vec = self._model.encode(text, convert_to_numpy=True, show_progress_bar=False)
        return vec.astype(np.float32).tolist()

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """批量编码"""
        self.ensure_model()
        vecs = self._model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return vecs.astype(np.float32)

    def embed_query(self, text: str) -> np.ndarray:
        """编码查询（BGE 检索模型需要加 instruction）"""
        instruction = "为这个句子生成表示以用于检索相关文章："
        if not text.startswith(instruction):
            text = instruction + text
        return self.embed_batch([text])[0]

    def index(self, force_rebuild: bool = False) -> None:
        """构建或重建向量索引

        原子写入保证索引一致性。
        """
        if not force_rebuild and self.vectors_path.exists() and self.metadata_path.exists():
            try:
                stats = self.get_stats()
                if stats.get("indexed", False):
                    return
            except Exception:
                pass

        records = self.episodic.recent(100_000)

        texts: List[str] = []
        exp_ids: List[str] = []
        timestamps: List[str] = []
        for rec in records:
            goal = rec.goal_summary or ""
            user_input = rec.task.get("user_input", "") if rec.task else ""
            text = f"{goal}\n{user_input}".strip()
            texts.append(text or "(no content)")
            exp_ids.append(rec.exp_id)
            timestamps.append(rec.timestamp)

        if not texts:
            self.ensure_model()
            dim = self._embedding_dim or 512
            vectors = np.zeros((0, dim), dtype=np.float32)
        else:
            vectors = self.embed_batch(texts)

        # 原子写入 vectors
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=str(self.cache_dir), prefix=".tmp_vectors_", suffix=".npy", delete=False
        ) as tmp:
            tmp_path = tmp.name
            np.save(tmp, vectors)
        os.replace(tmp_path, str(self.vectors_path))

        # 原子写入 metadata
        metadata: Dict[str, Any] = {
            "version": "6.1",
            "model": self.model_name,
            "embedding_dim": int(vectors.shape[1]),
            "count": int(vectors.shape[0]),
            "model_fingerprint": self._compute_fingerprint(),
            "items": [
                {"exp_id": eid, "timestamp": ts}
                for eid, ts in zip(exp_ids, timestamps)
            ],
        }
        with tempfile.NamedTemporaryFile(
            mode="w", dir=str(self.cache_dir), prefix=".tmp_metadata_", suffix=".json", delete=False
        ) as tmp:
            tmp_path = tmp.name
            json.dump(metadata, tmp, ensure_ascii=False, indent=2)
        os.replace(tmp_path, str(self.metadata_path))

    def search(self, query: str, top_k: int = 5) -> List[ExperienceRecord]:
        """语义相似度搜索

        Args:
            query: 查询文本
            top_k: 返回最大数量

        Returns:
            按相似度降序排列的 ExperienceRecord 列表
        """
        if not isinstance(query, str) or not query.strip() or top_k <= 0:
            return []

        if not self.vectors_path.exists() or not self.metadata_path.exists():
            self.index()

        try:
            vectors = np.load(self.vectors_path)
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception:
            self.index(force_rebuild=True)
            vectors = np.load(self.vectors_path)
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)

        n = vectors.shape[0]
        if n == 0:
            return []

        if len(metadata.get("items", [])) != n:
            raise RuntimeError("Index corruption: vectors count does not match metadata")

        query_vec = np.array(self.embed_query(query), dtype=np.float32)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1e-10, norms)
        similarities = (vectors @ query_vec) / (norms.flatten() * np.linalg.norm(query_vec))

        k = min(top_k, n)
        top_indices = np.argsort(similarities)[::-1][:k]

        results: List[ExperienceRecord] = []
        seen: set = set()
        for idx in top_indices:
            exp_id = metadata["items"][int(idx)]["exp_id"]
            if exp_id in seen:
                continue
            seen.add(exp_id)
            rec = self.episodic.get(exp_id)
            if rec is not None:
                results.append(rec)
        return results

    def _compute_fingerprint(self) -> str:
        """计算模型指纹（用于缓存失效判断）"""
        dim = self._embedding_dim or 0
        s = f"{self.model_name}:{dim}"
        return hashlib.sha256(s.encode()).hexdigest()

    def get_stats(self) -> Dict[str, Any]:
        """获取索引统计信息"""
        if not self.vectors_path.exists() or not self.metadata_path.exists():
            return {"indexed": False, "model": self.model_name}
        try:
            vectors = np.load(self.vectors_path)
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            if vectors.shape[0] != metadata["count"]:
                raise RuntimeError("Count mismatch")
            return {
                "indexed": True,
                "total_experiences": int(metadata["count"]),
                "embedding_dim": int(metadata["embedding_dim"]),
                "model": metadata["model"],
                "model_fingerprint": metadata.get("model_fingerprint", ""),
                "index_size_bytes": int(
                    self.vectors_path.stat().st_size + self.metadata_path.stat().st_size
                ),
            }
        except Exception as e:
            return {"indexed": False, "model": self.model_name, "error": str(e)}


__all__ = ["SemanticMemory"]
