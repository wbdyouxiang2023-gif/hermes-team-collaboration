"""
Evolution Configuration — 集中管理所有配置项

支持环境变量覆盖，消除断码中的硬编码路径。
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class EvolutionConfig:
    """Evolution 全局配置"""

    # === 路径 ===
    hermes_home: Path = field(default_factory=lambda: Path(os.getenv("HERMES_HOME", str(Path.home() / ".hermes"))))
    evolution_root: Optional[Path] = None
    experiences_dir: Optional[Path] = None
    cache_dir: Optional[Path] = None
    errors_log: Optional[Path] = None

    # === Embedding ===
    embedding_model: str = "BAAI/bge-small-zh-v1.5"
    embedding_local_path: Optional[Path] = None

    # === Retrieval ===
    semantic_weight: float = 0.8
    exact_weight: float = 0.2
    default_top_k: int = 5
    default_mode: str = "hybrid"

    # === Context Builder ===
    max_results: int = 5
    max_chars_per_field: int = 500
    max_total_chars: int = 2000
    min_score: float = 0.3

    # === Memory Intelligence ===
    min_importance_for_storage: float = 0.3
    max_importance_for_temporary: float = 0.4
    duplicate_threshold: float = 0.6

    # === Activation ===
    soft_penalty_factor: float = 0.5

    # === Bridge Worker ===
    bridge_log_level: str = "INFO"

    def __post_init__(self):
        """派生路径自动计算"""
        if self.evolution_root is None:
            self.evolution_root = self.hermes_home / "evolution"
        if self.experiences_dir is None:
            self.experiences_dir = self.evolution_root / "experiences"
        if self.cache_dir is None:
            self.cache_dir = self.evolution_root / "cache"
        if self.errors_log is None:
            self.errors_log = self.evolution_root / "errors.log"
        if self.embedding_local_path is None:
            self.embedding_local_path = (
                Path.home()
                / ".cache" / "hermes" / "embeddings" / "bge-small-zh-v1.5"
                / "models--BAAI--bge-small-zh-v1.5" / "snapshots"
                / "7999e1d3359715c523056ef9478215996d62a620"
            )

    def ensure_directories(self) -> None:
        """确保必要目录存在"""
        self.experiences_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_env(cls) -> "EvolutionConfig":
        """从环境变量创建配置"""
        kwargs = {}
        env_map = {
            "EVOLUTION_HERMES_HOME": ("hermes_home", Path),
            "EVOLUTION_EMBEDDING_MODEL": ("embedding_model", str),
            "EVOLUTION_SEMANTIC_WEIGHT": ("semantic_weight", float),
            "EVOLUTION_EXACT_WEIGHT": ("exact_weight", float),
            "EVOLUTION_DEFAULT_TOP_K": ("default_top_k", int),
            "EVOLUTION_BRIDGE_LOG_LEVEL": ("bridge_log_level", str),
        }
        for env_key, (attr, type_fn) in env_map.items():
            val = os.getenv(env_key)
            if val is not None:
                kwargs[attr] = type_fn(val)
        return cls(**kwargs)


# === 全局默认配置单例 ===
_default_config: Optional[EvolutionConfig] = None


def get_config() -> EvolutionConfig:
    """获取全局配置（延迟初始化）"""
    global _default_config
    if _default_config is None:
        _default_config = EvolutionConfig.from_env()
    return _default_config


def reset_config(config: Optional[EvolutionConfig] = None) -> None:
    """重置全局配置（主要用于测试）"""
    global _default_config
    _default_config = config


__all__ = ["EvolutionConfig", "get_config", "reset_config"]
