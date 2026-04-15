from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, TypedDict

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from agents.ag3_tutor import get_ag3_agent
from gateway.fedgnn_gateway import get_fedgnn_risk_score_for_session
from gateway.router import get_gateway
from gateway.public_bank_store import search_bank_for_student


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True, encoding="utf-8-sig")


class TutoringChatRequest(BaseModel):
    session_id: str
    sanitized_profile: Dict[str, Any]
    current_topic: str = "General Topic"
    user_message: str = ""
    gnn_risk_score: float = Field(default=0.2, ge=0.0, le=1.0)


class TutoringChatResponse(BaseModel):
    session_id: str
    current_phase: str
    learning_plan: List[str]
    tutor_reply: str
    reflection_scratchpad: str
    need_ag4_search: bool
    ag4_retrieved_context: str
    gnn_risk_score: float
    llm_mode: str
    llm_error: Optional[str] = None
    chat_history_preview: List[Dict[str, str]]


class TutoringLLMOutput(BaseModel):
    tutor_reply: str
    need_ag4_search: bool
    search_query: str = ""


class PlanningLLMOutput(BaseModel):
    learning_plan: List[str]


class SystemState(TypedDict, total=False):
    sanitized_profile: Dict[str, Any]
    learning_plan: List[str]
    chat_history: List[BaseMessage]
    reflection_scratchpad: str
    current_phase: str
    gnn_risk_score: float
    need_ag4_search: bool
    ag4_retrieved_context: str
    session_id: str
    current_topic: str
    latest_user_message: str
    tutor_reply: str
    search_query: str
    llm_mode: str
    llm_error: Optional[str]
    entry_route: Literal["planning", "reflection", "tutoring"]
    updated_at: str


session_store: Dict[str, SystemState] = {}
router = APIRouter(prefix="/chat", tags=["adaptive-tutoring"])
compat_router = APIRouter(tags=["adaptive-tutoring-compat"])


def get_deepseek_llm() -> Optional[ChatOpenAI]:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return None

    return ChatOpenAI(
        api_key=api_key,
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        temperature=0.4,
    )


def parse_json_payload(content: str) -> Dict[str, Any]:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", content, re.DOTALL)
    if match:
        return json.loads(match.group())

    raise ValueError("LLM response did not contain valid JSON.")


def bootstrap_node(state: SystemState) -> SystemState:
    if not state.get("learning_plan"):
        return {**state, "entry_route": "planning", "current_phase": "Planning"}

    if state.get("latest_user_message"):
        return {**state, "entry_route": "reflection", "current_phase": "Tutoring"}

    return {**state, "entry_route": "tutoring", "current_phase": "Tutoring"}


def route_from_bootstrap(state: SystemState) -> str:
    if state["entry_route"] == "reflection":
        return "reflexion_evaluator_node"
    return "abac_gateway_node"


def route_from_abac(state: SystemState) -> str:
    phase = state.get("current_phase", "Tutoring")
    if phase == "Planning":
        return "ag3_planning_node"
    if phase == "Mining":
        return "ag4_mining_node"
    return "ag3_tutoring_node"


def route_after_tutoring(state: SystemState) -> str:
    if state.get("need_ag4_search", False):
        return "abac_gateway_node"
    return END


def abac_gateway_node(state: SystemState) -> SystemState:
    score = state.get("gnn_risk_score", 0.0)
    phase = state.get("current_phase", "Tutoring")

    if score > 0.8:
        raise RuntimeError(f"[ABAC] Phase: {phase}, Score: {score}, Circuit Breaker Triggered")

    if phase == "Mining":
        print(f"[ABAC] Phase: {phase}, Score: {score}, Allowed AG4 Access")
    else:
        print(f"[ABAC] Phase: {phase}, Score: {score}, Allowed")

    return state


