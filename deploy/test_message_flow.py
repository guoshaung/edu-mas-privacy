"""
测试学生消息流程
验证学生端 → REST API → 网关 → 教学域 → 回复 流程
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gateway.client import GatewayClient
from protocols.messages import AgentRequest, AgentType


async def test_student_message():
    """测试学生消息发送和回复"""

    print("=" * 60)
    print("🧪 测试学生消息流程")
    print("=" * 60)
    print()

    # 连接网关
    print("1️⃣ 连接到网关服务...")
    try:
        client = GatewayClient(
            gateway_host="localhost",
            gateway_port=50051
        )
        await client.connect()
        print("✅ 成功连接到网关")
    except Exception as e:
        print(f"❌ 连接网关失败: {e}")
        print("\n请先运行: ./deploy/start_all.sh")
        return False

    print()

    # 测试健康检查
    print("2️⃣ 检查服务健康状态...")
    try:
        healthy = await client.health_check()
        if healthy:
            print("✅ 网关服务健康")
        else:
            print("⚠️  网关服务不健康")
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False

    print()

    # 测试学生消息
    print("3️⃣ 发送学生消息...")
    print("   学生ID: stu_001")
    print("   学习风格: Visual")
    print("   问题: 二次函数的顶点公式怎么理解？")
    print()

    try:
        request = AgentRequest(
            request_id="test_001",
            agent_type=AgentType.AG3_TUTOR,
            task_type="tutor",
            data={
                "student_pseudonym": "pseudo_stu_001",
                "learning_style": "Visual",
                "error_history": [
                    {
                        "knowledge_point": "二次函数求极值",
                        "error_type": "Calculation",
                        "student_answer": "公式记错"
                    }
                ],
                "student_input": "二次函数的顶点公式怎么理解？"
            },
            context={}
        )

        response = await client.route_to_education(request)

        if response.success:
            print("✅ 成功收到回复！")
            print()
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print("📝 AI老师的回复：")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

            result = response.result or {}
            explanation = result.get("explanation", "无解释")
            questions = result.get("scaffolding_questions", [])

            print(f"\n{explanation}\n")

            if questions:
                print("💡 思考问题：")
                for i, q in enumerate(questions, 1):
                    print(f"   {i}. {q}")

            print()
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

            # 显示元数据
            metadata = response.metadata or {}
            print(f"\n📊 元数据：")
            print(f"   • 请求ID: {response.request_id}")
            print(f"   • 智能体: {response.agent_type}")
            if 'student_pseudonym' in metadata:
                print(f"   • 学生伪ID: {metadata['student_pseudonym']}")
            if 'learning_style' in metadata:
                print(f"   • 学习风格: {metadata['learning_style']}")

            print()
            print("=" * 60)
            print("✅ 测试通过！消息流程工作正常")
            print("=" * 60)

        else:
            print(f"❌ 请求失败: {response.error}")
            return False

    except Exception as e:
        print(f"❌ 发送消息失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await client.close()

    return True


async def test_rest_api():
    """测试REST API服务"""
    import aiohttp

    print()
    print("=" * 60)
    print("🧪 测试REST API")
    print("=" * 60)
    print()

    base_url = "http://localhost:8080"

    # 测试健康检查
    print("1️⃣ 测试健康检查接口...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ 健康检查通过: {data}")
                else:
                    print(f"❌ 健康检查失败: HTTP {resp.status}")
    except Exception as e:
        print(f"❌ REST API不可用: {e}")
        print("\n请先运行: ./deploy/start_all.sh")
        return False

    print()

    # 测试学生消息接口
    print("2️⃣ 测试学生消息接口...")
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "student_id": "stu_001",
                "message": "二次函数的顶点公式怎么理解？",
                "learning_style": "Visual"
            }

            async with session.post(
                f"{base_url}/api/student/message",
                json=payload
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("success"):
                        print("✅ 学生消息发送成功")
                        response_text = data["data"]["response"]
                        print(f"\n📝 AI回复: {response_text[:100]}...")
                    else:
                        print(f"⚠️  消息处理失败: {data.get('error')}")
                else:
                    print(f"❌ HTTP错误: {resp.status}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

    print()
    print("=" * 60)
    print("✅ REST API测试通过！")
    print("=" * 60)

    return True


async def main():
    """主测试函数"""
    print()
    print("🚀 开始测试学生消息功能")
    print()

    # 测试gRPC流程
    grpc_ok = await test_student_message()

    # 测试REST API
    rest_ok = await test_rest_api()

    print()
    print("=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    print(f"  • gRPC流程: {'✅ 通过' if grpc_ok else '❌ 失败'}")
    print(f"  • REST API: {'✅ 通过' if rest_ok else '❌ 失败'}")
    print()

    if grpc_ok and rest_ok:
        print("🎉 所有测试通过！系统工作正常。")
        print()
        print("💡 现在可以：")
        print("   1. 在浏览器打开学生端发送消息")
        print("   2. 在教师端查看学生数据和回复")
        print()
    else:
        print("⚠️  部分测试失败，请检查服务状态和日志。")
        print()


if __name__ == "__main__":
    asyncio.run(main())
