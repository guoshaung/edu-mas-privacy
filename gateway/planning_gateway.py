from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True, encoding="utf-8-sig")


class SanitizedFeatures(BaseModel):
    cognitive_style: str = Field(..., description="SRPG/LDP processed cognitive style")
    weakness_tags: List[str] = Field(default_factory=list)
    stress_level: str


class PlanningPayload(BaseModel):
    current_topic: str
    sanitized_features: SanitizedFeatures


class RequestMetadata(BaseModel):
    timestamp: int
    client_version: str


class LearningPlanningRequest(BaseModel):
    session_id: str
    request_type: str
    payload: PlanningPayload
    metadata: RequestMetadata


class PlanningStep(BaseModel):
    stage: str
    objective: str
    recommended_action: str
    estimated_minutes: int


class LearningPlanningResponse(BaseModel):
    session_id: str
    request_type: str
    risk_score: float
    authorization: str
    diagnosis_result: str
    planning_path: List[PlanningStep]
    prompt_preview: str
    current_agent: str
    llm_mode: str
    llm_error: Optional[str] = None


class AgentState(TypedDict, total=False):
    student_profile_features: Dict[str, Any]
    current_topic: str
    diagnosis_result: str
    planning_path: List[Dict[str, Any]]
    current_agent: str
    prompt_preview: str
    llm_mode: str
    llm_error: Optional[str]


class PlanningAgentOutput(BaseModel):
    diagnosis_result: str
    planning_path: List[PlanningStep]


def mock_get_gnn_risk_score(request: LearningPlanningRequest) -> float:
    weakness_count = len(request.payload.sanitized_features.weakness_tags)
    stress_level = request.payload.sanitized_features.stress_level.lower()

    risk_score = 0.18 + weakness_count * 0.11
    if stress_level == "medium":
        risk_score += 0.12
    elif stress_level == "high":
        risk_score += 0.28

    return round(min(risk_score, 0.95), 2)


def mock_abac_authorize(
    request_type: str,
    sanitized_features: SanitizedFeatures,
    risk_score: float,
) -> bool:
    allowed_request = request_type == "learning_planning"
    supported_stress = sanitized_features.stress_level.lower() in {"low", "medium", "high"}
    return allowed_request and supported_stress and risk_score < 0.8


def build_planning_prompt(state: AgentState) -> str:
    features = state["student_profile_features"]
    weakness_tags = ", ".join(features.get("weakness_tags", [])) or "none"
    return (
        "你是零信任个性化教育系统中的 AG3_AdaptiveTutor。\n"
        "你当前处于学习规划阶段，需要以自适应辅导智能体的身份完成规划任务。\n"
        "你只能根据已脱敏的学生特征生成学习规划，不能假设任何未提供的隐私信息。\n"
        "请输出严格 JSON，格式为：\n"
        "{\n"
        '  "diagnosis_result": "一句到三句的学习诊断摘要",\n'
        '  "planning_path": [\n'
        '    {"stage": "阶段名", "objective": "阶段目标", "recommended_action": "建议动作", "estimated_minutes": 15}\n'
        "  ]\n"
        "}\n\n"
        f"当前主题: {state['current_topic']}\n"
        f"认知风格(脱敏后): {features.get('cognitive_style', 'unknown')}\n"
        f"薄弱点标签: {weakness_tags}\n"
        f"压力水平: {features.get('stress_level', 'unknown')}\n"
        "规划要求:\n"
        "1. 强调渐进式学习路线。\n"
        "2. 规划内容要体现可视化支持、纠错检查与低压节奏。\n"
        "3. planning_path 输出 4 个阶段。\n"
        "4. recommended_action 必须具体、可执行。"
    )


def get_planning_llm() -> Optional[ChatOpenAI]:
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
    if not deepseek_api_key:
        return None

    return ChatOpenAI(
        api_key=deepseek_api_key,
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        temperature=0.4,
    )


def parse_llm_json(content: str) -> Dict[str, Any]:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", content, re.DOTALL)
    if match:
        return json.loads(match.group())

    raise ValueError("LLM response did not contain valid JSON.")


