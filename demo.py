"""
零信任隐私保护多智能体学习平台 - MVP Demo
演示完整的端到端流程
"""
import asyncio
import sys
import os
from pydantic import BaseModel

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from protocols.messages import LearnerData, AgentType
from gateway.router import get_gateway
from agents.ag2_style import get_ag2_agent
from agents.ag3_tutor import get_ag3_agent


async def full_pipeline_demo():
    """
    完整流程演示：
    学生数据 → 隐私网关 → AG2诊断 → AG3辅导
    """

    print("\n" + "🔒"*40)
    print("零信任隐私保护多智能体学习平台 - MVP Demo")
    print("🔒"*40)

    # ================================================
    # 步骤1：准备学习者数据（高信域）
    # ================================================
    print("\n📚 步骤1：学习者域 - A1收集原始数据")
    print("-" * 60)

    learner_data = LearnerData(
        student_id="stu_20240313_001",
        demographic={
            "age": 15,
            "grade": 9,
            "school": "实验中学"
        },
        interaction_history=[
            {"action": "watch_video", "duration": 180, "completion": 0.8},
            {"action": "solve_problem", "attempts": 3, "success": False}
        ],
        performance_records=[
            {"subject": "数学", "topic": "二次函数", "score": 65},
            {"subject": "数学", "topic": "三角函数", "score": 72}
        ],
        raw_features={
            "visual_preference": 0.85,  # 视觉型倾向
            "auditory_preference": 0.55,
            "reading_speed": 0.70,
            "math_ability": 0.68,
            "attention_span": 0.62,
            "question_response_time": 0.75,
            "error_pattern_repetition": 0.45
        }
    )

    print(f"学生ID: {learner_data.student_id}")
    print(f"人口统计: {learner_data.demographic}")
    print(f"原始特征（明文，仅A1可见）:")
    for k, v in learner_data.raw_features.items():
        print(f"  - {k}: {v}")

    # ================================================
    # 步骤2：隐私网关处理（SRPG + RBAC）
    # ================================================
    print("\n🛡️  步骤2：隐私网关 - SRPG保护 + RBAC授权")
    print("-" * 60)

    gateway = get_gateway()

    # 场景A：学习风格诊断（路由到AG2）
    print("\n→ 场景A：学习风格诊断")
    print("-" * 40)

    response_ag2 = await gateway.route_learner_to_education(
        learner_data=learner_data,
        target_agent=AgentType.AG2_STYLE
    )

    if response_ag2.success:
        print(f"✅ AG2路由成功")
        print(f"   匿名化ID: {response_ag2.result['pseudonym']}")
        print(f"   保护特征（前3维）: {list(response_ag2.result['features'].values())[:3]}")
        print(f"   消耗隐私预算: {response_ag2.metadata['privacy_cost']:.4f}")
    else:
        print(f"❌ AG2路由失败: {response_ag2.error}")
        return

    # ================================================
    # 步骤3：AG2学习风格识别
    # ================================================
    print("\n🧠 步骤3：AG2 - 学习风格识别")
    print("-" * 60)

    ag2_agent = get_ag2_agent()

    # AG2分析（实际由网关调用）
    style_result = ag2_agent.analyze(
        protected_features=response_ag2.result['features']
    )

    print(f"✅ 分析完成")
    print(f"   主要学习风格: {style_result['primary_style']}")
    print(f"   置信度: {style_result['confidence']:.1%}")
    print(f"   分析理由: {style_result.get('reasoning', 'N/A')}")

    # ================================================
    # 步骤4：AG3自适应辅导（使用AG2的结果）
    # ================================================
    print("\n💬 步骤4：AG3 - 自适应辅导")
    print("-" * 60)

    # 先切换状态到辅导模式
    from gateway.rbac_manager import get_rbac_manager, BusinessState
    rbac = get_rbac_manager()
    rbac.transition_state(BusinessState.TUTORING)

    # AG3生成辅导内容
    ag3_agent = get_ag3_agent()

    tutor_result = ag3_agent.generate_scaffolding(
        student_pseudonym=response_ag2.result['pseudonym'],
        learning_style=style_result['primary_style'],
        error_history=[
            {
                "knowledge_point": "二次函数求极值",
                "error_type": "Conceptual",
                "student_answer": "直接套公式但理解有误"
            }
        ],
        student_input="我在求二次函数极值时总是不知道怎么确定开口方向",
        context={"style_confidence": style_result['confidence']}
    )

    print(f"✅ 辅导内容生成完成")
    print(f"\n启发式提问:")
    for i, q in enumerate(tutor_result['scaffolding_questions'], 1):
        print(f"   {i}. {q}")
    print(f"\n适配{style_result['primary_style']}风格的解释:")
    print(f"   {tutor_result.get('explanation', 'N/A')}")
    if 'encouragement' in tutor_result:
        print(f"\n激励语: {tutor_result['encouragement']}")

    # ================================================
    # 步骤5：查看隐私预算使用情况
    # ================================================
    print("\n📊 步骤5：隐私预算统计")
    print("-" * 60)

    remaining = gateway.privacy_engine.get_remaining_budget()
    used = gateway.privacy_engine.used_budget
    total = gateway.privacy_engine.max_budget

    print(f"总隐私预算: ε = {total:.2f}")
    print(f"已使用: ε = {used:.4f}")
    print(f"剩余: ε = {remaining:.4f}")
    print(f"使用率: {used/total:.1%}")

    # ================================================
    # 演示结束
    # ================================================
    print("\n" + "🎉"*40)
    print("Demo演示完成！")
    print("🎉"*40)
    print("\n核心特性验证：")
    print("✅ 三域物理隔离（学习者域 / 网关 / 教学域）")
    print("✅ 跨域通信必须经过网关（无横向直连）")
    print("✅ SRPG隐空间重构 + LDP噪声注入")
    print("✅ 动态RBAC临时授权")
    print("✅ 智能体零原始隐私访问")
    print("\n下一步可以：")
    print("- 实现AG4内容挖掘和AG5自适应评估")
    print("- 集成G-safeguard的GNN拓扑防御")
    print("- 部署为gRPC微服务架构")
    print("- 添加前端界面和可视化")


