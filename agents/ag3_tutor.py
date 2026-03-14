"""
AG3: 自适应辅导智能体
职责：教学大脑，生成启发式脚手架对话
输入：局部错误记录 + 学习风格标签
输出：个性化辅导对话（带启发式提问）
约束：严禁读取学生原始隐私数据
"""
from typing import Dict, Any, Optional, List
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.memory import ConversationBufferMemory

from protocols.messages import AgentRequest, AgentResponse


class AdaptiveTutorAgent:
    """
    AG3: 自适应辅导智能体
    功能：
    1. 接收学习风格标签和局部错误记录
    2. 生成符合学生风格的启发式对话
    3. 维护辅导会话上下文（不包含原始隐私）
    4. 输出"脚手架"式引导问题
    """

    def __init__(self, llm: Optional[BaseChatModel] = None):
        self.llm = llm or ChatOpenAI(
            model="gpt-4o",
            temperature=0.7  # 较高温度以促进创造性对话
        )
        self.agent_type = "AG3_AdaptiveTutor"

        # 会话记忆（每个学生独立）
        self.conversation_memory: Dict[str, ConversationBufferMemory] = {}

        # 辅导策略模板
        self.tutoring_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个自适应辅导导师，基于学生的错误和学习风格提供"脚手架式"引导。

核心原则：
1. **启发式提问**：不直接给出答案，而是通过提问引导学生自己思考
2. **风格适配**：根据学习风格调整辅导方式
   - Visual：多用图示、图表、可视化类比
   - Aural：多口头解释、讨论、故事化
   - Read/Write：提供文本材料、笔记模板
   - Kinesthetic：实践练习、动手操作、互动
3. **渐进式提示**：从简单提示开始，逐步深入
4. **正向激励**：鼓励学生的努力，而非只关注结果

输出格式：JSON格式
{{
  "scaffolding_questions": ["问题1", "问题2"],
  "explanation": "简短解释（适配风格）",
  "next_hint": "如果学生仍卡住，提供更具体提示",
  "encouragement": "正向激励语"
}}"""),
            ("system", "学生当前学习风格：{learning_style}\n最近的错误记录：\n{error_history}"),
            ("human", "{student_input}")
        ])

    def get_memory(self, student_pseudonym: str) -> ConversationBufferMemory:
        """获取学生的会话记忆"""
        if student_pseudonym not in self.conversation_memory:
            self.conversation_memory[student_pseudonym] = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
        return self.conversation_memory[student_pseudonym]

    def generate_scaffolding(
        self,
        student_pseudonym: str,
        learning_style: str,
        error_history: List[Dict[str, Any]],
        student_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成脚手架式辅导对话
        """
        print(f"[{self.agent_type}] 生成启发式辅导...")

        # 获取会话记忆
        memory = self.get_memory(student_pseudonym)

        # 调用LLM生成辅导内容
        chain = self.tutoring_prompt | self.llm

        try:
            # 格式化错误历史
            error_desc = self._format_errors(error_history)

            result = chain.invoke({
                "learning_style": learning_style,
                "error_history": error_desc,
                "student_input": student_input
            })

            response = self._parse_tutoring_response(result.content)

            # 更新会话记忆
            memory.save_context(
                {"input": student_input},
                {"output": response.get("explanation", "")}
            )

            print(f"[{self.agent_type}] ✅ 辅导内容生成完成")
            return response

        except Exception as e:
            print(f"[{self.agent_type}] ❌ 生成失败: {e}")
            return {
                "scaffolding_questions": [
                    f"你能再试一次吗？（{learning_style}风格提示：试着画个图）"
                ],
                "explanation": "抱歉，我遇到了一些问题。让我们从头开始思考这个概念。",
                "error": str(e)
            }

    def _format_errors(self, error_history: List[Dict[str, Any]]) -> str:
        """格式化错误历史"""
        if not error_history:
            return "暂无错误记录（首次辅导）"

        lines = []
        for i, error in enumerate(error_history[-5:], 1):  # 只保留最近5条
            lines.append(f"{i}. 知识点: {error.get('knowledge_point', 'Unknown')}")
            lines.append(f"   错误类型: {error.get('error_type', 'Calculation')}")
            lines.append(f"   学生答案: {error.get('student_answer', 'N/A')}")

        return "\n".join(lines)

    def _parse_tutoring_response(self, response: str) -> Dict[str, Any]:
        """解析LLM辅导响应"""
        import json
        import re

        # 尝试提取JSON
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # 备用返回
        return {
            "scaffolding_questions": [
                "你能解释一下你的思路吗？",
                "这个问题的关键点在哪里？"
            ],
            "explanation": response
        }

    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """
        处理来自网关的辅导请求
        """
        if request.task_type != "tutor":
            return AgentResponse(
                request_id=request.request_id,
                agent_type="AG3_Tutor",
                success=False,
                error="Unsupported task type"
            )

        # 提取参数
        student_pseudonym = request.data.get("student_pseudonym")
        learning_style = request.data.get("learning_style", "Mixed")
        error_history = request.data.get("error_history", [])
        student_input = request.data.get("student_input", "")

        if not student_pseudonym:
            return AgentResponse(
                request_id=request.request_id,
                agent_type="AG3_Tutor",
                success=False,
                error="Missing student identifier"
            )

        # 生成辅导内容
        result = self.generate_scaffolding(
            student_pseudonym=student_pseudonym,
            learning_style=learning_style,
            error_history=error_history,
            student_input=student_input,
            context=request.context
        )

        return AgentResponse(
            request_id=request.request_id,
            agent_type="AG3_Tutor",
            success=True,
            result=result,
            metadata={
                "student_pseudonym": student_pseudonym,
                "learning_style": learning_style
            }
        )


# 单例模式
_ag3_instance: AdaptiveTutorAgent = None


def get_ag3_agent() -> AdaptiveTutorAgent:
    """获取AG3智能体单例"""
    global _ag3_instance
    if _ag3_instance is None:
        _ag3_instance = AdaptiveTutorAgent()
    return _ag3_instance


# ============================================================
# 使用示例
# ============================================================
def demo_ag3():
    """演示AG3功能"""
    agent = get_ag3_agent()

    # 模拟输入数据
    mock_errors = [
        {
            "knowledge_point": "二次函数求极值",
            "error_type": "Calculation",
            "student_answer": "x = -b/2a（公式记错）"
        },
        {
            "knowledge_point": "二次函数图像",
            "error_type": "Conceptual",
            "student_answer": "开口方向判断错误"
        }
    ]

    print("\n" + "="*60)
    print("AG3 自适应辅导演示")
    print("="*60)

    result = agent.generate_scaffolding(
        student_pseudonym="pseudo_abc123",
        learning_style="Visual",
        error_history=mock_errors,
        student_input="我还是不太理解二次函数的顶点怎么求"
    )

    print("\n生成的辅导内容：")
    print(f"启发式提问: {result['scaffolding_questions']}")
    print(f"解释: {result.get('explanation', 'N/A')}")
    if 'next_hint' in result:
        print(f"下一步提示: {result['next_hint']}")
    print(f"激励语: {result.get('encouragement', '你做得很好！')}")


if __name__ == "__main__":
    demo_ag3()
