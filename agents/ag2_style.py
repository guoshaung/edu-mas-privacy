"""
AG2: 学习风格识别智能体
职责：接收脱敏特征，进行学习风格诊断
输入：SRPG保护后的特征向量
输出：学习风格标签（视觉型/听觉型/读写型/动觉型）
"""
from typing import Dict, Any, Optional
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from protocols.messages import AgentRequest, AgentResponse, ProtectedFeatures


class LearningStyleAgent:
    """
    AG2: 学习风格识别智能体
    功能：
    1. 接收网关传来的脱敏特征
    2. 基于VARK模型分析学习风格
    3. 输出风格标签 + 置信度
    """

    def __init__(self, llm: Optional[BaseChatModel] = None):
        self.llm = llm or ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3
        )
        self.agent_type = "AG2_StyleRecognition"

        # 分析提示词模板
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个学习风格分析专家，基于VARK模型（Visual视觉型、Aural听觉型、Read/Write读写型、Kinesthetic动觉型）。

你的任务：
1. 分析提供的特征向量，推断学生的学习风格倾向
2. 输出格式：JSON格式，包含：
   - primary_style: 主要风格（Visual/Aural/ReadWrite/Kinesthetic）
   - secondary_style: 次要风格（可选）
   - confidence: 置信度（0-1）
   - reasoning: 简短分析理由

注意：特征值是经过隐私保护的近似值，分析时考虑不确定性。"""),
            ("user", "特征向量数据：\n{features}")
        ])

    def analyze(
        self,
        protected_features: Dict[str, float],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        分析学习风格
        注意：这里接收的是已经过SRPG处理的特征
        """
        print(f"[{self.agent_type}] 开始学习风格分析...")

        # 构建特征描述
        feature_desc = self._format_features(protected_features)

        # 调用LLM分析
        chain = self.analysis_prompt | self.llm
        try:
            result = chain.invoke({"features": feature_desc})
            response = self._parse_result(result.content)

            print(f"[{self.agent_type}] ✅ 分析完成: {response['primary_style']}")
            return response

        except Exception as e:
            print(f"[{self.agent_type}] ❌ 分析失败: {e}")
            return {
                "primary_style": "Unknown",
                "confidence": 0.0,
                "error": str(e)
            }

    def _format_features(self, features: Dict[str, float]) -> str:
        """格式化特征向量为可读文本"""
        lines = ["学习特征分析："]
        for key, value in features.items():
            lines.append(f"- {key}: {value:.3f}")
        return "\n".join(lines)

    def _parse_result(self, result: str) -> Dict[str, Any]:
        """解析LLM输出为结构化数据"""
        import json
        import re

        # 尝试提取JSON
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # 备用解析
        return {
            "primary_style": "Mixed",
            "confidence": 0.5,
            "reasoning": result
        }

    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """
        处理来自网关的请求
        这是智能体的标准接口
        """
        if request.agent_type != "AG2_Style":
            return AgentResponse(
                request_id=request.request_id,
                agent_type="AG2_Style",
                success=False,
                error="Invalid agent type"
            )

        if request.task_type != "diagnose":
            return AgentResponse(
                request_id=request.request_id,
                agent_type="AG2_Style",
                success=False,
                error="Unsupported task type"
            )

        # 提取受保护的特征
        protected_features = request.data.get("protected_features", {})

        # 执行分析
        result = self.analyze(
            protected_features=protected_features,
            context=request.context
        )

        return AgentResponse(
            request_id=request.request_id,
            agent_type="AG2_Style",
            success=True,
            result={
                "learning_style": result["primary_style"],
                "confidence": result["confidence"],
                "reasoning": result.get("reasoning", "")
            },
            metadata={"model": "gpt-4o-mini"}
        )


# 单例模式
_ag2_instance: LearningStyleAgent = None


def get_ag2_agent() -> LearningStyleAgent:
    """获取AG2智能体单例"""
    global _ag2_instance
    if _ag2_instance is None:
        _ag2_instance = LearningStyleAgent()
    return _ag2_instance


# ============================================================
# 使用示例
# ============================================================
def demo_ag2():
    """演示AG2功能"""
    agent = get_ag2_agent()

    # 模拟受保护的特征（实际来自网关）
    mock_features = {
        "latent_0": 0.75,  # 可能对应视觉倾向
        "latent_1": 0.45,  # 可能对应听觉倾向
        "latent_2": 0.68,
        "latent_3": 0.52,
        "latent_4": 0.80,  # 可能对应读写倾向
    }

    print("\n" + "="*60)
    print("AG2 学习风格识别演示")
    print("="*60)

    result = agent.analyze(mock_features)

    print("\n分析结果：")
    print(f"- 主要风格: {result['primary_style']}")
    print(f"- 置信度: {result['confidence']:.2%}")
    print(f"- 分析理由: {result.get('reasoning', 'N/A')}")


if __name__ == "__main__":
    demo_ag2()
