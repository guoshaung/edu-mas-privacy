from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from agents.ag5_assess import get_ag5_agent
from gateway.router import get_gateway

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True, encoding="utf-8-sig")

router = APIRouter(prefix="/assessment", tags=["learning-assessment"])
compat_router = APIRouter(tags=["learning-assessment-compat"])


class AssessmentRequest(BaseModel):
    session_id: str
    current_topic: str = "General Topic"
    sanitized_profile: Dict[str, Any] = Field(default_factory=dict)
    learning_plan: List[str] = Field(default_factory=list)
    action: Literal["generate", "submit"] = "generate"
    answers: Dict[str, str] = Field(default_factory=dict)
    gnn_risk_score: float = Field(default=0.2, ge=0.0, le=1.0)


class AssessmentQuestion(BaseModel):
    question_id: str
    prompt: str
    options: List[str]
    target_skill: str
    difficulty: str


class AssessmentResponse(BaseModel):
    session_id: str
    current_phase: str
    quiz: List[AssessmentQuestion]
    score: int
    total: int
    mastery_level: str
    feedback: List[str]
    next_focus: List[str]
    gnn_risk_score: float
    llm_mode: str
    llm_error: Optional[str] = None


class AssessmentLLMQuestion(BaseModel):
    question_id: str
    prompt: str
    options: List[str]
    answer: str
    target_skill: str
    difficulty: str


class AssessmentLLMOutput(BaseModel):
    quiz: List[AssessmentLLMQuestion]


assessment_store: Dict[str, Dict[str, Any]] = {}


class RiskError(RuntimeError):
    pass


