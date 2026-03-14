"""
AG5: 自适应评估智能体
职责：独立考官，生成和评估测试（严禁读取辅导对话上下文）
输入：知识点 + 难度 + 学习目标
输出：测试题目 + 评分结果
约束：独立于AG3，防止大模型自判幻觉
"""
from typing import Dict, Any, Optional, List
import json
import hashlib
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from protocols.messages import AgentRequest, AgentResponse


class AssessmentAgent:
    """
    AG5: 自适应评估智能体
    功能：
    1. 生成适配学生水平的测试题
    2. 接收学生作答（选项A/B/C/D或开放作答）
    3. 自动评分并提供反馈
    4. **关键约束**：完全独立于AG3，不能访问辅导对话
    """

    def __init__(self, llm: Optional[BaseChatModel] = None):
        self.llm = llm or ChatOpenAI(
            model="gpt-4o",
            temperature=0.5  # 平衡创造性和准确性
        )
        self.agent_type = "AG5_Assessment"

        # 题目生成提示词
        self.question_gen_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个题目生成专家。根据学生信息生成测试题。

输入信息：
- 知识点: {knowledge_points}
- 难度等级: {difficulty} (0-1)
- 题目数量: {num_questions}
- 题目类型: {question_type}

要求：
1. 难度精准匹配（±0.1范围）
2. 覆盖所有指定知识点
3. 题目之间相互独立
4. 选项合理（干扰项有迷惑性但不过于刁钻）
5. **绝不依赖之前的辅导对话**（独立出题）