def mock_llm_planning_response(state: AgentState, prompt: str) -> Dict[str, Any]:
    topic = state["current_topic"]
    features = state["student_profile_features"]
    weakness_tags = features.get("weakness_tags", [])
    stress_level = features.get("stress_level", "Medium")

    diagnosis_parts = [
        f"该学生在主题“{topic}”上更适合可视化与分步演示式规划。",
        f"当前压力水平为 {stress_level}，建议采用中等节奏推进。",
    ]
    if "dimension_mismatch" in weakness_tags:
        diagnosis_parts.append("需要优先强化矩阵维度匹配判断。")
    if "calculation_carelessness" in weakness_tags:
        diagnosis_parts.append("需要加入过程检查点以减少计算粗心。")

    planning_path = [
        {
            "stage": "概念定向",
            "objective": f"建立 {topic} 的核心概念框架",
            "recommended_action": "通过图示与矩阵形状示例理解乘法条件与结果维度。",
            "estimated_minutes": 15,
        },
        {
            "stage": "规则拆解",
            "objective": "掌握维度检查与逐项相乘求和规则",
            "recommended_action": "先练习维度判断，再完成 2 组带步骤标注的例题。",
            "estimated_minutes": 20,
        },
        {
            "stage": "纠错训练",
            "objective": "降低维度混淆和计算粗心错误",
            "recommended_action": "使用检查清单：先看维度、再算元素、最后回看结果矩阵大小。",
            "estimated_minutes": 18,
        },
        {
            "stage": "迁移巩固",
            "objective": "将矩阵乘法应用到综合题中",
            "recommended_action": "完成 1 道综合应用题，并口头解释每一步为什么成立。",
            "estimated_minutes": 22,
        },
    ]

    return {
        "diagnosis_result": " ".join(diagnosis_parts),
        "planning_path": planning_path,
        "prompt_preview": prompt,
        "llm_mode": "mock",
    }


def call_real_planning_llm(prompt: str) -> Dict[str, Any]:
    llm = get_planning_llm()
    if llm is None:
        raise RuntimeError("DEEPSEEK_API_KEY is not configured.")

    response = llm.invoke(prompt)
    parsed = parse_llm_json(response.content)
    validated = PlanningAgentOutput(**parsed)
    return {
        "diagnosis_result": validated.diagnosis_result,
        "planning_path": [step.model_dump() for step in validated.planning_path],
        "llm_mode": "deepseek",
    }


def planning_agent(state: AgentState) -> AgentState:
    prompt = build_planning_prompt(state)

    try:
        llm_result = call_real_planning_llm(prompt)
        prompt_preview = prompt
        llm_error = None
    except Exception as exc:
        llm_result = mock_llm_planning_response(state, prompt)
        prompt_preview = prompt
        llm_error = str(exc)

    return {
        **state,
        "current_agent": "AG3_AdaptiveTutor",
        "diagnosis_result": llm_result["diagnosis_result"],
        "planning_path": llm_result["planning_path"],
        "prompt_preview": prompt_preview,
        "llm_mode": llm_result["llm_mode"],
        "llm_error": llm_error,
    }


def build_planning_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("planning_agent", planning_agent)
    workflow.set_entry_point("planning_agent")
    workflow.add_edge("planning_agent", END)
    return workflow.compile()


planning_graph = build_planning_graph()
router = APIRouter(prefix="/api/planning", tags=["learning-planning"])


@router.post("/learning-plan", response_model=LearningPlanningResponse)
async def create_learning_plan(request: LearningPlanningRequest) -> LearningPlanningResponse:
    risk_score = mock_get_gnn_risk_score(request)
    allowed = mock_abac_authorize(
        request_type=request.request_type,
        sanitized_features=request.payload.sanitized_features,
        risk_score=risk_score,
    )

    if not allowed:
        raise HTTPException(
            status_code=403,
            detail="ABAC authorization failed for this learning planning request.",
        )

    initial_state: AgentState = {
        "student_profile_features": request.payload.sanitized_features.model_dump(),
        "current_topic": request.payload.current_topic,
        "diagnosis_result": "",
        "planning_path": [],
        "current_agent": "AG3_AdaptiveTutor",
        "prompt_preview": "",
        "llm_mode": "mock",
        "llm_error": None,
    }

    final_state = planning_graph.invoke(initial_state)

    return LearningPlanningResponse(
        session_id=request.session_id,
        request_type=request.request_type,
        risk_score=risk_score,
        authorization="approved",
        diagnosis_result=final_state["diagnosis_result"],
        planning_path=[PlanningStep(**step) for step in final_state["planning_path"]],
        prompt_preview=final_state["prompt_preview"],
        current_agent=final_state["current_agent"],
        llm_mode=final_state["llm_mode"],
        llm_error=final_state.get("llm_error"),
    )