def build_planning_prompt(state: SystemState) -> str:
    return (
        "你是 AG3_AdaptiveTutor，目前处于宏观规划阶段。\n"
        "请仅依据脱敏画像和当前主题生成 3 个学习规划步骤。\n"
        "输出严格 JSON:\n"
        '{"learning_plan": ["步骤1", "步骤2", "步骤3"]}\n\n'
        f"当前主题: {state.get('current_topic', 'General Topic')}\n"
        f"脱敏画像: {json.dumps(state.get('sanitized_profile', {}), ensure_ascii=False)}"
    )


def mock_planning_plan(state: SystemState) -> List[str]:
    topic = state.get("current_topic", "当前主题")
    return [
        f"先通过可视化材料建立 {topic} 的整体概念框架。",
        "再围绕易错点做分步练习与过程检查。",
        "最后用综合题完成迁移巩固并形成自我复盘。",
    ]


def ag3_planning_node(state: SystemState) -> SystemState:
    prompt = build_planning_prompt(state)
    llm_error = state.get("llm_error")
    llm_mode = "mock"

    try:
        llm = get_deepseek_llm()
        if llm is None:
            raise RuntimeError("DEEPSEEK_API_KEY is not configured.")
        response = llm.invoke(prompt)
        parsed = parse_json_payload(response.content)
        validated = PlanningLLMOutput(**parsed)
        learning_plan = validated.learning_plan[:3]
        llm_mode = "deepseek"
        llm_error = None
    except Exception as exc:
        learning_plan = mock_planning_plan(state)
        llm_error = str(exc)

    return {
        **state,
        "learning_plan": learning_plan,
        "current_phase": "Tutoring",
        "llm_mode": llm_mode,
        "llm_error": llm_error,
        "updated_at": timestamp_text(),
    }


def build_tutoring_prompt(state: SystemState) -> str:
    history_lines = []
    for message in state.get("chat_history", [])[-6:]:
        role = "学生" if isinstance(message, HumanMessage) else "辅导智能体"
        history_lines.append(f"{role}: {message.content}")

    history_text = "\n".join(history_lines) if history_lines else "暂无历史对话"
    plan_text = "\n".join([f"{idx + 1}. {step}" for idx, step in enumerate(state.get("learning_plan", []))])

    return (
        "你是 AG3_AdaptiveTutor，目前处于微观辅导阶段。\n"
        "请结合 learning_plan、reflection_scratchpad 和 AG4 检索内容进行辅导。\n"
        "如果知识储备不足以回答，必须输出 need_ag4_search=true，并暂停生成辅导话术。\n"
        "输出严格 JSON:\n"
        "{\n"
        '  "tutor_reply": "本轮辅导话术，如果 need_ag4_search=true 则可以为空字符串",\n'
        '  "need_ag4_search": false,\n'
        '  "search_query": "如需 AG4 检索则提供检索关键词，否则为空"\n'
        "}\n\n"
        f"当前主题: {state.get('current_topic', 'General Topic')}\n"
        f"学习规划:\n{plan_text}\n\n"
        f"反思草稿:\n{state.get('reflection_scratchpad', '暂无')}\n\n"
        f"AG4 返回内容:\n{state.get('ag4_retrieved_context', '暂无')}\n\n"
        f"最近对话:\n{history_text}\n\n"
        f"学生最新输入: {state.get('latest_user_message', '') or '请给出本轮开场辅导'}"
    )


def mock_tutoring_output(state: SystemState) -> Dict[str, Any]:
    latest_message = state.get("latest_user_message", "")
    retrieved = state.get("ag4_retrieved_context", "")
    needs_search = False
    search_query = ""

    if latest_message and any(keyword in latest_message for keyword in ["变式", "例题", "更多题", "题库"]) and not retrieved:
        needs_search = True
        search_query = f"{state.get('current_topic', '当前主题')} 变式题 维度匹配"

    if needs_search:
        return {
            "tutor_reply": "",
            "need_ag4_search": True,
            "search_query": search_query,
            "llm_mode": "mock",
        }

    plan_focus = state.get("learning_plan", ["先建立概念框架"])[0]
    context_suffix = f" 我已经结合补充材料：{retrieved}" if retrieved else ""
    return {
        "tutor_reply": (
            f"我们先按当前规划的第一步来推进：{plan_focus}。"
            f"你先试着说一说矩阵乘法里两个矩阵为什么不能随便相乘？{context_suffix}"
        ),
        "need_ag4_search": False,
        "search_query": "",
        "llm_mode": "mock",
    }

