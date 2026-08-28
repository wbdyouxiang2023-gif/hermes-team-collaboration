"""
Evolution Logger - Independent experience recorder with redaction

Features:
- Write Experience to date-sharded JSONL files
- Recursive redaction of sensitive info (API keys, tokens, passwords)
- UUID whitelist: standard UUIDs are not redacted
- Error isolation: write failure does not affect production flow
"""

from __future__ import annotations

import json
import re
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from evolution.config import get_config

# === 敏感信息检测 ===

SENSITIVE_KEYS_PATTERN = re.compile(
    r"(api_key|apikey|api-key|token|password|secret|cookie|authorization|"
    r"bearer|credential|passwd|auth_token|access_token|refresh_token|"
    r"client_secret|private_key|session_token)",
    re.IGNORECASE,
)

FORBIDDEN_ENV_VARS = {
    "API_KEY", "SECRET_KEY", "PASSWORD", "TOKEN", "AUTHORIZATION",
    "BEARER", "CREDENTIAL", "ACCESS_KEY", "PRIVATE_KEY", "SECRET",
}

TOKEN_VALUE_RE = re.compile(r"^[A-Za-z0-9+/=]{32,}$")
BEARER_PATTERN = re.compile(r"^Bearer\s+", re.IGNORECASE)

SECRET_PREFIXES = ["sk-", "ghp_", "github_pat_", "xoxb-", "xoxp-"]

# === 脱敏函数 ===


def _is_standard_uuid(val: str) -> bool:
    """检查是否为标准 UUID v4（不脱敏）"""
    if not isinstance(val, str):
        return False
    return bool(re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", val.lower()))


def _looks_like_pem(val: str) -> bool:
    """是否像 PEM 私钥"""
    if not isinstance(val, str):
        return False
    return "PRIVATE KEY" in val


def _contains_secret_in_url(val: str) -> bool:
    """URL 中是否包含 secret 参数"""
    if not isinstance(val, str):
        return False
    return bool(re.search(
        r"[?&](token|api_key|authorization|access_token|refresh_token|client_secret|password|session_token)=",
        val,
        re.IGNORECASE,
    ))


def _redact_string(val: str) -> str:
    """高置信度 secret 脱敏"""
    if not isinstance(val, str):
        return val
    if _is_standard_uuid(val):
        return val
    if _looks_like_pem(val):
        return "***"
    if BEARER_PATTERN.match(val):
        return "***"
    if _contains_secret_in_url(val):
        return "***"
    if any(val.startswith(p) or p in val for p in SECRET_PREFIXES):
        return "***"
    if TOKEN_VALUE_RE.match(val):
        return "***"
    return val


def redact_data(data: Any) -> Any:
    """
    递归脱敏数据结构

    - 键名匹配敏感模式 → 整个值替换为 "***"
    - 字符串值匹配 secret 特征 → 替换为 "***"
    - UUID 白名单不脱敏
    """
    if isinstance(data, dict):
        out: Dict[str, Any] = {}
        for k, v in data.items():
            if SENSITIVE_KEYS_PATTERN.search(k) or k.upper() in FORBIDDEN_ENV_VARS:
                out[k] = "***"
            else:
                out[k] = redact_data(v)
        return out
    elif isinstance(data, list):
        return [redact_data(item) for item in data]
    elif isinstance(data, str):
        return _redact_string(data)
    return data


# === 日志写入 ===


def _get_date_filename() -> str:
    """按日期分片：YYYY-MM-DD.jsonl（UTC）"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d.jsonl")


def log_experience(exp_dict: Dict[str, Any], redact: bool = True) -> bool:
    """
    写入一条 experience 到 JSONL。

    Args:
        exp_dict: Experience 字典
        redact: 是否脱敏（默认 True）

    Returns:
        True 写入成功，False 写入失败（错误记录到 errors.log）
    """
    try:
        config = get_config()
        config.ensure_directories()

        if redact:
            exp_dict = redact_data(exp_dict)

        if "exp_id" not in exp_dict:
            exp_dict["exp_id"] = str(uuid.uuid4())
        if "timestamp" not in exp_dict:
            exp_dict["timestamp"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        filename = config.experiences_dir / _get_date_filename()
        with open(filename, "a", encoding="utf-8") as f:
            f.write(json.dumps(exp_dict, ensure_ascii=False, default=str) + "\n")
        return True

    except Exception as e:
        try:
            config = get_config()
            with open(config.errors_log, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now(timezone.utc).isoformat()}] Evolution logger error: {e}\n")
                f.write(traceback.format_exc() + "\n")
        except Exception:
            pass
        return False


def read_last_experience() -> Optional[Dict[str, Any]]:
    """读取最近写入的一条经验（测试/调试用）"""
    try:
        config = get_config()
        files = sorted(config.experiences_dir.glob("*.jsonl"), reverse=True)
        if not files:
            return None
        with open(files[0], "r", encoding="utf-8") as f:
            lines = f.readlines()
            if lines:
                return json.loads(lines[-1])
    except Exception:
        return None
    return None


__all__ = ["log_experience", "redact_data", "read_last_experience"]
