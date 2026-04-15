"""
治理层评分模块

负责把展示页里的两个核心评价函数真正落成可运行代码：
1. 动态隐私信任评估函数 T_p(t)
2. 动态版权合规评估函数 C_r(t)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class PrivacyTrustConfig:
    alpha: float = 1.0
    beta: float = 0.18
    gamma: float = 0.42
    lam: float = 0.25
    t_base: float = 1.0


@dataclass
class CopyrightRiskConfig:
    mu: float = 0.28
    nu: float = 0.22
    xi: float = 0.18
    rho: float = 0.17
    sigma: float = 0.15


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def compute_privacy_trust(
    duration_ratio: float,
    gnn_risk_score: float,
    exposure_strength: float,
    config: PrivacyTrustConfig | None = None,
) -> Dict[str, Any]:
    """
    动态隐私信任评估函数

    T_p(t)=αT_base-βD_t-γR_gnn-λE_t
    """
    cfg = config or PrivacyTrustConfig()
    duration_ratio = clamp(duration_ratio)
    gnn_risk_score = clamp(gnn_risk_score)
    exposure_strength = clamp(exposure_strength)

    score = (
        cfg.alpha * cfg.t_base
        - cfg.beta * duration_ratio
        - cfg.gamma * gnn_risk_score
        - cfg.lam * exposure_strength
    )
    score = clamp(score)

    if score >= 0.75:
        band = "high"
        policy = "allow_with_standard_sanitization"
    elif score >= 0.45:
        band = "medium"
        policy = "tighten_sanitization"
    else:
        band = "low"
        policy = "restrict_or_block"

    return {
        "score": round(score, 4),
        "band": band,
        "policy": policy,
        "components": {
            "T_base": cfg.t_base,
            "D_t": round(duration_ratio, 4),
            "R_gnn": round(gnn_risk_score, 4),
            "E_t": round(exposure_strength, 4),
        },
    }


def _copyright_level_score(copyright_level: str) -> float:
    mapping = {
        "public_open": 0.08,
        "school_authorized": 0.36,
        "class_authorized": 0.48,
        "teacher_private": 0.72,
        "restricted_original": 0.88,
    }
    return mapping.get(copyright_level, 0.5)


def _access_mismatch_score(access_scope: str, requester_role: str) -> float:
    if access_scope == "public":
        return 0.05
    if access_scope == "school":
        return 0.18 if requester_role in {"student", "teacher"} else 0.42
    if access_scope == "class":
        return 0.34 if requester_role == "student" else 0.18
    if access_scope == "teacher_only":
        return 0.82 if requester_role != "teacher" else 0.12
    return 0.5


def compute_copyright_risk(
    resource: Dict[str, Any],
    requester_role: str = "student",
    propagation_depth: int = 2,
    exposure_mode: str = "summary",
    iteration_count: int = 1,
    config: CopyrightRiskConfig | None = None,
) -> Dict[str, Any]:
    """
    动态版权合规评估函数

    C_r(t)=μR_c+νR_a+ξR_p+ρR_e+σR_i
    """
    cfg = config or CopyrightRiskConfig()

    r_c = _copyright_level_score(str(resource.get("copyright_level", "school_authorized")))
    r_a = _access_mismatch_score(str(resource.get("access_scope", "school")), requester_role)
    r_p = clamp(propagation_depth / 5.0)

    exposure_map = {
        "fulltext": 0.95,
        "summary": 0.42,
        "substitute_generation": 0.28,
        "metadata_only": 0.12,
    }
    r_e = exposure_map.get(exposure_mode, 0.5)
    r_i = clamp(iteration_count / 5.0)

    score = cfg.mu * r_c + cfg.nu * r_a + cfg.xi * r_p + cfg.rho * r_e + cfg.sigma * r_i
    score = clamp(score)

    if score >= 0.75:
        band = "high"
        policy = "block_or_substitute"
    elif score >= 0.45:
        band = "medium"
        policy = "summary_or_substitute"
    else:
        band = "low"
        policy = "allow"

    return {
        "score": round(score, 4),
        "band": band,
        "policy": policy,
        "components": {
            "R_c": round(r_c, 4),
            "R_a": round(r_a, 4),
            "R_p": round(r_p, 4),
            "R_e": round(r_e, 4),
            "R_i": round(r_i, 4),
        },
    }
