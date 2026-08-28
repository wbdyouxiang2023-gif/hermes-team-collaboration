#!/usr/bin/env python3
"""
Evaluate MemoryIntelligence on real Experience data.

Usage:
    python -m evolution.evaluate_intelligence
"""

from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from pathlib import Path

from evolution.config import get_config, reset_config
from evolution.memory.intelligence import MemoryIntelligence, MemoryType


def load_experiences() -> list:
    """从 JSONL 加载所有 Experience"""
    config = get_config()
    records = []
    for f in sorted(config.experiences_dir.glob("*.jsonl")):
        with open(f) as fp:
            for line in fp:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


def evaluate_all(records: list) -> tuple:
    """评估所有记录"""
    intel = MemoryIntelligence()
    stats = defaultdict(list)
    decisions = {}
    for rec in records:
        text = rec.get("task", {}).get("user_input", "")
        if not text:
            continue
        try:
            decision = intel.evaluate(rec)
        except Exception as e:
            print(f"Error evaluating exp_id={rec.get('exp_id')}: {e}")
            continue
        decisions[rec["exp_id"]] = decision
        stats[decision.memory_type.value].append(decision.importance)
    return stats, decisions


def print_distribution(stats: dict) -> None:
    """打印类型分布"""
    print("\n=== Memory Type Distribution ===")
    total = sum(len(v) for v in stats.values())
    for mtype in sorted(stats.keys()):
        count = len(stats[mtype])
        avg_imp = sum(stats[mtype]) / count if count else 0
        pct = 100 * count / total if total else 0
        print(f"{mtype:20s}: {count:4d} ({pct:4.1f}%) avg_imp={avg_imp:.3f}")


def print_samples(records: list, decisions: dict, n: int = 5) -> None:
    """打印各类型样本"""
    print("\n=== Sample Experiences by Type ===")
    by_type = defaultdict(list)
    for rec in records:
        exp_id = rec["exp_id"]
        if exp_id not in decisions:
            continue
        mtype = decisions[exp_id].memory_type.value
        by_type[mtype].append(rec)
    for mtype in sorted(by_type.keys()):
        sample = random.sample(by_type[mtype], min(n, len(by_type[mtype])))
        print(f"\n--- {mtype} ---")
        for rec in sample:
            text = rec["task"]["user_input"][:100].replace("\n", " ")
            dec = decisions[rec["exp_id"]]
            print(f"[{dec.importance:.2f}, {dec.stability:.2f}, {dec.scope}] {text}...")


def print_skipped(records: list, decisions: dict) -> None:
    """打印被跳过的记录"""
    print("\n=== Should Be Skipped (should_store=False) ===")
    skipped = [rec for rec in records if rec["exp_id"] in decisions and not decisions[rec["exp_id"]].should_store]
    print(f"Total skipped: {len(skipped)}")
    for rec in skipped[:20]:
        text = rec["task"]["user_input"][:80].replace("\n", " ")
        print(f"- {text}...")
    if len(skipped) > 20:
        print(f"... and {len(skipped) - 20} more")


def detect_duplicates(records: list, decisions: dict, threshold: float = 0.6) -> None:
    """Jaccard 重复检测"""
    print("\n=== Duplicate Detection (Jaccard) ===")
    import re

    def keywords(text):
        return set(re.findall(r"\w+", text.lower()))

    by_type: dict[str, list] = defaultdict(list)
    for rec in records:
        exp_id = rec["exp_id"]
        if exp_id not in decisions:
            continue
        by_type[decisions[exp_id].memory_type.value].append(rec)

    duplicates = []
    for mtype, recs in by_type.items():
        for i, r1 in enumerate(recs):
            k1 = keywords(r1["task"]["user_input"])
            if not k1:
                continue
            for j in range(i + 1, len(recs)):
                k2 = keywords(recs[j]["task"]["user_input"])
                if not k2:
                    continue
                inter = len(k1 & k2)
                union = len(k1 | k2)
                if union == 0:
                    continue
                jaccard = inter / union
                if jaccard >= threshold:
                    duplicates.append((r1["exp_id"], recs[j]["exp_id"], jaccard))

    print(f"Found {len(duplicates)} duplicate pairs (Jaccard >= {threshold})")
    for e1, e2, score in duplicates[:10]:
        print(f"- {e1[:8]}... <-> {e2[:8]}... (score={score:.2f})")
    if len(duplicates) > 10:
        print(f"... and {len(duplicates) - 10} more")


def main():
    print("Loading real Experience data...")
    records = load_experiences()
    print(f"Loaded {len(records)} records")
    if not records:
        print("No data found. Exiting.")
        return
    stats, decisions = evaluate_all(records)
    print_distribution(stats)
    print_samples(records, decisions, n=5)
    print_skipped(records, decisions)
    detect_duplicates(records, decisions)
    print("\n=== Done ===")


if __name__ == "__main__":
    main()
