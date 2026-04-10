from __future__ import annotations

from typing import Any, List

from fastapi import APIRouter
from pydantic import BaseModel, Field


router = APIRouter(prefix="/privacy", tags=["privacy-lab"])
compat_router = APIRouter(tags=["privacy-lab-compat"])


class PromptInjectionDemoRequest(BaseModel):
    attack_name: str = "prompt_injection"
    raw_prompt: str = Field(..., min_length=1)
    student_name: str = "张三"
    student_id: str = "20260001"
    raw_profile: dict[str, Any] = Field(default_factory=dict)


class LogEntry(BaseModel):
    step: str
    status: str
    detail: str


class CompareItem(BaseModel):
    field: str
    before: str
    after: str
    protection: str


class PromptInjectionDemoResponse(BaseModel):
    attack_name: str
    blocked: bool
    risk_score_before: float
    risk_score_after: float
    attacker_view_before: str
    attacker_view_after: str
    compare_panel: List[CompareItem]
    abac_timeline: List[LogEntry]
    user_notice: str


def _default_profile(request: PromptInjectionDemoRequest) -> dict[str, Any]:
    return {
        "student_name": request.student_name,
        "student_id": request.student_id,
        "personality": "INTJ",
        "stress_level": "Medium",
        "weakness_tags": ["dimension_mismatch", "calculation_carelessness"],
    }


@router.post("/prompt-injection-demo", response_model=PromptInjectionDemoResponse)
@compat_router.post(
    "/api/privacy/prompt-injection-demo",
    response_model=PromptInjectionDemoResponse,
    include_in_schema=False,
)
async def prompt_injection_demo(
    request: PromptInjectionDemoRequest,
) -> PromptInjectionDemoResponse:
    raw_profile = request.raw_profile or _default_profile(request)

    compare_panel = [
        CompareItem(
            field="姓名",
            before=str(raw_profile.get("student_name", request.student_name)),
            after="匿名学生-A01",
            protection="身份匿名化处理",
        ),
        CompareItem(
            field="学号",
            before=str(raw_profile.get("student_id", request.student_id)),
            after="已隐藏",
            protection="直接标识符屏蔽",
        ),
        CompareItem(
            field="心理压力",
            before=str(raw_profile.get("stress_level", "Medium")),
            after="区间化风险: 中等",
            protection="敏感属性模糊化",
        ),
        CompareItem(
            field="薄弱标签",
            before=", ".join(raw_profile.get("weakness_tags", ["dimension_mismatch"])),
            after="仅保留学习相关薄弱项",
            protection="最小必要数据流转",
        ),
    ]

    abac_timeline = [
        LogEntry(
            step="攻击请求进入隐私网关",
            status="received",
            detail="系统检测到提示注入式请求，准备进入联合鉴权。",
        ),
        LogEntry(
            step="提示注入模式识别",
            status="flagged",
            detail="发现越权关键词，例如“忽略规则”“返回原始画像”“暴露身份”。",
        ),
        LogEntry(
            step="ABAC 联合判定",
            status="blocked",
            detail="当前请求无权访问原始身份字段，仅允许读取脱敏后的最小必要特征。",
        ),
        LogEntry(
            step="语义重构与脱敏保护",
            status="applied",
            detail="直接标识被替换，心理与个体属性被区间化和模糊化处理。",
        ),
        LogEntry(
            step="云端智能体可见内容",
            status="safe",
            detail="云端仅接收到匿名后的学习相关特征，无法还原真实学生身份。",
        ),
    ]

    return PromptInjectionDemoResponse(
        attack_name=request.attack_name,
        blocked=True,
        risk_score_before=0.86,
        risk_score_after=0.24,
        attacker_view_before=(
            "攻击者试图让系统忽略安全规则，并返回学生原始画像、学号和心理标签。"
        ),
        attacker_view_after=(
            "系统仅返回匿名学生编号、脱敏后的学习偏好和区间化风险等级，无法定位到真实学生。"
        ),
        compare_panel=compare_panel,
        abac_timeline=abac_timeline,
        user_notice=(
            "你的姓名、学号和敏感心理标签没有被直接暴露。当前展示的是经过隐私网关保护后的安全结果。"
        ),
    )
