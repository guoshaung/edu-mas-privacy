from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel, Field

from gateway.governance import compute_copyright_risk, compute_privacy_trust
from gateway.public_bank_store import load_bank

router = APIRouter(prefix="/governance", tags=["governance"])


class GovernancePreviewRequest(BaseModel):
    duration_ratio: float = Field(default=0.25, ge=0.0, le=1.0)
    gnn_risk_score: float = Field(default=0.35, ge=0.0, le=1.0)
    exposure_strength: float = Field(default=0.12, ge=0.0, le=1.0)
    requester_role: str = Field(default="student")
    propagation_depth: int = Field(default=2, ge=1, le=8)
    exposure_mode: str = Field(default="summary")
    iteration_count: int = Field(default=1, ge=1, le=8)


def decide_joint_policy(privacy_trust: Dict[str, Any], copyright_risk: Dict[str, Any]) -> Dict[str, str]:
    trust_band = privacy_trust["band"]
    copyright_band = copyright_risk["band"]

    if trust_band == "high" and copyright_band == "low":
        return {
            "policy": "normal_release",
            "label": "正常放行",
            "explanation": "学生侧隐私信任较高，教师资源版权风险较低，可按标准脱敏后正常流转。",
        }
    if trust_band == "high" and copyright_band == "medium":
        return {
            "policy": "summary_or_substitute",
            "label": "摘要或替代生成",
            "explanation": "隐私侧可放行，但版权侧已进入中风险，优先返回摘要或变式内容。",
        }
    if trust_band == "medium" and copyright_band == "low":
        return {
            "policy": "tightened_sanitization",
            "label": "加强脱敏后放行",
            "explanation": "学生数据需提高脱敏强度，但版权侧风险较低，可继续完成教学流程。",
        }
    if trust_band == "low" and copyright_band == "low":
        return {
            "policy": "restrict_student_data",
            "label": "限制学生数据开放",
            "explanation": "优先保护学生侧数据，只保留完成教学任务所需的最小语义摘要。",
        }
    if trust_band == "low" and copyright_band in {"medium", "high"}:
        return {
            "policy": "block_or_minimal_release",
            "label": "阻断或最小必要返回",
            "explanation": "学生隐私与教师版权同时进入高压区，应阻断原文访问，仅保留极简安全结果。",
        }
    return {
        "policy": "controlled_release",
        "label": "受控放行",
        "explanation": "系统进入联合治理模式，根据当前阶段对学生侧和教师侧内容同时做粒度控制。",
    }


@router.get("/overview")
async def governance_overview() -> Dict[str, Any]:
    resources = load_bank()
    resource = resources[0] if resources else {
        "title": "默认教学资源",
        "copyright_level": "school_authorized",
        "access_scope": "school",
    }
    privacy_trust = compute_privacy_trust(
        duration_ratio=0.25,
        gnn_risk_score=0.35,
        exposure_strength=0.12,
    )
    copyright_risk = compute_copyright_risk(
        resource=resource,
        requester_role="student",
        propagation_depth=2,
        exposure_mode="summary",
        iteration_count=1,
    )
    return {
        "privacy_trust": privacy_trust,
        "copyright_risk": copyright_risk,
        "resource_preview": {
            "title": resource.get("title", "未命名资源"),
            "copyright_level": resource.get("copyright_level", "unknown"),
            "access_scope": resource.get("access_scope", "unknown"),
        },
        "joint_policy": decide_joint_policy(privacy_trust, copyright_risk),
    }


@router.post("/preview")
async def governance_preview(request: GovernancePreviewRequest) -> Dict[str, Any]:
    resources = load_bank()
    resource = resources[0] if resources else {
        "title": "默认教学资源",
        "copyright_level": "school_authorized",
        "access_scope": "school",
    }
    privacy_trust = compute_privacy_trust(
        duration_ratio=request.duration_ratio,
        gnn_risk_score=request.gnn_risk_score,
        exposure_strength=request.exposure_strength,
    )
    copyright_risk = compute_copyright_risk(
        resource=resource,
        requester_role=request.requester_role,
        propagation_depth=request.propagation_depth,
        exposure_mode=request.exposure_mode,
        iteration_count=request.iteration_count,
    )
    return {
        "privacy_trust": privacy_trust,
        "copyright_risk": copyright_risk,
        "resource_preview": {
            "title": resource.get("title", "未命名资源"),
            "copyright_level": resource.get("copyright_level", "unknown"),
            "access_scope": resource.get("access_scope", "unknown"),
        },
        "joint_policy": decide_joint_policy(privacy_trust, copyright_risk),
    }
