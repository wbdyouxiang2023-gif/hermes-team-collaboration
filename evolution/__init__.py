"""\nEvolution Memory System V6.1

Hermes 的经验记忆引擎，提供：
- Episodic Memory: 情景记忆（JSONL 只读查询）
- Semantic Memory: 语义记忆（BGE 向量检索）
- Memory Retriever: 统一检索层（hybrid/exact/semantic）
- Memory Intelligence: 记忆智能评估（规则引擎）
- Memory Activation: 记忆激活与软降权
- Context Builder: 检索结果 → LLM 上下文文本
- Bridge Worker: Hermes 子进程通信桥接
- Logger: 经验记录器（带脱敏）
"""

__version__ = "6.1.0"
__all__ = [
    # Schema
    "Action",
    "Task",
    "Experience",
    # Memory
    "EpisodicMemory",
    "SemanticMemory",
    "MemoryRetriever",
    "MemoryResult",
    # Intelligence
    "MemoryIntelligence",
    "MemoryDecision",
    "MemoryType",
    "MemoryStatus",
    # Activation
    "activate_memories",
    # Context
    "MemoryContextBuilder",
    "BuilderConfig",
    # Logger
    "log_experience",
    "redact_data",
    # Config
    "EvolutionConfig",
    "get_config",
    # Bridge
    "BridgeWorker",
]

from evolution.schema import Action, Experience, Task
from evolution.logger import log_experience, redact_data
from evolution.memory.episodic import EpisodicMemory, ExperienceRecord
from evolution.memory.semantic import SemanticMemory
from evolution.memory.retriever import MemoryRetriever, MemoryResult
from evolution.memory.intelligence import (
    MemoryDecision,
    MemoryIntelligence,
    MemoryStatus,
    MemoryType,
)
from evolution.memory.memory_activation import activate_memories
from evolution.context.context_builder import BuilderConfig, MemoryContextBuilder
from evolution.config import EvolutionConfig, get_config

# Bridge worker 不在默认导入中（有 heavy 依赖），按需导入
# from evolution.bridge_worker import main as bridge_main