def build_ag4_policy_context(item: Dict[str, Any], index: int) -> List[str]:
    policy = item.get("delivery_policy", {})
    decision = policy.get("decision", "summary_only")
    reason = policy.get("reason", "未提供版权说明。")
    visible = policy.get("student_visible_content", "")

    return [
        (
            f"{index}. {item.get('title', '未命名资源')} | 学科: {item.get('subject', '未分类')} | "
            f"类型: {item.get('resource_type', 'resource')}"
        ),
        (
            f"   版权等级: {item.get('copyright_level', 'unknown')} | "
            f"授权范围: {item.get('access_scope', 'unknown')} | "
            f"交付策略: {decision}"
        ),
        f"   策略说明: {reason}",
        f"   面向学生/AG3的可见内容: {visible}",
        (
            f"   教师策略提示: {policy.get('teacher_policy_hint', '未定义')} | "
            f"允许原文: {item.get('allow_fulltext_to_student', False)} | "
            f"允许衍生生成: {item.get('allow_derivative_generation', True)}"
        ),
    ]


def should_force_ag4_search(state: SystemState) -> bool:
    latest_message = str(state.get("latest_user_message", ""))
    if not latest_message or state.get("ag4_retrieved_context"):
        return False
    trigger_keywords = ["变式", "例题", "更多题", "题库", "讲义", "资料", "原文"]
    return any(keyword in latest_message for keyword in trigger_keywords)


def ag3_tutoring_node(state: SystemState) -> SystemState:
    llm_error = state.get("llm_error")
    latest_message = state.get("latest_user_message", "") or "请给出本轮开场辅导。"

    try:
        gateway = get_gateway()
        risk_score = float(state.get("gnn_risk_score", 0.2))
        epsilon = gateway.privacy_engine.epsilon
        dual_stream = gateway._build_dual_stream_payload(text_input=latest_message, epsilon=epsilon)
        duration_ratio = min(1.0, max(0.05, len(latest_message) / 500.0))
        _privacy_trust = gateway.privacy_engine.get_privacy_trust_snapshot(
            duration_ratio=duration_ratio,
            gnn_risk_score=risk_score,
        )
        noisy_state = dual_stream.get("noisy_privacy_vector", [])
        ag3_agent = get_ag3_agent()
        tutoring_result = ag3_agent.generate_scaffolding(
            student_input=latest_message,
            noisy_privacy_state=noisy_state,
            logic_topic=state.get("current_topic", "当前知识点"),
        )
        tutor_reply = tutoring_result.get("explanation", "")
        guidance_steps = tutoring_result.get("guidance_steps", [])
        encouragement = tutoring_result.get("encouragement", "")
        if guidance_steps:
            tutor_reply = tutor_reply + "\n\n辅导步骤：\n- " + "\n- ".join(guidance_steps)
        if encouragement:
            tutor_reply = tutor_reply + f"\n\n鼓励：{encouragement}"
        need_ag4_search = False
        search_query = ""
        llm_mode = "latent_marl"
        llm_error = None
    except Exception as exc:
        mock_result = mock_tutoring_output(state)
        tutor_reply = mock_result["tutor_reply"]
        need_ag4_search = mock_result["need_ag4_search"]
        search_query = mock_result["search_query"]
        llm_mode = mock_result["llm_mode"]
        llm_error = str(exc)

    if should_force_ag4_search(state):
        need_ag4_search = True
        tutor_reply = ""
        if not search_query:
            search_query = f"{state.get('current_topic', '当前主题')} 变式题 讲义 题库"

    new_history = list(state.get("chat_history", []))
    if tutor_reply and not need_ag4_search:
        new_history.append(AIMessage(content=tutor_reply))

    next_phase = "Mining" if need_ag4_search else "Tutoring"

    return {
        **state,
        "chat_history": new_history,
        "tutor_reply": tutor_reply,
        "need_ag4_search": need_ag4_search,
        "search_query": search_query,
        "current_phase": next_phase,
        "llm_mode": llm_mode,
        "llm_error": llm_error,
        "updated_at": timestamp_text(),
    }


