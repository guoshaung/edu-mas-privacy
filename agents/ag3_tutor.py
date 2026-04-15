"""
AG3 自适应辅导智能体

重构目标：
1. 引入 64 维加噪隐私态到 32 维策略向量的策略网络。
2. 通过轻量级 Latent MARL 模拟 AG3 和 AG5 的对抗博弈。
3. 让 AG3 最终把策略向量作为 system prompt 的控制变量，再交给 LLM 解码为文本。
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import torch
import torch.nn as nn
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from agents.ag5_assess import AG5ValueNet
from protocols.messages import AgentRequest, AgentResponse


class AG3PolicyNet(nn.Module):
    """
    AG3 策略网络

    输入：
    - 64 维学生加噪隐私流向量

    输出：
    - 32 维辅导策略隐向量
    """

    def __init__(self, input_dim: int = 64, hidden_dim: int = 96, output_dim: int = 32):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim),
            nn.Tanh(),
        )

    def forward(self, student_noisy_state: torch.Tensor) -> torch.Tensor:
        if student_noisy_state.dim() == 1:
            student_noisy_state = student_noisy_state.unsqueeze(0)
        return self.net(student_noisy_state)


def simulate_latent_game(student_noisy_state: List[float] | torch.Tensor) -> List[float]:
    """
    运行一个很轻量的对抗训练循环，模拟 Latent MARL。

    - AG3 试图最大化“通过测试概率”
    - AG5 试图最小化“通过测试概率”
    - 最终返回 AG3 学到的 32 维最优策略向量
    """
    if not isinstance(student_noisy_state, torch.Tensor):
        student_state = torch.tensor(student_noisy_state, dtype=torch.float32)
    else:
        student_state = student_noisy_state.float()

    if student_state.dim() > 1:
        student_state = student_state.reshape(-1)
    student_state = student_state[:64]
    if student_state.numel() < 64:
        student_state = torch.nn.functional.pad(student_state, (0, 64 - student_state.numel()))

    ag3_policy = AG3PolicyNet()
    ag5_value = AG5ValueNet()

    ag3_optimizer = torch.optim.Adam(ag3_policy.parameters(), lr=1e-2)
    ag5_optimizer = torch.optim.Adam(ag5_value.parameters(), lr=1e-2)

    for _ in range(8):
        # AG5 先作为“严格考官”更新，目标是压低通过概率
        ag5_optimizer.zero_grad()
        strategy = ag3_policy(student_state).detach()
        pass_prob = ag5_value(student_state, strategy)
        ag5_loss = pass_prob.mean()
        ag5_loss.backward()
        ag5_optimizer.step()

        # AG3 再作为“努力导师”更新，目标是提升通过概率
        ag3_optimizer.zero_grad()
        strategy = ag3_policy(student_state)
        pass_prob = ag5_value(student_state, strategy)
        ag3_loss = -pass_prob.mean()
        ag3_loss.backward()
        ag3_optimizer.step()

    with torch.no_grad():
        final_strategy = ag3_policy(student_state).squeeze(0).cpu().numpy().astype("float32")
    return final_strategy.tolist()


class AdaptiveTutorAgent:
    """
    AG3 自适应辅导智能体

    当前主流程：
    1. 接收学生加噪隐私态（64 维）
    2. 跑 Latent MARL 小型博弈
    3. 输出 32 维最优策略向量
    4. 将策略向量作为 system prompt 的控制变量，让 LLM 解码成文本辅导建议
    """

    def __init__(self, llm: Optional[BaseChatModel] = None):
        self.llm = llm or self._build_optional_llm()
        self.agent_type = "AG3_AdaptiveTutor"
        self.policy_net = AG3PolicyNet()
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "你是 AG3 自适应辅导智能体。下面的 32 维策略向量代表当前最优的辅导倾向，"
                    "请把它解码成自然语言辅导方案。输出 JSON，包含 explanation、guidance_steps、encouragement。",
                ),
                (
                    "system",
                    "策略向量：{policy_vector}\n当前学生问题：{student_input}\n逻辑主题：{logic_topic}",
                ),
                ("human", "请给出本轮辅导回应。"),
            ]
        )

    def generate_scaffolding(
        self,
        student_input: str,
        noisy_privacy_state: List[float],
        logic_topic: str = "当前知识点",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        AG3 主流程：
        - 先跑 latent game 拿到最优策略向量
        - 再让 LLM 把策略向量解释成文本
        """
        print(f"[{self.agent_type}] 接收到学生消息，开始 Latent MARL 策略博弈")
        best_strategy_vector = simulate_latent_game(noisy_privacy_state)

        try:
            if self.llm is None:
                raise RuntimeError("No available LLM client for AG3 decoding.")
            chain = self.prompt | self.llm
            result = chain.invoke(
                {
                    "policy_vector": best_strategy_vector,
                    "student_input": student_input,
                    "logic_topic": logic_topic,
                }
            )
            parsed = self._parse_json_like(result.content)
            parsed["latent_strategy_vector"] = best_strategy_vector
            parsed["logic_topic"] = logic_topic
            return parsed
        except Exception as error:
            return {
                "explanation": "已根据隐空间博弈生成辅导策略，但文本解码阶段回退为模板输出。",
                "guidance_steps": [
                    "先用直观例子解释当前知识点的核心结论。",
                    "再拆分证明链条，逐步确认学生是否跟上。",
                    "最后提供一道低门槛练习题做即时巩固。",
                ],
                "encouragement": "先把逻辑骨架搭起来，再去啃细节，会轻松很多。",
                "latent_strategy_vector": best_strategy_vector,
                "logic_topic": logic_topic,
                "fallback_reason": str(error),
            }

    async def process_request(self, request: AgentRequest) -> AgentResponse:
        if request.task_type not in {"tutor", "latent_tutor"}:
            return AgentResponse(
                request_id=request.request_id,
                agent_type=request.agent_type,
                success=False,
                error="Unsupported task type for AG3",
            )

        noisy_state = request.data.get("noisy_privacy_vector") or request.data.get("student_noisy_state") or []
        student_input = request.data.get("student_input", "")
        logic_topic = request.data.get("logic_topic", "当前知识点")

        result = self.generate_scaffolding(
            student_input=student_input,
            noisy_privacy_state=noisy_state,
            logic_topic=logic_topic,
            context=request.context,
        )

        return AgentResponse(
            request_id=request.request_id,
            agent_type=request.agent_type,
            success=True,
            result=result,
        )

    def _parse_json_like(self, text: str) -> Dict[str, Any]:
        import json
        import re

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {
            "explanation": text,
            "guidance_steps": [],
            "encouragement": "继续往下走，我们把复杂问题拆成小块来解决。",
        }

    def _build_optional_llm(self) -> Optional[BaseChatModel]:
        deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        if deepseek_key:
            return ChatOpenAI(
                api_key=deepseek_key,
                base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
                model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
                temperature=0.45,
            )

        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            return ChatOpenAI(api_key=openai_key, model="gpt-4o", temperature=0.55)

        return None


_ag3_instance: Optional[AdaptiveTutorAgent] = None


def get_ag3_agent() -> AdaptiveTutorAgent:
    global _ag3_instance
    if _ag3_instance is None:
        _ag3_instance = AdaptiveTutorAgent()
    return _ag3_instance
