# Evolution Memory System V6.1

Hermes 的经验记忆引擎，为 AI Agent 提供长期记忆能力。

## Architecture

```
User Query
    │
    ▼
Bridge Worker (stdin/stdout JSON)
    │
    ├──► MemoryRetriever (hybrid/exact/semantic)
    │       ├── EpisodicMemory (JSONL read-only)
    │       └── SemanticMemory (BGE vector index)
    │               │
    │               ▼
    │       MemoryResult[]
    │               │
    │               ▼
    │       Memory Activation (soft penalty)
    │               │
    │               ▼
    │       ContextBuilder → LLM context text
    │
    └──► sync_turn: Experience write + Intelligence eval
            ├── Logger (JSONL + redaction)
            └── MemoryIntelligence (rule engine)
```

## Components

| Component | Version | Description |
|-----------|---------|-------------|
| **Schema** | 6.1 | Action / Task / Experience 数据模型 |
| **Logger** | 0.1.1 | JSONL 写入 + 递归脱敏 |
| **EpisodicMemory** | 0.2-A | JSONL 只读查询 + 多条件过滤 |
| **SemanticMemory** | 0.3-A | BGE 向量编码 + cosine 检索 |
| **MemoryRetriever** | 0.4-A | 统一检索层 (hybrid/exact/semantic) |
| **MemoryIntelligence** | 0.6 | 规则引擎：分类、重要性、稳定性评估 |
| **MemoryActivation** | 0.1 | V6.1 软降权 + effective_score 排序 |
| **ContextBuilder** | 0.2 | 检索结果 → LLM 上下文文本 |
| **BridgeWorker** | 6.1 | Hermes 子进程通信桥接 |
| **Config** | 6.1 | 集中配置管理（环境变量覆盖） |

## Key Design Decisions

1. **Score Pollution Prevention**: `activate_memories()` 不修改 `MemoryResult.score`，新增 `activation_effective_score`
2. **Atomic Index Writes**: 使用 `tempfile + os.replace` 保证索引文件一致性
3. **Graceful Degradation**: Hybrid 模式在语义索引不可用时自动降级到 Exact
4. **Zero LLM Dependency**: MemoryIntelligence 纯规则引擎，不调用外部 API
5. **Production Safe**: Intelligence 评估失败不阻塞 Experience 写入

## Bugs Fixed from V6.0

- **semantic.py**: `etadata[...]` → `metadata["items"][idx]["exp_id"]` (missing 'm' prefix)
- **retriever.py**: Same `etadata` bug in `_retrieve_semantic()` and `_retrieve_hybrid()`
- **evaluate_intelligence.py**: `stats[statstype]` → `stats[s]`, `by_type[type]` → `by_type[mtype]`
- **context/__init__.py**: Removed duplicate `MemoryContextBuilder` class definition
- **schema.py**: `datetime.utcnow()` → `datetime.now(timezone.utc)` (deprecated API)

## Install

```bash
cd evolution-v6
pip install -e ".[dev]"
```

## Test

```bash
pytest tests/ -v
```

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HERMES_HOME` | `~/.hermes` | Hermes 根目录 |
| `EVOLUTION_EMBEDDING_MODEL` | `BAAI/bge-small-zh-v1.5` | Embedding 模型 |
| `EVOLUTION_SEMANTIC_WEIGHT` | `0.8` | 语义检索权重 |
| `EVOLUTION_EXACT_WEIGHT` | `0.2` | 精确匹配权重 |
| `EVOLUTION_DEFAULT_TOP_K` | `5` | 默认检索数量 |
| `EVOLUTION_BRIDGE_LOG_LEVEL` | `INFO` | Bridge 日志级别 |

## License

MIT
