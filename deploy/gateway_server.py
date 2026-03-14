"""
隐私网关gRPC服务器
部署为独立微服务（控制平面域）
"""
import asyncio
import grpc
from concurrent import futures
import json
from typing import Dict, Any

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import grpc
from protocols.gateway_pb2 import (
    CrossDomainRequest, CrossDomainResponse,
    LearnerDataRequest, AgentResponse,
    TopologyRequest, TopologyResponse,
    HealthCheckRequest, HealthCheckResponse,
    NodeInfo, EdgeInfo
)
from protocols.gateway_pb2_grpc import PrivacyGatewayServicer, add_PrivacyGatewayServicer_to_server

from gateway.router import get_gateway
from protocols.messages import LearnerData as PyLearnerData, AgentType


class GatewayServiceImpl(PrivacyGatewayServicer):
    """隐私网关gRPC服务实现"""

    def __init__(self):
        self.gateway = get_gateway()

    def RouteCrossDomain(
        self,
        request: CrossDomainRequest,
        context
    ) -> CrossDomainResponse:
        """路由跨域请求"""
        try:
            from protocols.messages import CrossDomainMessage, DomainType

            # 构建消息
            message = CrossDomainMessage(
                msg_id=request.msg_id,
                source_domain=DomainType(request.source_domain),
                target_domain=DomainType(request.target_domain),
                payload=dict(request.payload),
                timestamp=request.timestamp
            )

            # 路由
            # 注意：这里需要异步转同步，实际部署时应使用async gRPC
            response = asyncio.run(self.gateway.route_cross_domain(message))

            return CrossDomainResponse(
                success=response.success,
                error=response.error or "",
                result=response.result or {}
            )

        except Exception as e:
            return CrossDomainResponse(
                success=False,
                error=str(e),
                result={}
            )

    def RouteLearnerToEducation(
        self,
        request: LearnerDataRequest,
        context
    ) -> AgentResponse:
        """学习者域 → 教学域路由"""
        try:
            # 构建学习者数据
            learner_data = PyLearnerData(
                student_id=request.student_id,
                demographic=dict(request.demographic),
                raw_features=dict(request.raw_features)
            )

            # 路由
            response = asyncio.run(self.gateway.route_learner_to_education(
                learner_data=learner_data,
                target_agent=AgentType(request.target_agent)
            ))

            return AgentResponse(
                request_id=response.request_id,
                agent_type=response.agent_type,
                success=response.success,
                result=response.result or {},
                error=response.error or "",
                metadata=response.metadata or {}
            )

        except Exception as e:
            return AgentResponse(
                request_id="",
                agent_type=request.target_agent,
                success=False,
                error=str(e),
                result={},
                metadata={}
            )

    def GetTopologyStatus(
        self,
        request: TopologyRequest,
        context
    ) -> TopologyResponse:
        """获取GNN拓扑状态"""
        try:
            topology = self.gateway.get_topology_status()

            if not topology:
                return TopologyResponse(
                    nodes={},
                    edges=[],
                    quarantined_nodes=[],
                    anomaly_count=0
                )

            # 转换节点信息
            nodes = {}
            for node_id, node_info in topology["nodes"].items():
                nodes[node_id] = NodeInfo(
                    type=node_info.get("type", ""),
                    domain=node_info.get("domain", ""),
                    created_at=int(node_info.get("created_at", 0))
                )

            # 转换边信息
            edges = []
            for edge_data in topology.get("edges", []):
                if len(edge_data) >= 4:
                    edges.append(EdgeInfo(
                        src=edge_data[0],
                        dst=edge_data[1],
                        type=edge_data[2],
                        weight=edge_data[3]
                    ))

            return TopologyResponse(
                nodes=nodes,
                edges=edges,
                quarantined_nodes=topology.get("quarantined_nodes", []),
                anomaly_count=topology.get("anomaly_count", 0)
            )

        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return TopologyResponse()

    def HealthCheck(
        self,
        request: HealthCheckRequest,
        context
    ) -> HealthCheckResponse:
        """健康检查"""
        return HealthCheckResponse(
            healthy=True,
            version="1.0.0",
            uptime=0  # 实际应记录启动时间
        )


def serve(
    port: int = 50051,
    max_workers: int = 10
):
    """启动网关服务器"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))

    add_PrivacyGatewayServicer_to_server(
        GatewayServiceImpl(),
        server
    )

    server.add_insecure_port(f"[::]:{port}")
    server.start()

    print(f"[Gateway Server] 🚀 启动成功，监听端口: {port}")
    print(f"[Gateway Server] 控制平面域 - 隐私网关微服务")

    server.wait_for_termination()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="隐私网关gRPC服务器")
    parser.add_argument("--port", type=int, default=50051, help="监听端口")
    parser.add_argument("--workers", type=int, default=10, help="工作线程数")

    args = parser.parse_args()

    serve(port=args.port, max_workers=args.workers)
