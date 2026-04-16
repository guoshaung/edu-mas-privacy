"""
AG3 自适应辅导智能体

当前版本采用新的双流消费关系：
1. AG3 以差分隐私后的逻辑流作为主状态输入。
2. 辅助隐私流只用于个性化调节，不再主导语义理解。
3. AG3 与 AG5 在逻辑隐空间中进行轻量博弈，再由 LLM 解码为辅导文本。
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
    - 128 维差分隐私逻辑流

    输出：
    - 32 维辅导策略隐向量
    """

    def __init__(self, input_dim: int = 128, hidden_dim: int = 128, output_dim: int = 32):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim),
            nn.Tanh(),
        )

    def forward(self, student_logic_state: torch.Tensor) -> torch.Tensor:
        if student_logic_state.dim() == 1:
            student_logic_state = student_logic_state.unsqueeze(0)
        return self.net(student_logic_state)


def _prepare_logic_state(student_logic_state: List[float] | torch.Tensor) -> torch.Tensor:
    if not isinstance(student_logic_state, torch.Tensor):
        logic_state = torch.tensor(student_logic_state, dtype=torch.float32)
    else:
        logic_state = student_logic_state.float()

    if logic_state.dim() > 1:
        logic_state = logic_state.reshape(-1)
    logic_state = logic_state[:128]
    if logic_state.numel() < 128:
        logic_state = torch.nn.functional.pad(logic_state, (0, 128 - logic_state.numel()))
    return logic_state


def summarize_privacy_profile(privacy_profile_state: Optional[List[float]]) -> Dict[str, float]:
    if not privacy_profile_state:
        return {
            "support_intensity": 0.5,
            "stability_hint": 0.5,
            "pace_hint": 0.5,
        }

    vector = torch.tensor(privacy_profile_state, dtype=torch.float32)
    if vector.numel() == 0:
        return {
            "support_intensity": 0.5,
            "stability_hint": 0.5,
            "pace_hint": 0.5,
        }

    mean_abs = float(vector.abs().mean().item())
    variance = float(vector.var(unbiased=False).item()) if vector.numel() > 1 else 0.0
    max_abs = float(vector.abs().max().item())

    return {
        "support_intensity": round(min(1.0, mean_abs / 2.5), 3),
        "stability_hint": round(max(0.0, 1.0 - min(1.0, variance / 3.0)), 3),
        "pace_hint": round(min(1.0, max_abs / 4.0), 3),
    }


def simulate_latent_game(student_logic_state: List[float] | torch.Tensor) -> List[float]:
    """
    运行一个轻量的隐空间对抗循环：
    - AG3 试图最大化通过概率
    - AG5 试图最小化通过概率
    - 主状态由差分隐私后的逻辑流提供
    """
    logic_state = _prepare_logic_state(student_logic_state)

    ag3_policy = AG3PolicyNet()
    ag5_value = AG5ValueNet()

    ag3_optimizer = torch.optim.Adam(ag3_policy.parameters(), lr=1e-2)
    ag5_optimizer = torch.optim.Adam(ag5_value.parameters(), lr=1e-2)

    for _ in range(8):
        ag5_optimizer.zero_grad()
        strategy = ag3_policy(logic_state).detach()
        pass_prob = ag5_value(logic_state, strategy)
        ag5_loss = pass_prob.mean()
        ag5_loss.backward()
        ag5_optimizer.step()

        ag3_optimizer.zero_grad()
        strategy = ag3_policy(logic_state)
        pass_prob = ag5_value(logic_state, strategy)
        ag3_loss = -pass_prob.mean()
        ag3_loss.backward()
        ag3_optimizer.step()

    with torch.no_grad():
        final_strategy = ag3_policy(logic_state).squeeze(0).cpu().numpy().astype("float32")
    return final_strategy.tolist()


class AdaptiveTutorAgent:
    """
    AG3 自适应辅导智能体

    主流程：
    1. 读取差分隐私逻辑流
    2. 在逻辑隐空间里与 AG5 做轻量博弈
    3. 用辅助隐私流微调讲解风格
    4. 把策略向量交给 LLM 解码成文本
    """

    def __init__(self, llm: Optional[BaseChatModel] = None):
        self.llm = llm or self._build_optional_llm()
        self.agent_type = "AG3_AdaptiveTutor"
        self.policy_net = AG3PolicyNet()
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "你是 AG3 自适应辅导智能体。下面的 32 维策略向量代表当前最优的辅导倾向。"
                    "请把它解码成自然语言辅导方案，并结合辅助画像提示控制讲解节奏与支持强度。"
                    "输出 JSON，包含 explanation、guidance_steps、encouragement。",
                ),
                (
                    "system",
                    "策略向量：{policy_vector}\n"
                    "当前学生问题：{student_input}\n"
                    "逻辑主题：{logic_topic}\n"
                    "辅助画像提示：{privacy_hints}",
                ),
                ("human", "请给出本轮辅导回应。"),
            ]
        )

    def generate_scaffolding(
        self,
        student_input: str,
        noisy_logic_state: List[float],
        logic_topic: str = "当前知识点",
        privacy_profile_state: Optional[List[float]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        print(f"[{self.agent_type}] 接收到学生消息，开始基于主逻辑流执行 Latent MARL 策略博弈")
        best_strategy_vector = simulate_latent_game(noisy_logic_state)
        privacy_hints = summarize_privacy_profile(privacy_profile_state)

        try:
            if self.llm is None:
                raise RuntimeError("No available LLM client for AG3 decoding.")
            chain = self.prompt | self.llm
            result = chain.invoke(
                {
                    "policy_vector": best_strategy_vector,
                    "student_input": student_input,
                    "logic_topic": logic_topic,
                    "privacy_hints": privacy_hints,
                }
            )
            parsed = self._parse_json_like(result.content)
            parsed["latent_strategy_vector"] = best_strategy_vector
            parsed["logic_topic"] = logic_topic
            parsed["privacy_hints"] = privacy_hints
            return parsed
        except Exception as error:
            support_text = "更细致地分步讲解" if privacy_hints["support_intensity"] >= 0.5 else "保持标准讲解强度"
            return {
                "explanation": "已基于差分隐私逻辑流生成辅导策略，文本解码阶段回退为模板输出。",
                "guidance_steps": [
                    "先围绕当前逻辑主题解释核心结论与推导骨架。",
                    f"再结合辅助画像提示，{support_text}，逐步确认学生是否跟上。",
                    "最后安排一道低门槛练习题做即时巩固。",
                ],
                "encouragement": "我们先把逻辑骨架立住，再回头处理细节，难点会清楚很多。",
                "latent_strategy_vector": best_strategy_vector,
                "logic_topic": logic_topic,
                "privacy_hints": privacy_hints,
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

        noisy_logic_state = request.data.get("noisy_logic_vector") or request.data.get("student_logic_state") or []
        privacy_profile_state = request.data.get("privacy_profile_vector") or []
        student_input = request.data.get("student_input", "")
        logic_topic = request.data.get("logic_topic", "当前知识点")

        result = self.generate_scaffolding(
            student_input=student_input,
            noisy_logic_state=noisy_logic_state,
            logic_topic=logic_topic,
            privacy_profile_state=privacy_profile_state,
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
