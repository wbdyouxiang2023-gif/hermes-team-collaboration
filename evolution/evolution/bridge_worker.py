"""
Evolution Bridge Worker V6.1

Runs as a child process, communicates with Hermes via stdin/stdout JSON protocol.
Responsible for: memory retrieval (prefetch), experience writing (sync_turn),
memory intelligence evaluation.

Protocol: one JSON request per stdin line, one JSON response per stdout line.
Logs to stderr only (does not interfere with stdout JSON protocol).
"""

from __future__ import annotations

import json
import logging
import sys
import time
import traceback
import uuid
from pathlib import Path
from typing import Any, Dict

from evolution.config import get_config, reset_config

# 配置日志（stderr only）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("bridge_worker")

# 延迟加载 heavy modules
_retriever = None
_context_builder = None
_intelligence = None


def _ensure_components():
    """懒加载 Evolution 组件"""
    global _retriever, _context_builder, _intelligence
    if _retriever is not None:
        return
    try:
        from evolution.memory.episodic import EpisodicMemory
        from evolution.memory.semantic import SemanticMemory
        from evolution.memory.retriever import MemoryRetriever
        from evolution.context.context_builder import MemoryContextBuilder
        from evolution.memory.intelligence import MemoryIntelligence

        config = get_config()
        config.ensure_directories()

        episodic = EpisodicMemory()
        semantic = SemanticMemory(episodic)
        semantic.ensure_model()
        _retriever = MemoryRetriever(episodic, semantic)
        _context_builder = MemoryContextBuilder()
        _intelligence = MemoryIntelligence()
        logger.info("Evolution components loaded")
    except Exception:
        logger.exception("Failed to load Evolution components")
        raise


# ==================== Request Handlers ====================


def handle_init(params: Dict[str, Any]) -> Dict[str, Any]:
    """初始化确认"""
    session_id = params.get("session_id", "")
    logger.info("Initialized for session: %s", session_id)
    return {"status": "ok", "version": "6.1"}


def handle_prefetch(params: Dict[str, Any]) -> Dict[str, Any]:
    """检索：返回格式化上下文文本"""
    query = params.get("query", "").strip()
    session_id = params.get("session_id", "")
    if not query:
        return {"text": ""}
    try:
        _ensure_components()
        config = get_config()
        results = _retriever.retrieve(
            query=query,
            mode=config.default_mode,
            top_k=config.default_top_k,
        )
        context = _context_builder.build(results, query=query)
        return {"text": context or ""}
    except Exception:
        logger.exception("Prefetch failed")
        return {"text": "", "error": "prefetch_failed"}


def handle_sync_turn(params: Dict[str, Any]) -> Dict[str, Any]:
    """写入 Experience + Memory Intelligence 评估"""
    try:
        _ensure_components()
        from evolution.logger import log_experience, redact_data

        messages = params["messages"]
        user_content = params.get("user_content", "")
        session_id = params.get("session_id", "")

        user_msg = user_content[:1000]

        # 提取 tool_calls 和 tool_results
        tool_calls_by_id: Dict[str, Dict] = {}
        for msg in messages:
            if msg.get("role") == "assistant" and "tool_calls" in msg:
                for tc in msg["tool_calls"]:
                    call_id = tc.get("id")
                    if call_id:
                        tool_calls_by_id[call_id] = tc

        tool_results_by_id: Dict[str, Any] = {}
        for msg in messages:
            if msg.get("role") == "tool":
                call_id = msg.get("tool_call_id")
                if call_id:
                    tool_results_by_id[call_id] = msg.get("content", "")

        # 构造 actions
        actions = []
        seq = 0
        for msg in messages:
            if msg.get("role") == "assistant" and "tool_calls" in msg:
                for tc in msg["tool_calls"]:
                    seq += 1
                    call_id = tc.get("id", "")
                    function = tc.get("function", {})
                    actions.append({
                        "seq": seq,
                        "tool": tc.get("name", ""),
                        "function": function.get("name", ""),
                        "arguments": function.get("arguments", {}),
                        "result": tool_results_by_id.get(call_id, {}),
                        "tool_success": True,
                        "duration_sec": 0.0,
                    })

        # 构造 Experience
        exp = {
            "exp_id": str(uuid.uuid4()),
            "session_id": session_id,
            "turn_id": 0,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.", time.gmtime())
            + str(int(time.time() * 1000) % 1000)
            + "Z",
            "task": {
                "user_input": user_msg[:1000],
                "goal_summary": user_msg[:500],
            },
            "actions": actions,
            "task_success": None,
            "user_confirmed": None,
            "reward": None,
            "context": {},
        }

        # 脱敏
        exp = redact_data(exp)

        # V6 Memory Intelligence（仅 metadata，不影响生产流程）
        try:
            if _intelligence is not None:
                decision = _intelligence.evaluate(exp)
                exp.setdefault("task", {})["memory"] = {
                    "type": decision.memory_type.value,
                    "importance": decision.importance,
                    "stability": decision.stability,
                    "scope": decision.scope,
                    "should_store": decision.should_store,
                    "status": decision.status.value,
                    "reason": decision.reason,
                }
        except Exception:
            logger.exception("MemoryIntelligence evaluation failed, continuing without metadata")

        # 写入
        if log_experience(exp, redact=False):  # 已脱敏，不再重复
            logger.info("Experience written: %s", exp["exp_id"])
            return {"status": "ok", "exp_id": exp["exp_id"]}
        else:
            return {"status": "error", "error": "write_failed"}
    except Exception:
        logger.exception("Sync turn failed")
        return {"status": "error", "error": "sync_failed"}


def handle_shutdown(params: Dict[str, Any]) -> Dict[str, Any]:
    return {"status": "shutting down"}


def handle_ping(params: Dict[str, Any]) -> Dict[str, Any]:
    return {"ok": True}


def handle_get_stats(params: Dict[str, Any]) -> Dict[str, Any]:
    """V6.1: 获取记忆系统统计"""
    try:
        _ensure_components()
        return _retriever.get_stats()
    except Exception:
        logger.exception("Get stats failed")
        return {"error": "stats_failed"}


# ==================== Method Dispatch ====================

_METHOD_MAP = {
    "init": handle_init,
    "prefetch": handle_prefetch,
    "sync_turn": handle_sync_turn,
    "shutdown": handle_shutdown,
    "ping": handle_ping,
    "get_stats": handle_get_stats,
}


# ==================== Main Loop ====================


def main():
    logger.info("Bridge worker v6.1 started")
    try:
        for line in sys.stdin:
            if not line.strip():
                continue
            try:
                req = json.loads(line)
                req_id = req.get("id")
                method = req.get("method")
                params = req.get("params", {})
            except json.JSONDecodeError:
                logger.error("Invalid JSON: %s", line[:100])
                continue

            handler = _METHOD_MAP.get(method)
            if handler is None:
                result = {"error": f"Unknown method: {method}"}
            else:
                try:
                    result = handler(params)
                except Exception:
                    logger.exception("Method %s failed", method)
                    result = {"error": "internal_error"}

            resp = {"id": req_id, "result": result}
            try:
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
            except BrokenPipeError:
                break

            if method == "shutdown":
                break
    except KeyboardInterrupt:
        pass
    except Exception:
        logger.exception("Worker fatal error")
    finally:
        logger.info("Bridge worker exiting")


if __name__ == "main":
    main()