def ag4_mining_node(state: SystemState) -> SystemState:
    query = state.get("search_query") or f"{state.get('current_topic', '当前主题')} 公共题库 变式题"
    results = search_bank(query=query, topic=state.get("current_topic", ""), limit=3)

    if results:
        lines = [f"[AG4 公共题库检索] 关键词: {query}"]
        for index, item in enumerate(results, start=1):
            lines.append(
                f"{index}. {item.get('title', '未命名资源')} | 学科: {item.get('subject', '未分类')} | "
                f"类型: {item.get('resource_type', 'resource')}"
            )
            lines.append(f"   标签: {', '.join(item.get('tags', [])) or '无'}")
            lines.append(f"   内容: {item.get('content', '')}")
        retrieved = "\n".join(lines)
    else:
        retrieved = (
            f"[AG4 公共题库检索] 关键词: {query}\n"
            "当前没有命中教师公共题库，建议教师在题库管理页补充相关讲义、题目或知识文档。"
        )

    return {
        **state,
        "ag4_retrieved_context": retrieved,
        "need_ag4_search": False,
        "current_phase": "Tutoring",
        "updated_at": timestamp_text(),
    }


def ag4_mining_node(state: SystemState) -> SystemState:
    query = state.get("search_query") or f"{state.get('current_topic', '当前主题')} 公共题库 变式题"
    results = search_bank_for_student(query=query, topic=state.get("current_topic", ""), limit=3)

    if results:
        lines = [
            f"[AG4 公共题库检索] 检索词: {query}",
            "以下结果已经过版权字段判定，AG3 只能使用当前策略允许的内容粒度。",
        ]
        for index, item in enumerate(results, start=1):
            lines.extend(build_ag4_policy_context(item, index))
            tags = ", ".join(item.get("tags", [])) or "无标签"
            lines.append(f"   标签: {tags}")
        retrieved = "\n".join(lines)
    else:
        retrieved = (
            f"[AG4 公共题库检索] 检索词: {query}\n"
            "当前没有命中教师公共题库。请教师在题库管理页补充资料，并设置版权等级与授权范围。"
        )

    return {
        **state,
        "ag4_retrieved_context": retrieved,
        "need_ag4_search": False,
        "current_phase": "Tutoring",
        "updated_at": timestamp_text(),
    }


def reflexion_evaluator_node(state: SystemState) -> SystemState:
    latest = state.get("latest_user_message", "")
    old_pad = state.get("reflection_scratchpad", "")

    triggers = ["听不懂", "不明白", "还是不会", "做错", "看不懂", "不会做", "又错了"]
    if any(token in latest for token in triggers):
        reflection = (
            "Reflexion: 学生反馈持续存在理解障碍，需要下一轮辅导进一步降低抽象度。"
            "优先回到规划中的基础步骤，增加可视化解释和过程检查提示。"
        )
        if old_pad:
            reflection = old_pad + "\n" + reflection
        return {**state, "reflection_scratchpad": reflection, "updated_at": timestamp_text()}

    return {**state, "updated_at": timestamp_text()}


