"""
动态密码学授权（DCAC）网关路由

本模块用于替代传统“按字段名做文本权限判断”的做法，改成：
1. 接收双流数据（noisy_privacy_vector / encrypted_logic_vector）
2. 按 agent_id 与 risk_score 分配隐私预算 epsilon
3. 对 AG5 只下发密文逻辑流和临时授权 token
4. 输出清晰的控制台日志，便于演示零信任 / 密文计算流程
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, Optional, Tuple

from pydantic import BaseModel, Field

from gateway.privacy_engine import get_privacy_engine
from protocols.messages import (
    AgentRequest,
    AgentResponse,
    AgentType,
    CrossDomainMessage,
    DomainType,
)


class GatewayState(BaseModel):
    pending_request_id: Optional[str] = None
    route_result: Dict[str, Any] = Field(default_factory=dict)


def calculate_privacy_budget(agent_id: str, risk_score: float) -> float:
    """
    根据风险分数动态分配隐私预算。

    - 风险高：epsilon=0.1，代表更强噪声
    - 风险低：epsilon=2.0，代表较弱噪声
    """
    if risk_score >= 0.8:
        return 0.1
    if risk_score <= 0.3:
        return 2.0
    # 中间区间线性插值，保证 Demo 更平滑
    return round(2.0 - ((risk_score - 0.3) / 0.5) * 1.9, 4)


class PrivacyGateway:
    """
    升级后的零信任 / DCAC 网关。
    """

    def __init__(self):
        self.privacy_engine = get_privacy_engine()
        self.gateway_id = f"dcac_gateway_{uuid.uuid4().hex[:8]}"

    def _issue_temporary_token(self, agent_id: str, permission: str) -> Dict[str, Any]:
        token = {
            "token_id": f"tok_{uuid.uuid4().hex[:10]}",
            "agent_id": agent_id,
            "permission": permission,
            "issued_at": time.time(),
            "expires_in": 300,
        }
        print(f"[DCAC Router] 已签发临时授权 Token -> {agent_id} / permission={permission}")
        return token

    def _build_dual_stream_payload(self, text_input: str, epsilon: float) -> Dict[str, Any]:
        vectors = self.privacy_engine.process_dual_stream_vector(text_input=text_input, epsilon=epsilon)
        return {
            "noisy_privacy_vector": vectors["noisy_privacy_vector"],
            "logic_graph_vector": vectors["logic_graph_vector"],
        }

    async def route_dual_stream_request(
        self,
        agent_id: str,
        text_input: str,
        risk_score: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        新的双流入口：
        - 输入是文本和风险分数
        - 输出是不同 Agent 可见的安全载荷
        """
        epsilon = calculate_privacy_budget(agent_id, risk_score)
        print(f"[DCAC Router] agent={agent_id} risk_score={risk_score:.4f} -> epsilon={epsilon}")

        dual_stream = self._build_dual_stream_payload(text_input=text_input, epsilon=epsilon)
        noisy_privacy_vector = dual_stream["noisy_privacy_vector"]
        logic_graph_vector = dual_stream["logic_graph_vector"]
        # 用文本长度粗略映射会话持续度，作为 D_t 的一个 Demo 入口
        duration_ratio = min(1.0, max(0.05, len(text_input) / 500.0))
        privacy_trust = self.privacy_engine.get_privacy_trust_snapshot(
            duration_ratio=duration_ratio,
            gnn_risk_score=risk_score,
        )

        if agent_id == AgentType.AG5_ASSESS.value:
            encrypted_logic_vector = {
                "ciphertext": logic_graph_vector,
                "cipher_mode": "mock_homomorphic_cipher",
            }
            temp_token = self._issue_temporary_token(agent_id=agent_id, permission="homomorphic_compute")
            print("[DCAC Router] 检测到 AG5 请求，已阻断明文访问，仅下发密文计算授权与加密向量流")
            return {
                "agent_id": agent_id,
                "epsilon": epsilon,
                "privacy_trust": privacy_trust,
                "temporary_token": temp_token,
                "encrypted_logic_vector": encrypted_logic_vector,
            }

        print(f"[DCAC Router] 已为 {agent_id} 下发加噪隐私流和逻辑图谱流")
        return {
            "agent_id": agent_id,
            "epsilon": epsilon,
            "privacy_trust": privacy_trust,
            "noisy_privacy_vector": noisy_privacy_vector,
            "logic_graph_vector": logic_graph_vector,
        }

    async def route_cross_domain(self, message: CrossDomainMessage) -> Optional[AgentResponse]:
        """
        兼容旧接口：
        - 如果 message.payload 里有双流数据，走新的 DCAC 分发
        - 否则维持一个最小兼容响应
        """
        target = message.target_agent.value if message.target_agent else "unknown_agent"
        risk_score = float(message.payload.get("risk_score", 0.5))

        if "text_input" in message.payload:
            dcac_payload = await self.route_dual_stream_request(
                agent_id=target,
                text_input=message.payload["text_input"],
                risk_score=risk_score,
                context=message.payload,
            )
            return AgentResponse(
                request_id=message.msg_id,
                agent_type=message.target_agent or AgentType.AG2_STYLE,
                success=True,
                result=dcac_payload,
            )

        if "noisy_privacy_vector" in message.payload or "encrypted_logic_vector" in message.payload:
            print("[DCAC Router] 收到已处理的双流载荷，执行最小兼容转发")
            return AgentResponse(
                request_id=message.msg_id,
                agent_type=message.target_agent or AgentType.AG2_STYLE,
                success=True,
                result=message.payload,
            )

        return AgentResponse(
            request_id=message.msg_id,
            agent_type=message.target_agent or AgentType.AG2_STYLE,
            success=False,
            error="Message payload does not contain supported DCAC fields",
        )

    async def route_learner_to_education(self, learner_data, target_agent: AgentType) -> Optional[AgentResponse]:
        """
        兼容旧入口：
        - 从 learner_data 中提取文本
        - 自动构建双流载荷并路由
        """
        text_input = learner_data.demographic.get("text_input") if getattr(learner_data, "demographic", None) else None
        if not text_input:
            text_input = f"student={learner_data.student_id}, features={learner_data.raw_features}"

        result = await self.route_dual_stream_request(
            agent_id=target_agent.value,
            text_input=text_input,
            risk_score=0.5,
        )

        return AgentResponse(
            request_id=f"req_{uuid.uuid4().hex[:10]}",
            agent_type=target_agent,
            success=True,
            result=result,
        )


_gateway_instance: Optional[PrivacyGateway] = None


def get_gateway() -> PrivacyGateway:
    global _gateway_instance
    if _gateway_instance is None:
        _gateway_instance = PrivacyGateway()
    return _gateway_instance
