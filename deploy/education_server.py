"""
教学域智能体gRPC服务器
部署为独立微服务（教学域）
"""
import asyncio
import grpc
from concurrent import futures
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import grpc
from protocols.gateway_pb2 import (
    AgentRequestGRPC, AgentResponseGRPC,
    HealthCheckRequest, HealthCheckResponse
)
from protocols.gateway_pb2_grpc import AgentServiceServicer, add_AgentServiceServicer_to_server

from agents.ag2_style import get_ag2_agent
from agents.ag3_tutor import get_ag3_agent
from agents.ag4_content import get_ag4_agent
from agents.ag5_assess import get_ag5_agent


class EducationDomainServiceImpl(AgentServiceServicer):
    """教学域智能体服务实现"""

    def __init__(self):
        # 初始化所有智能体
        self.ag2 = get_ag2_agent()
        self.ag3 = get_ag3_agent()
        self.ag4 = get_ag4_agent()
        self.ag5 = get_ag5_agent()

        # 智能体映射
        self.agent_map = {
            "AG2_Style": self.ag2,
            "AG3_Tutor": self.ag3,
            "AG4_Content": self.ag4,
            "AG5_Assessment": self.ag5
        }

        print(f"[Education Server] ✅ 智能体初始化完成")
        print(f"  - AG2: 学习风格识别")
        print(f"  - AG3: 自适应辅导")
        print(f"  - AG4: 内容挖掘")
        print(f"  - AG5: 自适应评估")

    def ProcessRequest(
        self,
        request: AgentRequestGRPC,
        context
    ) -> AgentResponseGRPC:
        """处理智能体请求"""
        try:
            from protocols.messages import AgentRequest as PyAgentRequest

            # 构建请求
            py_request = PyAgentRequest(
                request_id=request.request_id,
                agent_type=request.agent_type,
                task_type=request.task_type,
                data=dict(request.data),
                context=dict(request.context)
            )

            # 路由到对应智能体
            agent = self.agent_map.get(request.agent_type)

            if not agent:
                return AgentResponseGRPC(
                    request_id=request.request_id,
                    agent_type=request.agent_type,
                    success=False,
                    error=f"Unknown agent type: {request.agent_type}"
                )

            # 调用智能体
            response = asyncio.run(agent.process_request(py_request))

            # 转换结果为JSON（因为protobuf不支持嵌套Dict）
            result_json = json.dumps(response.result) if response.result else "{}"
            metadata_json = json.dumps(response.metadata) if response.metadata else "{}"

            return AgentResponseGRPC(
                request_id=response.request_id,
                agent_type=response.agent_type,
                success=response.success,
                result={"json": result_json},
                error=response.error or "",
                metadata={"json": metadata_json}
            )

        except Exception as e:
            import traceback
            traceback.print_exc()
            return AgentResponseGRPC(
                request_id=request.request_id,
                agent_type=request.agent_type,
                success=False,
                error=str(e)
            )

    def HealthCheck(
        self,
        request: HealthCheckRequest,
        context
    ) -> HealthCheckResponse:
        """健康检查"""
        # 检查所有智能体是否可用
        all_healthy = all(agent is not None for agent in self.agent_map.values())

        return HealthCheckResponse(
            healthy=all_healthy,
            version="1.0.0",
            uptime=0
        )


def serve(
    port: int = 50052,
    max_workers: int = 10
):
    """启动教学域服务器"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))

    add_AgentServiceServicer_to_server(
        EducationDomainServiceImpl(),
        server
    )

    server.add_insecure_port(f"[::]:{port}")
    server.start()

    print(f"[Education Server] 🚀 启动成功，监听端口: {port}")
    print(f"[Education Server] 教学域 - 智能体微服务集群")

    server.wait_for_termination()


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="教学域智能体gRPC服务器")
    parser.add_argument("--port", type=int, default=50052, help="监听端口")
    parser.add_argument("--workers", type=int, default=10, help="工作线程数")

    args = parser.parse_args()

    serve(port=args.port, max_workers=args.workers)
