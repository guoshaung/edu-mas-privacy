from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel, Field

from gateway.public_bank_store import evaluate_student_access, load_bank, save_bank
from gateway.tutoring_gateway import session_store


router = APIRouter(prefix="/teacher", tags=["teacher"])


class TeacherResourceCreate(BaseModel):
    title: str = Field(..., min_length=1)
    subject: str = Field(..., min_length=1)
    resource_type: Literal["exercise", "lesson_note", "knowledge_doc", "worksheet"] = "lesson_note"
    tags: list[str] = Field(default_factory=list)
    content: str = Field(..., min_length=1)
    source: str = "教师上传"
    owner_teacher: str = "李四"
    copyright_level: Literal[
        "public_open",
        "school_authorized",
        "class_authorized",
        "teacher_private",
        "restricted_original",
    ] = "school_authorized"
    access_scope: Literal["public", "school", "class", "teacher_only"] = "school"
    allow_fulltext_to_student: bool = False
    allow_derivative_generation: bool = True


def _now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _message_excerpt(messages: list[Any]) -> str:
    if not messages:
        return "学生尚未开始多轮交互。"
    last = messages[-1]
    content = getattr(last, "content", "")
    return str(content)[:80] if content else "暂无内容"


def _build_agent_cards(state: dict[str, Any]) -> list[dict[str, Any]]:
    profile = state.get("sanitized_profile", {})
    learning_plan = state.get("learning_plan", [])
    retrieved = state.get("ag4_retrieved_context", "")
    return [
        {
            "agent": "AG2_DiagnosisAgent",
            "status": "done" if profile else "idle",
            "summary": "已接收脱敏画像标签，用于后续教学编排。",
        },
        {
            "agent": "AG3_AdaptiveTutor",
            "status": "running" if learning_plan else "idle",
            "summary": "负责学习规划与当前微观辅导。",
        },
        {
            "agent": "AG4_ContentMiner",
            "status": "ready" if retrieved else "standby",
            "summary": "按需从教师公共题库检索题目、教案和知识文档，并受版权策略约束。",
        },
        {
            "agent": "AG5_AssessmentAgent",
            "status": "standby",
            "summary": "等待接收本轮辅导结果，准备生成阶段性检验。",
        },
    ]


@router.get("/summary")
async def teacher_summary() -> dict[str, Any]:
    bank = load_bank()
    active_sessions = len(session_store)
    ag4_ready = len(bank)
    copyright_count = sum(1 for item in bank if item.get("copyright_level") != "public_open")
    return {
        "active_sessions": active_sessions,
        "resource_count": len(bank),
        "ag4_ready_count": ag4_ready,
        "copyright_controlled_count": copyright_count,
        "updated_at": _now_text(),
    }


@router.get("/question-bank")
async def get_question_bank() -> dict[str, Any]:
    items = load_bank()
    enriched_items = [{**item, "delivery_policy": evaluate_student_access(item)} for item in items]
    return {
        "total": len(enriched_items),
        "items": enriched_items,
        "subjects": sorted({item.get("subject", "未分类") for item in items}),
    }


@router.post("/question-bank")
async def create_question_bank_item(payload: TeacherResourceCreate) -> dict[str, Any]:
    items = load_bank()
    record = {
        "id": f"res_{uuid4().hex[:10]}",
        "title": payload.title,
        "subject": payload.subject,
        "resource_type": payload.resource_type,
        "tags": payload.tags,
        "content": payload.content,
        "source": payload.source,
        "owner_teacher": payload.owner_teacher,
        "copyright_level": payload.copyright_level,
        "access_scope": payload.access_scope,
        "allow_fulltext_to_student": payload.allow_fulltext_to_student,
        "allow_derivative_generation": payload.allow_derivative_generation,
        "created_at": _now_text(),
    }
    items.insert(0, record)
    save_bank(items)
    return {"ok": True, "item": record, "total": len(items)}


@router.get("/agent-monitor")
async def teacher_agent_monitor() -> dict[str, Any]:
    sessions = []
    for session_id, state in session_store.items():
        profile = state.get("sanitized_profile", {})
        sessions.append(
            {
                "session_id": session_id,
                "student_alias": profile.get("student_alias", "匿名学生"),
                "current_topic": state.get("current_topic", "未设定主题"),
                "current_phase": state.get("current_phase", "Planning"),
                "risk_score": state.get("gnn_risk_score", 0.0),
                "message_excerpt": _message_excerpt(state.get("chat_history", [])),
                "updated_at": state.get("updated_at", _now_text()),
                "agent_cards": _build_agent_cards(state),
                "teaching_flow": [
                    "A1 提交脱敏画像",
                    "AG2 完成诊断摘要",
                    "AG3 生成学习规划",
                    "AG3 执行自适应辅导",
                    "AG4 按需检索公共题库",
                    "AG5 等待知识检验触发",
                ],
            }
        )

    sessions.sort(key=lambda item: item["updated_at"], reverse=True)
    return {
        "updated_at": _now_text(),
        "session_count": len(sessions),
        "sessions": sessions,
    }
