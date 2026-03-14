"""
AG4: 内容挖掘智能体
职责：从全局题库RAG检索学习资源（无个体隐私访问权限）
输入：知识点列表 + 难度等级
输出：个性化学习资源（视频、习题、文本）
"""
from typing import Dict, Any, Optional, List
import numpy as np
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

from protocols.messages import AgentRequest, AgentResponse


# 模拟全局题库（生产环境应从数据库加载）
GLOBAL_RESOURCE_POOL = {
    "math": {
        "secondary_function": {
            "basic": [
                {
                    "type": "video",
                    "title": "二次函数基础概念",
                    "url": "https://example.com/math/quadratic_basic.mp4",
                    "duration": 300,
                    "tags": ["visual", "step_by_step"],
                    "difficulty": 0.3
                },
                {
                    "type": "exercise",
                    "title": "二次函数顶点坐标练习",
                    "questions": 10,
                    "estimated_time": 600,
                    "tags": ["practice", "calculation"],
                    "difficulty": 0.4
                }
            ],
            "intermediate": [
                {
                    "type": "text",
                    "title": "二次函数图像变换详解",
                    "content": "详细讲解平移、缩放、旋转对图像的影响...",
                    "reading_time": 400,
                    "tags": ["reading", "conceptual"],
                    "difficulty": 0.6
                },
                {
                    "type": "interactive",
                    "title": "二次函数图像交互实验",
                    "url": "https://example.com/math/quadratic_interactive.html",
                    "features": ["drag_points", "real_time_graph"],
                    "tags": ["kinesthetic", "visual"],
                    "difficulty": 0.65
                }
            ],
            "advanced": [
                {
                    "type": "video",
                    "title": "二次函数最值问题深度解析",
                    "url": "https://example.com/math/quadratic_max.mp4",
                    "duration": 450,
                    "tags": ["auditory", "problem_solving"],
                    "difficulty": 0.8
                },
                {
                    "type": "exercise",
                    "title": "二次函数综合应用题",
                    "questions": 5,
                    "estimated_time": 900,
                    "tags": ["challenge", "real_world"],
                    "difficulty": 0.9
                }
            ]
        },
        "trigonometric_function": {
            "basic": [
                {
                    "type": "video",
                    "title": "三角函数入门",
                    "url": "https://example.com/math/trig_basic.mp4",
                    "duration": 360,
                    "tags": ["visual", "intuitive"],
                    "difficulty": 0.35
                }
            ]
        }
    },
    "physics": {
        "mechanics": {
            "basic": [
                {
                    "type": "video",
                    "title": "牛顿第一定律实验",
                    "url": "https://example.com/physics/newton1.mp4",
                    "duration": 240,
                    "tags": ["visual", "experiment"],
                    "difficulty": 0.4
                }
            ]
        }
    }
}


class ContentMiningAgent:
    """
    AG4: 内容挖掘智能体
    功能：
    1. 接收AG3提供的知识点和难度
    2. 从全局题库RAG检索相关资源
    3. 根据学习风格过滤资源
    4. 返回个性化资源列表
    """

    def __init__(self, llm: Optional[BaseChatModel] = None):
        self.llm = llm or ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3
        )
        self.agent_type = "AG4_ContentMining"

        # 向量存储（用于语义检索）
        self.embeddings = OpenAIEmbeddings()
        self.vector_store = None  # 实际部署时初始化

        # 资源推荐提示词
        self.recommendation_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个学习资源推荐专家。基于以下信息，为学生选择最合适的资源：

输入信息：
- 知识点: {knowledge_points}
- 难度等级: {difficulty} (0-1)
- 学习风格: {learning_style}

资源库:
{resources}

推荐规则：
1. 难度匹配：资源难度应在学生当前水平±0.2范围内
2. 风格适配：
   - Visual：优先视频、交互式可视化
   - Aural：优先视频、音频讲解
   - Read/Write：优先文本、阅读材料
   - Kinesthetic：优先交互式、实践练习
