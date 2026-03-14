"""
gRPC网关客户端
用于REST API服务器连接到后端gRPC服务
"""
import asyncio
import grpc
from typing import Optional, Dict, Any

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from protocols.gateway_pb2 import (
    CrossDomainRequest, CrossDomainResponse,
    LearnerDataRequest, AgentResponse as GrpcAgentResponse,
    HealthCheckRequest, HealthCheckResponse
)
from protocols.gateway_pb2_grpc import PrivacyGatewayStub
from protocols.messages import AgentRequest, AgentResponse, AgentType


class GatewayClient:
    """gRPC网关客户端"""

    def __init__(
        self,
        gateway_host: str = "localhost",
        gateway_port: int = 50051
    ):
        self.gateway_host = gateway_host
        self.gateway_port = gateway_port
        self.channel: Optional[grpc.aio.Channel] = None
        self.stub: Optional[PrivacyGatewayStub] = None

    async def connect(self):
        """连接到网关服务"""
        channel_str = f"{self.gateway_host}:{self.gateway_port}"
        self.channel = grpc.aio.insecure_channel(channel_str)
        self.stub = PrivacyGatewayStub(self.channel)

        # 测试连接
        try:
            await self.health_check()
            print(f"✅ 成功连接到网关服务: {channel_str}")
        except Exception as e:
            print(f"❌ 连接网关服务失败: {e}")
            raise

    async def close(self):
        """关闭连接"""
        if self.channel:
            await self.channel.close()

    async def health_check(self) -> bool:
        """健康检查"""
        if not self.stub:
            raise RuntimeError("客户端未连接")

        request = HealthCheckRequest()
        response: HealthCheckResponse = await self.stub.HealthCheck(request)
        return response.healthy

    async def route_cross_domain(
        self,
        source_domain: str,
        target_domain: str,
        payload: Dict[str, Any]
    ) -> CrossDomainResponse:
        """路由跨域请求"""
        if not self.stub:
            raise RuntimeError("客户端未连接")

        import time
        request = CrossDomainRequest(
            msg_id=f"msg_{int(time.time())}",
            source_domain=source_domain,
            target_domain=target_domain,
            payload=payload,
            timestamp=time.time()
        )

        response: CrossDomainResponse = await self.stub.RouteCrossDomain(request)
        return response

    async def route_to_education(
        self,
        request: AgentRequest
    ) -> AgentResponse:
        """路由请求到教学域智能体"""
        if not self.stub:
            raise RuntimeError("客户端未连接")

        # 构建gRPC请求
        grpc_request = LearnerDataRequest(
            student_id=request.data.get("student_pseudonym", "unknown"),
            demographic={},  # 人口统计信息已脱敏
            raw_features={},  # 原始特征已脱敏
            target_agent=request.agent_type.value
        )

        # 调用gRPC服务
        grpc_response: GrpcAgentResponse = await self.stub.RouteLearnerToEducation(grpc_request)

        # 转换响应
        return AgentResponse(
            request_id=grpc_response.request_id,
            agent_type=grpc_response.agent_type,
            success=grpc_response.success,
            result=grpc_response.result,
            error=grpc_response.error,
            metadata=grpc_response.metadata
        )


# ============================================================
# 使用示例
# ============================================================

async def demo_client():
    """演示客户端使用"""
    client = GatewayClient()

    try:
        # 连接
        await client.connect()

        # 健康检查
        healthy = await client.health_check()
        print(f"健康状态: {'健康' if healthy else '不健康'}")

        # 测试路由
        response = await client.route_cross_domain(
            source_domain="learner",
            target_domain="education",
            payload={"test": "data"}
        )
        print(f"路由响应: {response.success}")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(demo_client())