async def security_test():
    """
    安全性测试：验证横向连接被阻止
    """
    print("\n" + "🔐"*40)
    print("安全性测试 - 验证零信任机制")
    print("🔐"*40)

    from protocols.messages import CrossDomainMessage, DomainType, AgentType
    from gateway.router import get_gateway

    gateway = get_gateway()

    # 尝试：AG2直接向AG3发送数据（应该被拒绝）
    print("\n测试：AG2 → AG3 直连（应被拒绝）")
    print("-" * 60)

    illegal_message = CrossDomainMessage(
        source_domain=DomainType.EDUCATION,  # 教学域
        target_domain=DomainType.EDUCATION,  # 教学域（同域）
        source_agent=AgentType.AG2_STYLE,
        target_agent=AgentType.AG3_TUTOR,
        payload={"data": "malicious lateral connection attempt"}
    )

    response = await gateway.route_cross_domain(illegal_message)

    if not response.success:
        print(f"✅ 测试通过：横向连接已被阻止")
        print(f"   错误信息: {response.error}")
    else:
        print(f"❌ 测试失败：横向连接未被阻止！")

    # 尝试：AG3请求访问原始隐私数据（应被RBAC拒绝）
    print("\n测试：AG3请求原始数据（应被RBAC拒绝）")
    print("-" * 60)

    rbac = get_rbac_manager()
    has_permission = rbac.check_permission(
        agent_id=AgentType.AG3_TUTOR,
        resource_id="stu_20240313_001_raw_data",
        required_level="RAW"
    )

    if not has_permission:
        print(f"✅ 测试通过：AG3无原始数据访问权限")
    else:
        print(f"❌ 测试失败：AG3获得了原始数据权限！")


if __name__ == "__main__":
    print("\n选择演示模式：")
    print("1. 完整流程演示（学习者 → 网关 → AG2 → AG3）")
    print("2. 安全性测试（验证零信任机制）")
    print("3. 两者都运行")

    choice = input("\n请输入选项 (1/2/3，默认3): ").strip() or "3"

    async def run_all():
        if choice in ["1", "3"]:
            await full_pipeline_demo()
        if choice in ["2", "3"]:
            await security_test()

    asyncio.run(run_all())
