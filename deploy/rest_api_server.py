"""
REST API服务器
连接前端和后端gRPC服务
提供HTTP接口供前端调用
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入gRPC客户端
from gateway.client import GatewayClient
from protocols.messages import AgentType, AgentRequest

# 创建FastAPI应用
app = FastAPI(
    title="教育平台REST API",
    description="连接前端和gRPC后端服务的REST API",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源（开发环境）
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局gRPC客户端
gateway_client: Optional[GatewayClient] = None


# ============================================================
# 数据模型
# ============================================================

class StudentMessage(BaseModel):
    """学生消息"""
    student_id: str
    message: str
    learning_style: str = "Visual"
    timestamp: Optional[str] = None


class GenerateTestRequest(BaseModel):
    """生成测试请求"""
    student_id: str
    knowledge_point: str


class APIResponse(BaseModel):
    """API响应"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ============================================================
# 启动和关闭事件
# ============================================================

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化gRPC客户端"""
    global gateway_client
    try:
        gateway_client = GatewayClient(
            gateway_host="localhost",
            gateway_port=50051
        )
        await gateway_client.connect()
        print("✅ REST API服务器启动成功")
        print("✅ 已连接到gRPC网关服务")
    except Exception as e:
        print(f"⚠️ 无法连接到gRPC网关服务: {e}")
        print("⚠️ 某些功能可能不可用")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    global gateway_client
    if gateway_client:
        await gateway_client.close()
        print("✅ REST API服务器已关闭")


# ============================================================
# 健康检查
# ============================================================

@app.get("/health")
async def health_check():
    """健康检查"""
    healthy = True
    gateway_status = "connected"

    if gateway_client and gateway_client.channel:
        try:
            # 尝试调用gRPC健康检查
            await gateway_client.health_check()
        except Exception as e:
            healthy = False
            gateway_status = f"disconnected: {e}"
    else:
        gateway_status = "not initialized"

    return {
        "status": "healthy" if healthy else "unhealthy",
        "gateway": gateway_status,
        "services": {
            "rest_api": "running",
            "gateway": gateway_status
        }
    }


# ============================================================
# 学生端API
# ============================================================

@app.post("/api/student/message", response_model=APIResponse)
async def send_student_message(message: StudentMessage):
    """
    学生发送消息，获取AI辅导回复
    """
    try:
        if not gateway_client:
            raise HTTPException(status_code=503, detail="后端服务不可用")

        # 构建智能体请求
        request = AgentRequest(
            request_id=f"req_{message.student_id}_{id(message)}",
            agent_type=AgentType.AG3_TUTOR,
            task_type="tutor",
            data={
                "student_pseudonym": message.student_id,  # 使用伪ID保护隐私
                "learning_style": message.learning_style,
                "error_history": [],  # 可以从数据库获取历史错误
                "student_input": message.message
            },
            context={
                "timestamp": message.timestamp or asyncio.get_event_loop().time()
            }
        )

        # 调用gRPC服务
        response = await gateway_client.route_to_education(request)

        if response.success:
            # 提取辅导响应
            result = response.result or {}
            explanation = result.get("explanation", "")
            questions = result.get("scaffolding_questions", [])

            # 构建回复文本
            response_text = explanation
            if questions:
                response_text += "\n\n思考问题：\n" + "\n".join([f"• {q}" for q in questions])

            return APIResponse(
                success=True,
                data={
                    "response": response_text,
                    "metadata": {
                        "agent_type": response.agent_type,
                        "request_id": response.request_id
                    }
                }
            )
        else:
            raise HTTPException(status_code=500, detail=response.error)

    except HTTPException:
        raise
    except Exception as e:
        print(f"处理学生消息失败: {e}")
        # 返回备用响应
        from frontend.api import generateFallbackResponse
        return APIResponse(
            success=True,
            data={
                "response": generateFallbackResponse(message.learning_style),
                "fallback": True,
                "error": str(e)
            }
        )


# ============================================================
# 教师端API
# ============================================================

@app.get("/api/teacher/students")
async def get_all_students():
    """
    获取所有学生列表
    """
    try:
        # 这里应该从数据库或gRPC服务获取真实数据
        # 目前返回模拟数据
        from frontend.api import getMockStudents
        students = getMockStudents()

        return {
            "success": True,
            "data": students,
            "total": len(students)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/teacher/student/{student_id}")
async def get_student_detail(student_id: str):
    """
    获取学生详情
    """
    try:
        # 这里应该从数据库获取真实数据
        from frontend.api import getMockStudents
        students = getMockStudents()
        student = next((s for s in students if s["id"] == student_id), None)

        if not student:
            raise HTTPException(status_code=404, detail="学生不存在")

        # 模拟获取更多详情
        detail = {
            **student,
            "chat_history": [
                {
                    "sender": "student",
                    "message": "老师，我刚才问了一个关于二次函数的问题",
                    "timestamp": "2025-01-13 10:30:00"
                },
                {
                    "sender": "teacher",
                    "message": "好的，我来帮你解答。二次函数的顶点公式是...",
                    "timestamp": "2025-01-13 10:30:30"
                }
            ],
            "learning_progress": [
                {"topic": "二次函数", "progress": 85},
                {"topic": "三角函数", "progress": 45},
                {"topic": "一元二次不等式", "progress": 20}
            ]
        }

        return {
            "success": True,
            "data": detail
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/teacher/generate-test")
async def generate_test(request: GenerateTestRequest):
    """
    为学生生成测试题
    """
    try:
        if not gateway_client:
            raise HTTPException(status_code=503, detail="后端服务不可用")

        # 调用AG5评估智能体
        agent_request = AgentRequest(
            request_id=f"test_{request.student_id}_{id(request)}",
            agent_type=AgentType.AG5_ASSESS,
            task_type="generate_test",
            data={
                "student_pseudonym": request.student_id,
                "knowledge_point": request.knowledge_point,
                "difficulty": "medium"
            },
            context={}
        )

        response = await gateway_client.route_to_education(agent_request)

        if response.success:
            return APIResponse(
                success=True,
                data={
                    "questions": response.result or {},
                    "student_id": request.student_id
                }
            )
        else:
            raise HTTPException(status_code=500, detail=response.error)

    except HTTPException:
        raise
    except Exception as e:
        print(f"生成测试失败: {e}")
        # 返回模拟测试题
        return APIResponse(
            success=True,
            data={
                "questions": {
                    "knowledge_point": request.knowledge_point,
                    "items": [
                        {
                            "question": f"关于{request.knowledge_point}的应用题",
                            "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
                            "answer": "A",
                            "difficulty": "medium"
                        }
                    ]
                },
                "fallback": True
            }
        )


# ============================================================
# 主函数
# ============================================================

if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("🚀 启动REST API服务器")
    print("=" * 60)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )
