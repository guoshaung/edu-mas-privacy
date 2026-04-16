"""
AG5 评估智能体

当前版本重点：
1. 使用差分隐私后的逻辑流作为主评估输入。
2. 支持基于模拟同态加密的盲评估协议。
3. 提供 AG5ValueNet，供 AG3 / AG5 隐空间博弈使用。
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, List, Optional

import numpy as np
import torch
import torch.nn as nn
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from protocols.messages import AgentRequest, AgentResponse


class AG5ValueNet(nn.Module):
    """
    AG5 价值网络

    输入：
    - 128 维差分隐私逻辑流
    - 32 维 AG3 策略向量

    输出：
    - 一个 0~1 之间的 sigmoid 值，表示在该策略下通过测试的概率
    """

    def __init__(self, input_dim: int = 128 + 32):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid(),
        )

    def forward(self, student_state: torch.Tensor, tutor_strategy: torch.Tensor) -> torch.Tensor:
        if student_state.dim() == 1:
            student_state = student_state.unsqueeze(0)
        if tutor_strategy.dim() == 1:
            tutor_strategy = tutor_strategy.unsqueeze(0)

        if student_state.shape[-1] > 128:
            student_state = student_state[..., :128]
        elif student_state.shape[-1] < 128:
            student_state = torch.nn.functional.pad(student_state, (0, 128 - student_state.shape[-1]))

        features = torch.cat([student_state, tutor_strategy], dim=-1)
        return self.net(features)


class SecureSMPCScorer:
    """
    模拟 Paillier 同态加密的盲评估器。

    这里不追求真实密码学安全性，而是用于 Demo 场景展示：
    - 学生逻辑流以“密文态”进入 AG5
    - AG5 在不暴露标准答案图谱的前提下完成相似度评估
    """

    def __init__(self):
        self._last_offset: Optional[np.ndarray] = None

    def mock_encrypt(self, vector: List[float] | np.ndarray) -> List[float]:
        vector_np = np.asarray(vector, dtype=np.float32)
        offset = np.random.uniform(5_000.0, 9_000.0, size=vector_np.shape).astype(np.float32)
        self._last_offset = offset
        encrypted = vector_np + offset
        print("[SMPC] 已将学生逻辑流封装为密文态向量（Demo 偏移加密）")
        return encrypted.tolist()

    def mock_homomorphic_dot_product(
        self,
        encrypted_vec: List[float] | np.ndarray,
        plain_vec: List[float] | np.ndarray,
    ) -> float:
        print("[SMPC] 接收到加密逻辑流，开始盲计算")
        encrypted_np = np.asarray(encrypted_vec, dtype=np.float32)
        plain_np = np.asarray(plain_vec, dtype=np.float32)
        offset = self._last_offset if self._last_offset is not None else np.zeros_like(encrypted_np)

        recovered = encrypted_np - offset
        denom = (np.linalg.norm(recovered) * np.linalg.norm(plain_np)) + 1e-8
        score = float(np.dot(recovered, plain_np) / denom)
        normalized = max(0.0, min(1.0, (score + 1.0) / 2.0))
        print("[SMPC] 执行密文态点乘，标准答案图谱未暴露")
        return normalized

    def build_reference_answer_vector(self, question_id: str) -> List[float]:
        digest = hashlib.sha256(f"reference:{question_id}".encode("utf-8")).hexdigest()
        seed = int(digest[:16], 16) % (2**32)
        rng = np.random.default_rng(seed)
        return rng.normal(loc=0.0, scale=1.0, size=128).astype(np.float32).tolist()

    def evaluate_answers(self, encrypted_logic_vector: List[float], question_id: str) -> Dict[str, Any]:
        reference_vector = self.build_reference_answer_vector(question_id)
        score = self.mock_homomorphic_dot_product(encrypted_logic_vector, reference_vector)
        return {
            "question_id": question_id,
            "blind_score": score,
            "band": "high" if score >= 0.8 else "medium" if score >= 0.55 else "low",
        }


class AssessmentAgent:
    """
    AG5 评估智能体
    """

    def __init__(self, llm: Optional[BaseChatModel] = None):
        self.llm = llm or self._build_optional_llm()
        self.agent_type = "AG5_Assessment"
        self.value_net = AG5ValueNet()
        self.secure_scorer = SecureSMPCScorer()
        self.question_gen_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "你是 AG5_AssessmentAgent。你只负责根据知识点、难度和题型独立出题，"
                    "不能引用 AG3 的辅导上下文。请输出 JSON。",
                ),
                (
                    "human",
                    "知识点：{knowledge_points}\n难度：{difficulty}\n题数：{num_questions}\n题型：{question_type}",
                ),
            ]
        )

    def generate_test(
        self,
        knowledge_points: List[str],
        difficulty: float,
        num_questions: int = 5,
        question_type: str = "single_choice",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        print(f"[{self.agent_type}] 开始生成测验题")
        test_id = f"test_{hashlib.md5(json.dumps({'kp': knowledge_points, 'difficulty': difficulty}, sort_keys=True).encode()).hexdigest()[:10]}"

        try:
            if self.llm is None:
                raise RuntimeError("No available LLM client for AG5 question generation.")
            chain = self.question_gen_prompt | self.llm
            result = chain.invoke(
                {
                    "knowledge_points": ", ".join(knowledge_points),
                    "difficulty": difficulty,
                    "num_questions": num_questions,
                    "question_type": question_type,
                }
            )
            parsed = self._parse_json(result.content)
            parsed.setdefault("questions", [])
            parsed["test_id"] = test_id
            return parsed
        except Exception:
            return self._generate_fallback_test(test_id, knowledge_points, difficulty, num_questions)

    def blind_grade_with_encrypted_logic(
        self,
        encrypted_logic_vector: List[float],
        question_id: str = "default_question",
    ) -> Dict[str, Any]:
        print(f"[{self.agent_type}] 接收到加密逻辑流，开始盲评估")
        blind_result = self.secure_scorer.evaluate_answers(encrypted_logic_vector, question_id)
        print(f"[{self.agent_type}] 盲评估完成，得分={blind_result['blind_score']:.4f}")
        return blind_result

    def grade_test(
        self,
        test_spec: Dict[str, Any],
        student_answers: Dict[str, str],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        encrypted_logic_vector = None
        question_id = test_spec.get("test_id", "default_question")

        if context:
            encrypted_logic_vector = context.get("encrypted_logic_vector")
            question_id = context.get("question_id", question_id)

        if encrypted_logic_vector:
            blind_result = self.blind_grade_with_encrypted_logic(encrypted_logic_vector, question_id)
            return {
                "test_id": test_spec.get("test_id", question_id),
                "total_score": round(blind_result["blind_score"] * 100, 2),
                "question_scores": [
                    {
                        "question_id": question_id,
                        "score": round(blind_result["blind_score"] * 100, 2),
                        "max_score": 100,
                        "feedback": f"盲评估完成，风险带宽={blind_result['band']}",
                    }
                ],
                "overall_feedback": "已基于同态加密模拟协议完成盲评估。",
                "weak_points": ["需要进一步强化语义对齐"] if blind_result["blind_score"] < 0.6 else [],
                "suggested_next_topics": ["继续当前知识点练习"] if blind_result["blind_score"] < 0.8 else ["可以进入下一阶段"],
                "blind_protocol": True,
            }

        return self._fallback_grading(test_spec, student_answers)

    async def process_request(self, request: AgentRequest) -> AgentResponse:
        if request.task_type == "generate_test":
            result = self.generate_test(
                knowledge_points=request.data.get("knowledge_points", []),
                difficulty=float(request.data.get("difficulty", 0.5)),
                num_questions=int(request.data.get("num_questions", 5)),
                question_type=request.data.get("question_type", "single_choice"),
                context=request.context,
            )
            return AgentResponse(
                request_id=request.request_id,
                agent_type=request.agent_type,
                success=True,
                result=result,
            )

        if request.task_type in {"grade_test", "secure_assess"}:
            result = self.grade_test(
                test_spec=request.data.get("test_spec", {}),
                student_answers=request.data.get("student_answers", {}),
                context=request.context or request.data,
            )
            return AgentResponse(
                request_id=request.request_id,
                agent_type=request.agent_type,
                success=True,
                result=result,
            )

        return AgentResponse(
            request_id=request.request_id,
            agent_type=request.agent_type,
            success=False,
            error="Unsupported task type for AG5",
        )

    def _parse_json(self, text: str) -> Dict[str, Any]:
        import re

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                return {}
        return {}

    def _build_optional_llm(self) -> Optional[BaseChatModel]:
        deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        if deepseek_key:
            return ChatOpenAI(
                api_key=deepseek_key,
                base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
                model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
                temperature=0.35,
            )

        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            return ChatOpenAI(api_key=openai_key, model="gpt-4o", temperature=0.4)

        return None

    def _generate_fallback_test(
        self,
        test_id: str,
        knowledge_points: List[str],
        difficulty: float,
        num_questions: int,
    ) -> Dict[str, Any]:
        questions = []
        points = knowledge_points or ["矩阵基础"]
        for idx in range(num_questions):
            point = points[idx % len(points)]
            questions.append(
                {
                    "question_id": f"Q{idx + 1}",
                    "type": "single_choice",
                    "question": f"关于 {point} 的测试题 {idx + 1}",
                    "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
                    "correct_answer": "A",
                    "difficulty": difficulty,
                    "knowledge_point": point,
                    "explanation": "这是降级生成的示例题。",
                }
            )
        return {"test_id": test_id, "questions": questions, "estimated_time": num_questions * 120}

    def _fallback_grading(self, test_spec: Dict[str, Any], student_answers: Dict[str, str]) -> Dict[str, Any]:
        total_score = 0
        question_scores = []
        weak_points: List[str] = []
        for question in test_spec.get("questions", []):
            qid = question["question_id"]
            correct = question.get("correct_answer", "")
            student_answer = student_answers.get(qid, "")
            is_correct = student_answer.upper() == str(correct).upper()
            score = 10 if is_correct else 0
            total_score += score
            question_scores.append(
                {
                    "question_id": qid,
                    "score": score,
                    "max_score": 10,
                    "feedback": "正确" if is_correct else f"正确答案是 {correct}",
                }
            )
            if not is_correct:
                weak_points.append(question.get("knowledge_point", "未知知识点"))

        return {
            "test_id": test_spec.get("test_id", "fallback_test"),
            "total_score": total_score,
            "question_scores": question_scores,
            "overall_feedback": f"总分：{total_score}/{max(len(question_scores), 1) * 10}",
            "weak_points": weak_points,
            "suggested_next_topics": weak_points,
            "blind_protocol": False,
        }


_ag5_instance: Optional[AssessmentAgent] = None


def get_ag5_agent() -> AssessmentAgent:
    global _ag5_instance
    if _ag5_instance is None:
        _ag5_instance = AssessmentAgent()
    return _ag5_instance
