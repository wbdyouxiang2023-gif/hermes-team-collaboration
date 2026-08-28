"""
Memory package - Episodic + Semantic + Retrieval + Intelligence + Activation

Public API:
    from evolution.memory import EpisodicMemory, SemanticMemory, MemoryRetriever
    from evolution.memory import MemoryIntelligence, MemoryType, MemoryDecision
    from evolution.memory import activate_memories
"""

from evolution.memory.episodic import EpisodicMemory, ExperienceRecord
from evolution.memory.intelligence import (
    MemoryIntelligence,
    MemoryDecision,
    MemoryType,
    MemoryStatus,
)
from evolution.memory.memory_activation import activate_memories

# Lazy imports (require numpy / sentence-transformers)
try:
    from evolution.memory.semantic import SemanticMemory
    from evolution.memory.retriever import MemoryRetriever, MemoryResult
except ImportError:
    SemanticMemory = None  # type: ignore[assignment,misc]
    MemoryRetriever = None  # type: ignore[assignment,misc]
    MemoryResult = None  # type: ignore[assignment,misc]

__all__ = [
    "EpisodicMemory",
    "ExperienceRecord",
    "SemanticMemory",
    "MemoryRetriever",
    "MemoryResult",
    "MemoryIntelligence",
    "MemoryDecision",
    "MemoryType",
    "MemoryStatus",
    "activate_memories",
]
