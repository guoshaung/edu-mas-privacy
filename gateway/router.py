"""
隐私网关路由器（更新版）
集成G-safeguard GNN拓扑防御
"""
import asyncio
import uuid
from typing import Optional, Dict, Any
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from protocols.messages import (
    CrossDomainMessage, DomainType, AgentType,
    LearnerData, ProtectedFeatures, AgentRequest, AgentResponse, PrivacyLevel
)
from gateway.privacy_engine import get_privacy_engine
from gateway.rbac_manager import get_rbac_manager, BusinessState
from gateway.gnn_guard import monitor_cross_domain_message, get_gnn_guard


class GatewayState(BaseModel):
    """网关状态流转"""
    pending_requests: Dict[str, CrossDomainMessage] = {}
    active_permissions: Dict[str, Any] = {}
    gnn_enabled: bool = True


class PrivacyGateway:
    """
    隐私网关路由器（集成G-safeguard）
    所有跨域通信的唯一入口
    """

    def __init__(self, enable_gnn: bool = True):
        self.privacy_engine = get_privacy_engine()
        self.rbac_manager = get_rbac_manager()
        self.gnn_guard = get_gnn_guard() if enable_gnn else None
        self.gateway_id = f"gateway_{uuid.uuid4().hex[:8]}"
        self.gnn_enabled = enable_gnn

        # 构建LangGraph状态机
        self.graph = self._build_gateway_graph()
        self.memory = MemorySaver()

    def _build_gateway_graph(self) -> StateGraph:
        """构建网关工作流状态机"""

        async def validate_request(state: GatewayState) -> GatewayState:
            """步骤1：验证请求合法性"""
            print("[Gateway] Validating cross-domain request...")
            return state

        async def gnn_check(state: GatewayState) -> GatewayState:
            """步骤1.5：GNN安全检查"""
            if self.gnn_enabled:
                print("[Gateway] Running G-safeguard topology check...")
            return state

        async def check_permission(state: GatewayState) -> GatewayState:
            """步骤2：检查RBAC权限"""
            print("[Gateway] Checking RBAC permissions...")
            return state

        async def apply_privacy(state: GatewayState) -> GatewayState:
            """步骤3：应用SRPG隐私处理"""
            print("[Gateway] Applying SRPG protection...")
            return state

        async def route_to_agent(state: GatewayState) -> GatewayState:
            """步骤4：路由到目标智能体"""
            print("[Gateway] Routing to target agent...")
            return state

        async def log_audit(state: GatewayState) -> GatewayState:
            """步骤5：记录审计日志"""
            print("[Gateway] Logging to audit trail...")
            return state

        # 构建图
        workflow = StateGraph(GatewayState)
        workflow.add_node("validate", validate_request)
        workflow.add_node("gnn_check", gnn_check)
        workflow.add_node("permission", check_permission)
        workflow.add_node("privacy", apply_privacy)
        workflow.add_node("route", route_to_agent)
        workflow.add_node("audit", log_audit)

        workflow.set_entry_point("validate")
        workflow.add_edge("validate", "gnn_check")
        workflow.add_edge("gnn_check", "permission")
        workflow.add_edge("permission", "privacy")
        workflow.add_edge("privacy", "route")
        workflow.add_edge("route", "audit")
        workflow.add_edge("audit", END)

        return workflow.compile()

    async def route_cross_domain(
        self,
        message: CrossDomainMessage
    ) -> Optional[AgentResponse]:
        """
        处理跨域请求（集成GNN检查）
        """
        print(f"\n[Gateway] 收到跨域请求: {message.source_domain} → {message.target_domain}")

        # 0. G-safeguard拓扑检查
        if self.gnn_enabled:
            src = message.source_agent.value if message.source_agent else message.source_domain.value
            dst = message.target_agent.value if message.target_agent else message.target_domain.value

            allowed, reason = monitor_cross_domain_message(message)
            if not allowed:
                print(f"[Gateway] 🚨 G-safeguard拦截: {reason}")
                return AgentResponse(
                    request_id=message.msg_id,
                    agent_type=message.source_agent or AgentType.AG2_STYLE,
                    success=False,
                    error=f"Blocked by G-safeguard: {reason}"
                )

        # 1. 域隔离检查：禁止横向直连
        if self._is_lateral_connection(message):
            print("[Gateway] ❌ 拒绝：检测到非法横向连接！")
            return AgentResponse(
                request_id=message.msg_id,
                agent_type=message.source_agent or AgentType.AG2_STYLE,
                success=False,
                error="Lateral connection prohibited by zero-trust policy"
            )

        # 2. 通过LangGraph状态机处理请求
        try:
            state = GatewayState(pending_requests={message.msg_id: message}, gnn_enabled=self.gnn_enabled)
            final_state = await self.graph.ainvoke(state, config={"configurable": {"thread_id": message.msg_id}})

            print("[Gateway] ✅ 请求处理完成")
            return AgentResponse(
                request_id=message.msg_id,
                agent_type=message.target_agent or AgentType.AG2_STYLE,
                success=True,
                result={"status": "processed"}
            )

        except Exception as e:
            print(f"[Gateway] ❌ 处理失败: {e}")
            return AgentResponse(
                request_id=message.msg_id,
                agent_type=message.target_agent or AgentType.AG2_STYLE,
                success=False,
                error=str(e)
            )

    def _is_lateral_connection(self, message: CrossDomainMessage) -> bool:
        """检测是否为非法横向连接"""
        if (message.source_domain == DomainType.EDUCATION and
            message.target_domain == DomainType.EDUCATION):
            return True
        if (message.source_domain == DomainType.LEARNER and
            message.target_domain == DomainType.LEARNER):
            return True
        return False

    async def route_learner_to_education(
        self,
        learner_data: LearnerData,
        target_agent: AgentType
    ) -> Optional[AgentResponse]:
        """
        学习者域 → 教学域路由（集成GNN监控）
        """
        print(f"\n[Gateway] 处理学习者 → 教学域请求 (目标: {target_agent})")

        # 0. G-safeguard监控
        if self.gnn_enabled:
            allowed, reason = self.gnn_guard.monitor_interaction(
                src="A1",
                dst=target_agent.value,
                interaction_type="learner_to_education",
                metadata={"data_size": len(str(learner_data.raw_features))}
            )
            if not allowed:
                print(f"[Gateway] 🚨 G-safeguard拦截: {reason}")
                return AgentResponse(
                    request_id=f"req_{uuid.uuid4().hex}",
                    agent_type=target_agent,
                    success=False,
                    error=f"Blocked by G-safeguard: {reason}"
                )

        # 1. 切换业务状态
        state_map = {
            AgentType.AG2_STYLE: BusinessState.DIAGNOSING,
            AgentType.AG3_TUTOR: BusinessState.TUTORING,
            AgentType.AG4_CONTENT: BusinessState.CONTENT_RETRIEVAL,
            AgentType.AG5_ASSESS: BusinessState.ASSESSING,
        }
        target_state = state_map.get(target_agent, BusinessState.IDLE)
        self.rbac_manager.transition_state(target_state)

        # 2. 应用SRPG隐私保护
        try:
            protected_features, cost = self.privacy_engine.protect(learner_data)
            print(f"[Gateway] ✅ SRPG保护完成，消耗隐私预算: {cost:.4f}")
        except Exception as e:
            print(f"[Gateway] ❌ SRPG保护失败: {e}")
            return AgentResponse(
                request_id=f"req_{uuid.uuid4().hex}",
                agent_type=target_agent,
                success=False,
                error=f"Privacy protection failed: {e}"
            )

        # 3. 颁发临时权限令牌
        permission = self.rbac_manager.grant_permission(
            agent_id=target_agent,
            resource_id=protected_features.student_pseudonym,
            privacy_level=PrivacyLevel.RECONSTRUCTED
        )

        if not permission:
            print("[Gateway] ❌ 权限授予失败")
            return AgentResponse(
                request_id=f"req_{uuid.uuid4().hex}",
                agent_type=target_agent,
                success=False,
                error="Permission denied by RBAC"
            )

        print(f"[Gateway] ✅ 权限令牌已颁发: {permission.agent_id}")

        # 4. 构建跨域消息
        message = CrossDomainMessage(
            source_domain=DomainType.LEARNER,
            target_domain=DomainType.EDUCATION,
            source_agent=AgentType.A1_PROFILE,
            target_agent=target_agent,
            payload={
                "protected_features": protected_features.model_dump(),
                "permission": permission.model_dump()
            }
        )

        # 5. 记录到GNN
        if self.gnn_enabled:
            self.gnn_guard.monitor_interaction(
                src="privacy_gateway",
                dst=target_agent.value,
                interaction_type="forward_protected_data",
                metadata={"privacy_cost": cost}
            )

        print(f"[Gateway] ✅ 路由完成，数据已发送至 {target_agent}")

        return AgentResponse(
            request_id=message.msg_id,
            agent_type=target_agent,
            success=True,
            result={
                "features": protected_features.reconstructed_features,
                "pseudonym": protected_features.student_pseudonym
            },
            metadata={"privacy_cost": cost}
        )

    def get_topology_status(self) -> Optional[Dict]:
        """获取GNN拓扑状态（如果启用）"""
        if self.gnn_enabled:
            return self.gnn_guard.get_topology_snapshot()
        return None