3. 多样性：提供2-4种不同类型的资源
4. 渐进性：从易到难排序

输出格式：JSON
{{
  "recommended_resources": [
    {{
      "resource_id": "资源唯一标识",
      "type": "video/exercise/text/interactive",
      "title": "资源标题",
      "url": "链接",
      "estimated_time": 预计用时（秒）,
      "reason": "推荐理由（结合学习风格）",
      "difficulty": 难度值
    }}
  ],
  "study_sequence": "学习顺序建议（如：先看视频，再做练习）"
}}"""),
            ("user", "为学生推荐资源")
        ])

    def retrieve_resources(
        self,
        knowledge_points: List[str],
        difficulty: float,
        learning_style: str = "Mixed",
        subject: str = "math"
    ) -> Dict[str, Any]:
        """
        从全局题库检索资源
        注意：此函数无个体隐私访问，仅基于知识点和风格
        """
        print(f"[{self.agent_type}] 检索资源...")
        print(f"  - 知识点: {knowledge_points}")
        print(f"  - 难度: {difficulty:.2f}")
        print(f"  - 学习风格: {learning_style}")

        # 1. 从静态题库中匹配资源（简化版）
        candidates = self._match_resources_from_pool(
            knowledge_points, difficulty, subject
        )

        if not candidates:
            print(f"[{self.agent_type}] ⚠️ 未找到匹配资源")
            return {
                "recommended_resources": [],
                "study_sequence": "暂无推荐资源，建议调整学习目标"
            }

        # 2. 使用LLM进行智能推荐
        chain = self.recommendation_prompt | self.llm

        try:
            result = chain.invoke({
                "knowledge_points": ", ".join(knowledge_points),
                "difficulty": difficulty,
                "learning_style": learning_style,
                "resources": self._format_resources(candidates)
            })

            recommendation = self._parse_recommendation(result.content)

            print(f"[{self.agent_type}] ✅ 推荐完成: {len(recommendation['recommended_resources'])}个资源")
            return recommendation

        except Exception as e:
            print(f"[{self.agent_type}] ❌ 推荐失败: {e}")
            # 降级到规则推荐
            return self._fallback_recommendation(candidates, learning_style)

    def _match_resources_from_pool(
        self,
        knowledge_points: List[str],
        difficulty: float,
        subject: str
    ) -> List[Dict]:
        """从题库中匹配资源（简化版规则匹配）"""
        candidates = []

        for kc in knowledge_points:
            # 遍历题库（实际应使用向量检索）
            for subj_key, subj_data in GLOBAL_RESOURCE_POOL.items():
                if subj_key != subject:
                    continue

                for kc_key, kc_data in subj_data.items():
                    # 模糊匹配知识点
                    if kc.lower() in kc_key.lower() or kc_key.lower() in kc.lower():
                        # 根据难度获取对应层级的资源
                        difficulty_level = self._get_difficulty_level(difficulty)
                        resources = kc_data.get(difficulty_level, [])

                        # 过滤难度范围
                        for res in resources:
                            if abs(res["difficulty"] - difficulty) <= 0.2:
                                candidates.append({
                                    **res,
                                    "knowledge_point": kc
                                })

        return candidates

    def _get_difficulty_level(self, difficulty: float) -> str:
        """将连续难度值映射到离散等级"""
        if difficulty < 0.4:
            return "basic"
        elif difficulty < 0.7:
            return "intermediate"
        else:
            return "advanced"

    def _format_resources(self, resources: List[Dict]) -> str:
        """格式化资源列表为文本"""
        lines = []
        for i, res in enumerate(resources, 1):
            lines.append(f"{i}. {res['title']}")
            lines.append(f"   类型: {res['type']}")
            lines.append(f"   难度: {res['difficulty']}")
            lines.append(f"   标签: {', '.join(res['tags'])}")
        return "\n".join(lines)

    def _parse_recommendation(self, response: str) -> Dict[str, Any]:
        """解析LLM推荐结果"""
        import json
        import re

        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # 备用返回
        return {
            "recommended_resources": [],
            "study_sequence": "解析失败，请重试"
        }

    def _fallback_recommendation(
        self,
        candidates: List[Dict],
        learning_style: str
    ) -> Dict[str, Any]:
        """降级推荐（基于规则）"""
        # 根据学习风格排序
        style_priority = {
            "Visual": ["video", "interactive", "text", "exercise"],
            "Aural": ["video", "text", "exercise", "interactive"],
            "ReadWrite": ["text", "exercise", "video", "interactive"],
            "Kinesthetic": ["interactive", "exercise", "video", "text"]
        }

        priority = style_priority.get(learning_style, ["video", "exercise", "text"])

        # 排序候选资源
        sorted_candidates = sorted(
            candidates,
            key=lambda x: (
                priority.index(x["type"]) if x["type"] in priority else 99,
                x["difficulty"]
            )
        )

        # 取前4个
        top_resources = sorted_candidates[:4]

        return {
            "recommended_resources": [
                {
                    "resource_id": f"{res['type']}_{hash(res['title']) % 10000}",
                    "type": res["type"],
                    "title": res["title"],
                    "url": res.get("url", ""),
                    "estimated_time": res.get("duration", res.get("estimated_time", 300)),
                    "reason": f"适合{learning_style}学习风格",
                    "difficulty": res["difficulty"]
                }
                for res in top_resources
            ],
            "study_sequence": "建议按顺序学习：先理解概念，再做练习"
        }

    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """处理来自网关的资源检索请求"""
        if request.task_type != "retrieve":
            return AgentResponse(
                request_id=request.request_id,
                agent_type="AG4_Content",
                success=False,
                error="Unsupported task type"
            )

        # 提取参数
        knowledge_points = request.data.get("knowledge_points", [])
        difficulty = request.data.get("difficulty", 0.5)
        learning_style = request.data.get("learning_style", "Mixed")
        subject = request.data.get("subject", "math")

        if not knowledge_points:
            return AgentResponse(
                request_id=request.request_id,
                agent_type="AG4_Content",
                success=False,
                error="Missing knowledge points"
            )

        # 检索资源
        result = self.retrieve_resources(
            knowledge_points=knowledge_points,
            difficulty=difficulty,
            learning_style=learning_style,
            subject=subject
        )

        return AgentResponse(
            request_id=request.request_id,
            agent_type="AG4_Content",
            success=True,
            result=result,
            metadata={
                "knowledge_points": knowledge_points,
                "resource_count": len(result["recommended_resources"])
            }
        )


# 单例模式
_ag4_instance: ContentMiningAgent = None


def get_ag4_agent() -> ContentMiningAgent:
    """获取AG4智能体单例"""
    global _ag4_instance
    if _ag4_instance is None:
        _ag4_instance = ContentMiningAgent()
    return _ag4_instance


# ============================================================
# 使用示例
# ============================================================
def demo_ag4():
    """演示AG4功能"""
    agent = get_ag4_agent()

    # 模拟输入
    mock_kc = ["二次函数", "顶点坐标"]
    mock_difficulty = 0.65
    mock_style = "Visual"

    print("\n" + "="*60)
    print("AG4 内容挖掘演示")
    print("="*60)

    result = agent.retrieve_resources(
        knowledge_points=mock_kc,
        difficulty=mock_difficulty,
        learning_style=mock_style
    )

    print("\n推荐资源:")
    for i, res in enumerate(result["recommended_resources"], 1):
        print(f"\n{i}. {res['title']}")
        print(f"   类型: {res['type']}")
        print(f"   难度: {res['difficulty']}")
        print(f"   预计用时: {res['estimated_time']}秒")
        print(f"   推荐理由: {res['reason']}")

    print(f"\n学习顺序建议: {result['study_sequence']}")


if __name__ == "__main__":
    demo_ag4()
