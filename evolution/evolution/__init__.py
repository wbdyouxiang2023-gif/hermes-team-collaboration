"""
Evolution Memory System V6.1

Hermes experience memory engine providing:
- Episodic Memory: JSONL read-only query
- Semantic Memory: BGE vector retrieval (requires numpy, sentence-transformers)
- Memory Retriever: Unified retrieval (hybrid/exact/semantic)
- Memory Intelligence: Rule-based evaluator (zero external deps)
- Memory Activation: Soft penalty and re-ranking
- Context Builder: Retrieval results to LLM context text
- Bridge Worker: Hermes subprocess communication
- Logger: Experience recorder with redaction
"""

__version__ = "6.1.0"

# === Eager imports (no heavy deps) ===
from evolution.schema import Action, Experience, Task
from evolution.logger import log_experience, redact_data
from evolution.config import EvolutionConfig, get_config
from evolution.memory.episodic import EpisodicMemory, ExperienceRecord
from evolution.memory.intelligence import (
    MemoryDecision,
    MemoryIntelligence,
    MemoryStatus,
    MemoryType,
)
from evolution.memory.memory_activation import activate_memories
from evolution.context.context_builder import BuilderConfig, MemoryContextBuilder

# === Lazy imports (require numpy / sentence-transformers) ===
try:
    from evolution.memory.semantic import SemanticMemory
    from evolution.memory.retriever import MemoryRetriever, MemoryResult
    _SEMANTIC_AVAILABLE = True
except ImportError:
    SemanticMemory = None  # type: ignore[assignment,misc]
    MemoryRetriever = None  # type: ignore[assignment,misc]
    MemoryResult = None  # type: ignore[assignment,misc]
    _SEMANTIC_AVAILABLE = False

__all__ = [
    "Action", "Task", "Experience",
    "EpisodicMemory", "ExperienceRecord",
    "SemanticMemory", "MemoryRetriever", "MemoryResult",
    "MemoryIntelligence", "MemoryDecision", "MemoryType", "MemoryStatus",
    "activate_memories",
    "MemoryContextBuilder", "BuilderConfig",
    "log_experience", "redact_data",
    "EvolutionConfig", "get_config",
]


def is_semantic_available() -> bool:
    """Check if semantic memory (numpy + sentence-transformers) is available."""
    return _SEMANTIC_AVAILABLE