def build_tutoring_graph():
    workflow = StateGraph(SystemState)
    workflow.add_node("bootstrap_node", bootstrap_node)
    workflow.add_node("abac_gateway_node", abac_gateway_node)
    workflow.add_node("ag3_planning_node", ag3_planning_node)
    workflow.add_node("ag3_tutoring_node", ag3_tutoring_node)
    workflow.add_node("ag4_mining_node", ag4_mining_node)
    workflow.add_node("reflexion_evaluator_node", reflexion_evaluator_node)

    workflow.add_edge(START, "bootstrap_node")
    workflow.add_conditional_edges(
        "bootstrap_node",
        route_from_bootstrap,
        {
            "abac_gateway_node": "abac_gateway_node",
            "reflexion_evaluator_node": "reflexion_evaluator_node",
        },
    )
    workflow.add_conditional_edges(
        "abac_gateway_node",
        route_from_abac,
        {
            "ag3_planning_node": "ag3_planning_node",
            "ag3_tutoring_node": "ag3_tutoring_node",
            "ag4_mining_node": "ag4_mining_node",
        },
    )
    workflow.add_edge("ag3_planning_node", "abac_gateway_node")
    workflow.add_conditional_edges(
        "ag3_tutoring_node",
        route_after_tutoring,
        {
            "abac_gateway_node": "abac_gateway_node",
            END: END,
        },
    )
    workflow.add_edge("ag4_mining_node", "ag3_tutoring_node")
    workflow.add_edge("reflexion_evaluator_node", "abac_gateway_node")

    return workflow.compile()


tutoring_graph = build_tutoring_graph()


def serialize_history(messages: List[BaseMessage]) -> List[Dict[str, str]]:
    serialized = []
    for message in messages[-8:]:
        role = "human" if isinstance(message, HumanMessage) else "ai"
        serialized.append({"role": role, "content": message.content})
    return serialized


def timestamp_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@router.post("/tutoring", response_model=TutoringChatResponse)
@compat_router.post("/api/chat/tutoring", response_model=TutoringChatResponse, include_in_schema=False)
@compat_router.post("/api/tutoring", response_model=TutoringChatResponse, include_in_schema=False)
async def tutoring_chat(request: TutoringChatRequest) -> TutoringChatResponse:
    state = session_store.get(
        request.session_id,
        {
            "session_id": request.session_id,
            "sanitized_profile": {},
            "learning_plan": [],
            "chat_history": [],
            "reflection_scratchpad": "",
            "current_phase": "Planning",
            "gnn_risk_score": request.gnn_risk_score,
            "need_ag4_search": False,
            "ag4_retrieved_context": "",
            "current_topic": request.current_topic,
            "latest_user_message": "",
            "tutor_reply": "",
            "search_query": "",
            "llm_mode": "mock",
            "llm_error": None,
            "updated_at": timestamp_text(),
        },
    )

    state["sanitized_profile"] = request.sanitized_profile or state.get("sanitized_profile", {})
    state["current_topic"] = request.current_topic or state.get("current_topic", "General Topic")
    state["gnn_risk_score"] = max(
        request.gnn_risk_score,
        get_fedgnn_risk_score_for_session(request.session_id, fallback=request.gnn_risk_score),
    )
    state["latest_user_message"] = request.user_message.strip()
    state["need_ag4_search"] = False
    state["search_query"] = ""
    state["updated_at"] = timestamp_text()

    if request.user_message.strip():
        state["chat_history"] = list(state.get("chat_history", [])) + [HumanMessage(content=request.user_message.strip())]

    try:
        final_state = tutoring_graph.invoke(state)
    except RuntimeError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    session_store[request.session_id] = final_state

    return TutoringChatResponse(
        session_id=request.session_id,
        current_phase=final_state.get("current_phase", "Tutoring"),
        learning_plan=final_state.get("learning_plan", []),
        tutor_reply=final_state.get("tutor_reply", ""),
        reflection_scratchpad=final_state.get("reflection_scratchpad", ""),
        need_ag4_search=final_state.get("need_ag4_search", False),
        ag4_retrieved_context=final_state.get("ag4_retrieved_context", ""),
        gnn_risk_score=final_state.get("gnn_risk_score", 0.0),
        llm_mode=final_state.get("llm_mode", "mock"),
        llm_error=final_state.get("llm_error"),
        chat_history_preview=serialize_history(final_state.get("chat_history", [])),
    )
