"""
Memory Intelligence - Rule-based deterministic evaluator

No LLM/network/database dependency. Uses keyword matching and heuristics
to classify, score importance, assess stability, and detect scope.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from evolution.config import get_config


# ==================== Enums ====================


class MemoryType(str, Enum):
    TEMPORARY = "temporary"          # 一次性、短期、无长期价值
    EPISODE = "episode"              # 具体事件过程
    FACT = "fact"                    # 稳定事实
    PREFERENCE = "preference"        # 用户偏好
    GOAL = "goal"                    # 目标
    DECISION = "decision"            # 工程/设计决策
    TECHNICAL_SOLUTION = "technical_solution"  # 技术方案
    PROJECT_STATE = "project_state"  # 项目当前状态


class MemoryStatus(str, Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    EXPIRED = "expired"
    DUPLICATE = "duplicate"
    ARCHIVED = "archived"


@dataclass
class MemoryDecision:
    """记忆评估决策"""
    should_store: bool
    memory_type: MemoryType
    importance: float      # 0.0 ~ 1.0
    stability: float       # 0.0 ~ 1.0
    scope: str             # "project" | "general"
    status: MemoryStatus = MemoryStatus.ACTIVE
    reason: str = ""       # 决策依据（调试用）


# ==================== Intelligence Core ====================

class MemoryIntelligence:
    """记忆智能评估器 — 纯规则引擎

    评估 Experience 是否值得记忆、如何分类、重要性和稳定性。
    """

    # 类型关键词映射
    TYPE_KEYWORDS: Dict[MemoryType, List[str]] = {
        MemoryType.TECHNICAL_SOLUTION: [
            "死锁", "解决方案", "修复", "bug", "问题.*解决",
            "通过.*解决", "修好", "绕过", "修改", "改动", "替换",
            "更新", "升级", "优化", "重构", "调整", "配置", "部署",
            "上线", "回退", "回滚", "重启", "补丁", "hotfix",
            "patch", "改.*代码", "写.*代码", "加.*日志", "加.*配置",
            "加.*参数", "超时", "timeout", "报错", "异常", "错误",
            "error", "exception", "排查", "调试", "debug", "定位.*问题",
            "发现.*bug", "实现", "实现.*功能", "编写", "开发", "接入",
            "集成", "适配", "脚本", "script", "命令", "命令行", "cli",
            "端口", "port", "接口", "api", "endpoint", "路由",
            "curl", "wget", "ssh", "scp", "管道", "重定向",
        ],
        MemoryType.DECISION: [
            "决定", "决策", "原则", "保持", "不改", "选择",
            "采用", "拒绝", "坚持", "确认", "敲定", "确定",
            "不改.*了", "就用", "用.*方案", "选.*方案",
            "最终.*决定", "最终.*选择", "一致同意", "拍板",
            "不再", "不要.*改", "保持.*不变", "维持.*现状",
            "方案 a", "方案 b", "方案.*一", "方案.*二",
            "a吧", "b吧", "放弃", "弃用", "切换.*到", "从.*换成",
        ],
        MemoryType.GOAL: [
            "目标", "方向", "发展", "计划", "愿景", "要.*成为",
            "未来", "长期.*规划", "长期.*发展", "下一步",
            "接下来.*要", "准备.*做", "打算", "想要.*实现",
            "任务", "待办", "todo", "里程碑", "milestone",
            "上线.*前", "发布.*前", "交付", "deadline", "优先级",
            "排期", "规划", "路线图",
        ],
        MemoryType.FACT: [
            "是.*系统", "是.*组件", "属于", "位于", "版本",
            "由.*构建", "基于", "定义为", "记忆系统", "长期记忆",
            "架构", "组件", "模块", "服务", "微服务", "进程",
            "线程", "配置.*是", "参数.*是", "路径.*是", "地址.*是",
            "端口.*是", "文件.*在", "目录.*在", "代码.*在", "日志.*在",
            "环境变量", "依赖", "requirement", "package", "数据库",
            "缓存", "队列", "消息", "中间件", "权重", "阈值",
            "超时.*秒", "超时.*毫秒",
        ],
        MemoryType.PREFERENCE: [
            "喜欢", "偏好", "更倾向于", "习惯", "通常", "风格",
            "审美", "不要.*用", "我喜欢", "我习惯", "简洁",
            "详细", "专业", "口语化",
        ],
        MemoryType.PROJECT_STATE: [
            "当前", "状态", "进度", "已完成", "未完成", "正在",
            "跑通", "通过", "验证", "测试", "test", "运行.*正常",
            "工作.*正常", "成功.*启动", "启动.*成功", "失败",
            "挂了", "崩了", "不工作", "不正常", "无响应",
            "上线.*了", "部署.*了", "改.*完了", "修.*好了",
            "日志.*显示", "日志.*看到", "看到.*日志",
        ],
    }

    # 临时性标记词（降低 stability）
    TEMPORARY_INDICATORS = ["今天", "刚才", "刚刚", "现在", "临时", "暂时", "本次", "这次"]

    # 项目关键词（scope=project）
    PROJECT_KEYWORDS = [
        "Hermes", "Evolution", "OpenViking", "WSL",
        "Agent", "Bridge", "Core", "plugin",
    ]

    def __init__(self, config: Optional[Any] = None):
        cfg = config or get_config()
        self._min_importance = cfg.min_importance_for_storage
        self._max_temp_importance = cfg.max_importance_for_temporary
        self._duplicate_threshold = cfg.duplicate_threshold

    def evaluate(self, exp: Dict[str, Any]) -> MemoryDecision:
        """评估 Experience 是否值得记忆，以及如何分类"""
        text = self._extract_text(exp)

        # 1. 临时聊天检测
        if self._is_temporary_chat(text):
            return MemoryDecision(
                should_store=False,
                memory_type=MemoryType.TEMPORARY,
                importance=0.0,
                stability=0.0,
                scope="general",
                status=MemoryStatus.ACTIVE,
                reason="temporary chat detected",
            )

        # 2. 类型分类
        mtype, type_reason = self._classify_type(text)

        # 3. 重要性
        importance = self._compute_importance(text, mtype)

        # 4. 稳定性
        stability = self._compute_stability(text)

        # 5. 作用域
        scope = self._detect_scope(text)

        return MemoryDecision(
            should_store=importance >= self._min_importance,
            memory_type=mtype,
            importance=round(importance, 3),
            stability=round(stability, 3),
            scope=scope,
            status=MemoryStatus.ACTIVE,
            reason=f"type={mtype.value}, reason={type_reason}",
        )

    def detect_duplicate(
        self, candidate: Dict[str, Any], existing: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """基于 Jaccard 相似度的重复检测"""
        cand_text = self._extract_text(candidate)
        cand_kw = set(re.findall(r"\w+", cand_text.lower()))

        best_match = None
        best_jaccard = 0.0

        for exp in existing:
            exp_kw = set(re.findall(r"\w+", self._extract_text(exp).lower()))
            if not cand_kw or not exp_kw:
                continue
            inter = len(cand_kw & exp_kw)
            union = len(cand_kw | exp_kw)
            jaccard = inter / union
            if jaccard > best_jaccard:
                best_jaccard = jaccard
                best_match = exp

        if best_match and best_jaccard >= self._duplicate_threshold:
            return {
                "duplicate": True,
                "matched_exp_id": best_match.get("exp_id"),
                "reason": f"jaccard={best_jaccard:.2f}",
            }
        return {"duplicate": False, "matched_exp_id": None, "reason": ""}

    def detect_conflict(
        self, candidate: Dict[str, Any], existing: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """冲突检测（V6.2 预留）"""
        cand_decision = self.evaluate(candidate)
        if cand_decision.memory_type not in (MemoryType.GOAL, MemoryType.DECISION):
            return {"conflict": False, "matched_exp_id": None, "reason": "not goal/decision"}
        # V6.2: 实现语义冲突检测
        return {"conflict": False, "matched_exp_id": None, "reason": "not implemented"}

    # ==================== Private ====================

    def _extract_text(self, exp: Dict[str, Any]) -> str:
        task = exp.get("task", {})
        return f"{task.get('user_input', '')} {task.get('goal_summary', '')}".lower().strip()

    def _is_temporary_chat(self, text: str) -> bool:
        if any(kw.lower() in text for kw in self.PROJECT_KEYWORDS):
            return False
        heuristics = [
            len(text) < 10,
            "？" in text or "?" in text,
            text.startswith(("怎么", "如何", "是否", "能不能")),
            any(word in text for word in ["天气", "吃了", "谢谢", "你好", "再见"]),
        ]
        return any(heuristics)

    def _classify_type(self, text: str) -> tuple[MemoryType, str]:
        for mtype, keywords in self.TYPE_KEYWORDS.items():
            for kw in keywords:
                if re.search(kw, text, re.IGNORECASE):
                    return mtype, f"matched keyword '{kw}'"
        return MemoryType.EPISODE, "no keyword match"

    def _compute_importance(self, text: str, mtype: MemoryType) -> float:
        type_weights = {
            MemoryType.TECHNICAL_SOLUTION: 0.9,
            MemoryType.DECISION: 0.85,
            MemoryType.GOAL: 0.75,
            MemoryType.FACT: 0.7,
            MemoryType.PROJECT_STATE: 0.65,
            MemoryType.PREFERENCE: 0.6,
            MemoryType.EPISODE: 0.55,
            MemoryType.TEMPORARY: 0.1,
        }
        base = type_weights.get(mtype, 0.5)

        # 文本长度惩罚
        if len(text) > 500:
            base *= 0.6
        elif len(text) > 200:
            base *= 0.8

        # 项目关键词加分（临时词不加分）
        has_temp = any(ind in text for ind in self.TEMPORARY_INDICATORS)
        if not has_temp and any(kw.lower() in text for kw in self.PROJECT_KEYWORDS):
            base *= 1.2

        return min(max(base, 0.0), 1.0)

    def _compute_stability(self, text: str) -> float:
        count_temp = sum(1 for ind in self.TEMPORARY_INDICATORS if ind in text)
        if count_temp > 0:
            return max(0.1, 1.0 - count_temp * 0.3)
        return 0.8

    def _detect_scope(self, text: str) -> str:
        if any(kw.lower() in text for kw in self.PROJECT_KEYWORDS):
            return "project"
        return "general"


__all__ = ["MemoryIntelligence", "MemoryDecision", "MemoryType", "MemoryStatus"]