def get_deepseek_llm() -> Optional[ChatOpenAI]:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return None

    return ChatOpenAI(
        api_key=api_key,
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        temperature=0.3,
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


def enforce_abac(score: float, phase: str) -> None:
    if score > 0.8:
        raise RiskError(f"[ABAC] Phase: {phase}, Score: {score}, Circuit Breaker Triggered")
    print(f"[ABAC] Phase: {phase}, Score: {score}, Allowed")


def build_generation_prompt(request: AssessmentRequest) -> str:
    weakness_tags = ", ".join(request.sanitized_profile.get("weakness_tags", [])) or "none"
    plan_lines = "\n".join([f"- {item}" for item in request.learning_plan]) or "- build a basic checkpoint"
    return (
        "You are AG5_AssessmentAgent in a privacy-preserving tutoring system.\n"
        "Generate exactly 3 multiple-choice questions in strict JSON.\n"
        "Return this schema only:\n"
        "{\n"
        '  "quiz": [\n'
        '    {"question_id": "q1", "prompt": "...", "options": ["A", "B", "C", "D"], "answer": "A", "target_skill": "...", "difficulty": "easy"}\n'
        "  ]\n"
        "}\n\n"
        f"Current topic: {request.current_topic}\n"
        f"Weakness tags: {weakness_tags}\n"
        f"Stress level: {request.sanitized_profile.get('stress_level', 'unknown')}\n"
        f"Learning plan:\n{plan_lines}\n"
        "Requirements:\n"
        "1. Focus on concept understanding, procedure checking, and transfer.\n"
        "2. Keep the questions school-friendly and concise.\n"
        "3. Options must be single-choice."
    )


def mock_quiz(topic: str) -> List[Dict[str, Any]]:
    return [
        {
            "question_id": "q1",
            "prompt": f"For {topic}, when can matrix A times matrix B be computed?",
            "options": [
                "A. When the number of columns of A equals the number of rows of B",
                "B. When both matrices have the same number of rows",
                "C. When both matrices are square matrices",
                "D. When the number of rows of A equals the number of columns of B",
            ],
            "answer": "A",
            "target_skill": "dimension_check",
            "difficulty": "easy",
        },
        {
            "question_id": "q2",
            "prompt": "What should you check immediately after computing one element of the result matrix?",
            "options": [
                "A. Whether the final matrix has the expected dimensions",
                "B. Whether all entries are positive",
                "C. Whether the matrices can be added",
                "D. Whether the determinant is non-zero",
            ],
            "answer": "A",
            "target_skill": "process_check",
            "difficulty": "medium",
        },
        {
            "question_id": "q3",
            "prompt": "Which strategy best shows transfer of matrix multiplication knowledge?",
            "options": [
                "A. Explaining why row-column matching matters before calculation",
                "B. Memorizing one worked example only",
                "C. Skipping dimension checks to save time",
                "D. Replacing matrices with unrelated formulas",
            ],
            "answer": "A",
            "target_skill": "transfer_application",
            "difficulty": "medium",
        },
    ]


def generate_quiz(request: AssessmentRequest) -> Dict[str, Any]:
    prompt = build_generation_prompt(request)
    try:
        llm = get_deepseek_llm()
        if llm is None:
            raise RuntimeError("DEEPSEEK_API_KEY is not configured.")
        response = llm.invoke(prompt)
        parsed = parse_json_payload(response.content)
        validated = AssessmentLLMOutput(**parsed)
        quiz = [item.model_dump() for item in validated.quiz[:3]]
        llm_mode = "deepseek"
        llm_error = None
    except Exception as exc:
        quiz = mock_quiz(request.current_topic)
        llm_mode = "mock"
        llm_error = str(exc)

    return {"quiz": quiz, "llm_mode": llm_mode, "llm_error": llm_error}


def public_quiz(quiz: List[Dict[str, Any]]) -> List[AssessmentQuestion]:
    return [
        AssessmentQuestion(
            question_id=item["question_id"],
            prompt=item["prompt"],
            options=item["options"],
            target_skill=item["target_skill"],
            difficulty=item["difficulty"],
        )
        for item in quiz
    ]


def evaluate_answers(quiz: List[Dict[str, Any]], answers: Dict[str, str]) -> Dict[str, Any]:
    total = len(quiz)
    score = 0
    weak_skills: List[str] = []
    feedback: List[str] = []

    for item in quiz:
        correct = item["answer"]
        user_answer = (answers.get(item["question_id"], "") or "").strip().upper()
        if user_answer == correct:
            score += 1
            feedback.append(f"{item['question_id']}: correct, {item['target_skill']} is improving.")
        else:
            weak_skills.append(item["target_skill"])
            feedback.append(
                f"{item['question_id']}: expected {correct}. Review {item['target_skill']} before moving on."
            )

    ratio = score / total if total else 0.0
    if ratio >= 0.8:
        mastery_level = "high"
        next_focus = ["increase transfer problems", "move to mixed practice"]
    elif ratio >= 0.5:
        mastery_level = "medium"
        next_focus = ["repeat guided practice", "add one error-check checkpoint"]
    else:
        mastery_level = "low"
        next_focus = weak_skills or ["return to concept explanation", "slow down and use visual support"]

    return {
        "score": score,
        "total": total,
        "mastery_level": mastery_level,
        "feedback": feedback,
        "next_focus": next_focus,
    }


@router.post("/session", response_model=AssessmentResponse)
@compat_router.post("/api/assessment/session", response_model=AssessmentResponse, include_in_schema=False)
@compat_router.post("/api/session/assessment", response_model=AssessmentResponse, include_in_schema=False)
async def assessment_session(request: AssessmentRequest) -> AssessmentResponse:
    enforce_abac(request.gnn_risk_score, "Assessment")

    if request.action == "generate":
        generated = generate_quiz(request)
        quiz = generated["quiz"]
        assessment_store[request.session_id] = {
            "quiz": quiz,
            "current_topic": request.current_topic,
            "learning_plan": request.learning_plan,
        }
        return AssessmentResponse(
            session_id=request.session_id,
            current_phase="Assessment",
            quiz=public_quiz(quiz),
            score=0,
            total=len(quiz),
            mastery_level="pending",
            feedback=["Question set generated. Submit answers to receive mastery feedback."],
            next_focus=["complete the current assessment"],
            gnn_risk_score=request.gnn_risk_score,
            llm_mode=generated["llm_mode"],
            llm_error=generated["llm_error"],
        )

    session = assessment_store.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Assessment session not found. Generate a quiz first.")

    quiz = session["quiz"]
    try:
        gateway = get_gateway()
        ag5_agent = get_ag5_agent()
        answer_text = " | ".join([f"{qid}:{ans}" for qid, ans in sorted(request.answers.items())]) or "no_answer"
        dual_stream = gateway._build_dual_stream_payload(
            text_input=f"{request.current_topic} {answer_text}",
            epsilon=gateway.privacy_engine.epsilon,
        )
        encrypted_logic_vector = ag5_agent.secure_scorer.mock_encrypt(dual_stream["noisy_logic_vector"])
        blind_result = ag5_agent.grade_test(
            test_spec={"test_id": request.session_id, "questions": quiz},
            student_answers=request.answers,
            context={
                "encrypted_logic_vector": encrypted_logic_vector,
                "question_id": request.session_id,
            },
        )
        blind_feedback = [
            question_score.get("feedback", "")
            for question_score in blind_result.get("question_scores", [])
            if question_score.get("feedback")
        ]
        if blind_result.get("overall_feedback"):
            blind_feedback.insert(0, blind_result["overall_feedback"])
        result = {
            "score": round(float(blind_result["total_score"])),
            "total": 100,
            "mastery_level": "high" if blind_result["total_score"] >= 80 else "medium" if blind_result["total_score"] >= 55 else "low",
            "feedback": blind_feedback or ["已完成盲评估。"],
            "next_focus": blind_result.get("suggested_next_topics", []),
        }
        mode = "blind_evaluation"
    except Exception:
        result = evaluate_answers(quiz, request.answers)
        mode = "evaluation"
    return AssessmentResponse(
        session_id=request.session_id,
        current_phase="Assessment",
        quiz=public_quiz(quiz),
        score=result["score"],
        total=result["total"],
        mastery_level=result["mastery_level"],
        feedback=result["feedback"],
        next_focus=result["next_focus"],
        gnn_risk_score=request.gnn_risk_score,
        llm_mode=mode,
        llm_error=None,
    )