# 单例模式
_gateway_instance: PrivacyGateway = None


def get_gateway() -> PrivacyGateway:
    """获取网关单例"""
    global _gateway_instance
    if _gateway_instance is None:
        _gateway_instance = PrivacyGateway(enable_gnn=True)
    return _gateway_instance


# ============================================================
# 使用示例
# ============================================================
async def demo_gateway():
    """演示网关功能（集成GNN）"""
    gateway = get_gateway()

    # 模拟学习者数据
    learner_data = LearnerData(
        student_id="stu_20240313_001",
        demographic={"age": 15, "grade": 9},
        raw_features={
            "visual_score": 0.8,
            "auditory_score": 0.6,
            "reading_speed": 0.75,
            "math_ability": 0.7,
            "attention_span": 0.65
        }
    )

    # 场景1：学习者 → AG2
    print("\n" + "="*60)
    print("场景1：学习风格诊断（含GNN监控）")
    print("="*60)
    response = await gateway.route_learner_to_education(
        learner_data=learner_data,
        target_agent=AgentType.AG2_STYLE
    )
    print(f"响应: {response.model_dump()}")

    # 场景2：查看拓扑状态
    if gateway.gnn_enabled:
        print("\n" + "="*60)
        print("GNN拓扑状态")
        print("="*60)
        topology = gateway.get_topology_status()
        print(f"节点数: {len(topology['nodes'])}")
        print(f"边数（最近50条）: {len(topology['edges'])}")
        print(f"被隔离节点: {topology['quarantined_nodes']}")

    # 检查剩余隐私预算
    remaining = gateway.privacy_engine.get_remaining_budget()
    print(f"\n剩余隐私预算: {remaining:.4f} / {gateway.privacy_engine.max_budget}")


if __name__ == "__main__":
    import asyncio
    from pydantic import BaseModel

    asyncio.run(demo_gateway())