输出格式（JSON）：
{{
  "test_id": "唯一测试标识",
  "questions": [
    {{
      "question_id": "Q1",
      "type": "single_choice",
      "question": "题目内容",
      "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
      "correct_answer": "A",
      "difficulty": 0.65,
      "knowledge_point": "知识点",
      "explanation": "答案解析"
    }}
  ],
  "estimated_time": 预计用时（秒）
}}"""),
            ("user", "生成测试题")
        ])

        # 评分提示词（不看对话，仅看答案）
        self.grading_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个客观评分助手。

你的任务：根据标准答案评分学生作答

**关键规则**：
1. **严格基于标准答案评分**，不考虑任何"语境"或"对话历史"
2. 选择题：完全匹配答案
3. 开放题：根据关键点给分
4. 只看答案内容，不参考任何其他信息

输入：
- 题目和标准答案: {questions}
- 学生作答: {student_answers}

输出（JSON）：
{{
  "test_id": "测试标识",
  "total_score": 总分（0-100）,
  "question_scores": [
    {{"question_id": "Q1", "score": 10, "max_score": 10, "feedback": "反馈"}}
  ],
  "overall_feedback": "总体评价",
  "weak_points": ["薄弱知识点"],
  "suggested_next_topics": ["建议下一步学习"]
}}"""),
            ("user", "评分")
        ])

    def generate_test(
        self,
        knowledge_points: List[str],
        difficulty: float,
        num_questions: int = 5,
        question_type: str = "single_choice",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成测试题
        注意：此函数完全独立，不依赖AG3的辅导历史
        """
        print(f"[{self.agent_type}] 生成测试...")
        print(f"  - 知识点: {knowledge_points}")
        print(f"  - 难度: {difficulty:.2f}")
        print(f"  - 题数: {num_questions}")

        # 生成唯一测试ID
        test_id = f"test_{hashlib.md5(json.dumps({
            'kc': knowledge_points,
            'difficulty': difficulty,
            'timestamp': __import__('time').time()
        }, sort_keys=True).encode()).hexdigest()[:12]}"

        # 调用LLM生成题目
        chain = self.question_gen_prompt | self.llm

        try:
            result = chain.invoke({
                "knowledge_points": ", ".join(knowledge_points),
                "difficulty": difficulty,
                "num_questions": num_questions,
                "question_type": question_type
            })

            test_spec = self._parse_test_spec(result.content)
            test_spec["test_id"] = test_id

            print(f"[{self.agent_type}] ✅ 测试生成完成: {len(test_spec['questions'])}题")
            return test_spec

        except Exception as e:
            print(f"[{self.agent_type}] ❌ 生成失败: {e}")
            # 降级到模板题目
            return self._generate_fallback_test(
                test_id, knowledge_points, difficulty, num_questions
            )

    def grade_test(
        self,
        test_spec: Dict[str, Any],
        student_answers: Dict[str, str],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        评分学生作答
        注意：仅基于答案评分，不参考辅导对话（防止自判幻觉）
        """
        print(f"[{self.agent_type}] 评分测试...")

        # 调用LLM评分
        chain = self.grading_prompt | self.llm

        try:
            result = chain.invoke({
                "questions": json.dumps(test_spec["questions"], ensure_ascii=False),
                "student_answers": json.dumps(student_answers, ensure_ascii=False)
            })

            grading_result = self._parse_grading(result.content)

            print(f"[{self.agent_type}] ✅ 评分完成: {grading_result['total_score']}/100")
            return grading_result

        except Exception as e:
            print(f"[{self.agent_type}] ❌ 评分失败: {e}")
            # 降级到规则评分
            return self._fallback_grading(test_spec, student_answers)

    def _parse_test_spec(self, response: str) -> Dict[str, Any]:
        """解析测试题生成结果"""
        json_match = __import__('re').search(r'\{.*\}', response, __import__('re').DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # 备用返回
        return {
            "questions": [],
            "estimated_time": 0
        }

    def _parse_grading(self, response: str) -> Dict[str, Any]:
        """解析评分结果"""
        json_match = __import__('re').search(r'\{.*\}', response, __import__('re').DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # 备用返回
        return {
            "total_score": 0,
            "question_scores": [],
            "overall_feedback": "评分失败"
        }

    def _generate_fallback_test(
        self,
        test_id: str,
        knowledge_points: List[str],
        difficulty: float,
        num_questions: int
    ) -> Dict[str, Any]:
        """降级：生成模板题目（不使用LLM）"""
        questions = []

        for i in range(num_questions):
            kc = knowledge_points[i % len(knowledge_points)]
            questions.append({
                "question_id": f"Q{i+1}",
                "type": "single_choice",
                "question": f"关于{kc}的题目{i+1}（难度{difficulty:.1f}）",
                "options": [
                    f"A. 选项1",
                    f"B. 选项2",
                    f"C. 选项3",
                    f"D. 选项4"
                ],
                "correct_answer": "A",
                "difficulty": difficulty,
                "knowledge_point": kc,
                "explanation": "这是模板题目"
            })

        return {
            "test_id": test_id,
            "questions": questions,
            "estimated_time": num_questions * 120
        }

    def _fallback_grading(
        self,
        test_spec: Dict[str, Any],
        student_answers: Dict[str, str]
    ) -> Dict[str, Any]:
        """降级：规则评分"""
        total_score = 0
        question_scores = []
        weak_points = []

        for q in test_spec["questions"]:
            q_id = q["question_id"]
            correct = q["correct_answer"]
            student_answer = student_answers.get(q_id, "")

            is_correct = student_answer.upper() == correct.upper()
            score = 10 if is_correct else 0
            total_score += score

            question_scores.append({
                "question_id": q_id,
                "score": score,
                "max_score": 10,
                "feedback": "正确" if is_correct else f"正确答案是{correct}"
            })

            if not is_correct:
                weak_points.append(q["knowledge_point"])

        return {
            "test_id": test_spec["test_id"],
            "total_score": total_score,
            "question_scores": question_scores,
            "overall_feedback": f"总分: {total_score}/{len(test_spec['questions'])*10}",
            "weak_points": weak_points,
            "suggested_next_topics": weak_points
        }

    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """处理来自网关的评估请求"""
        if request.task_type == "generate_test":
            # 生成测试
            knowledge_points = request.data.get("knowledge_points", [])
            difficulty = request.data.get("difficulty", 0.5)
            num_questions = request.data.get("num_questions", 5)

            result = self.generate_test(
                knowledge_points=knowledge_points,
                difficulty=difficulty,
                num_questions=num_questions,
                context=request.context
            )

            return AgentResponse(
                request_id=request.request_id,
                agent_type="AG5_Assessment",
                success=True,
                result=result,
                metadata={"num_questions": len(result["questions"])}
            )

        elif request.task_type == "grade_test":
            # 评分
            test_spec = request.data.get("test_spec", {})
            student_answers = request.data.get("student_answers", {})

            result = self.grade_test(
                test_spec=test_spec,
                student_answers=student_answers,
                context=request.context
            )

            return AgentResponse(
                request_id=request.request_id,
                agent_type="AG5_Assessment",
                success=True,
                result=result,
                metadata={"total_score": result["total_score"]}
            )

        else:
            return AgentResponse(
                request_id=request.request_id,
                agent_type="AG5_Assessment",
                success=False,
                error="Unsupported task type"
            )


# 单例模式
_ag5_instance: AssessmentAgent = None


def get_ag5_agent() -> AssessmentAgent:
    """获取AG5智能体单例"""
    global _ag5_instance
    if _ag5_instance is None:
        _ag5_instance = AssessmentAgent()
    return _ag5_instance


# ============================================================
# 使用示例
# ============================================================
def demo_ag5():
    """演示AG5功能"""
    agent = get_ag5_agent()

    print("\n" + "="*60)
    print("AG5 自适应评估演示")
    print("="*60)

    # 场景1：生成测试
    print("\n场景1：生成测试题")
    print("-" * 40)

    test_spec = agent.generate_test(
        knowledge_points=["二次函数", "顶点坐标", "最值问题"],
        difficulty=0.65,
        num_questions=3
    )

    print(f"测试ID: {test_spec['test_id']}")
    print(f"题目数: {len(test_spec['questions'])}")
    print(f"预计用时: {test_spec['estimated_time']}秒")

    for q in test_spec["questions"]:
        print(f"\n{q['question_id']}. {q['question']}")
        for opt in q['options']:
            print(f"  {opt}")

    # 场景2：评分
    print("\n场景2：评分学生作答")
    print("-" * 40)

    mock_answers = {
        "Q1": "A",
        "Q2": "B",
        "Q3": "A"  # 故意错一个
    }

    grading_result = agent.grade_test(
        test_spec=test_spec,
        student_answers=mock_answers
    )

    print(f"\n总分: {grading_result['total_score']}/100")
    print(f"总体评价: {grading_result['overall_feedback']}")
    if grading_result['weak_points']:
        print(f"薄弱点: {', '.join(grading_result['weak_points'])}")
    if grading_result['suggested_next_topics']:
        print(f"建议下一步: {', '.join(grading_result['suggested_next_topics'])}")


if __name__ == "__main__":
    demo_ag5()
