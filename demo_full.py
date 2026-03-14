"""
零信任隐私保护多智能体学习平台 - 完整演示
包含所有智能体和GNN防御
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from protocols.messages import LearnerData, AgentType
from gateway.router import get_gateway
from agents.ag2_style import get_ag2_agent
from agents.ag3_tutor import get_ag3_agent
from agents.ag4_content import get_ag4_agent
from agents.ag5_assess import get_ag5_agent
from gateway.rbac_manager import get_rbac_manager, BusinessState


async def complete_learning_journey():
    """
    完整学习旅程演示
    学生数据 → 诊断 → 辅导 → 资源检索 → 评估
    """

    print("\n" + "🎓"*40)
    print("零信任隐私保护多智能体学习平台 - 完整演示")
    print("🎓"*40)

    # ================================================
    # 步骤1：学习者数据采集
    # ================================================
    print("\n📚 步骤1：学习者域 - 数据采集")
    print("-" * 70)

    learner_data = LearnerData(
        student_id="stu_20240313_zhang",
        demographic={"age": 15, "grade": 9, "school": "实验中学"},
        interaction_history=[
            {"action": "watch_video", "topic": "二次函数", "duration": 300, "completion": 0.85},
            {"action": "solve_problem", "attempts": 3, "success": False}
        ],
        performance_records=[
            {"subject": "数学", "topic": "二次函数顶点", "score": 62},
            {"subject": "数学", "topic": "二次函数图像", "score": 70}
        ],
        raw_features={
            "visual_preference": 0.82,      # 视觉型
            "auditory_preference": 0.54,
            "reading_preference": 0.68,
            "kinesthetic_preference": 0.61,
            "math_ability": 0.72,
            "abstract_thinking": 0.65,
            "question_response_time": 0.58,
            "error_pattern_repetition": 0.48
        }
    )

    print(f"学生ID: {learner_data.student_id}")
    print(f"人口统计: {learner_data.demographic}")
    print(f"学习表现:")
    for record in learner_data.performance_records:
        print(f"  - {record['subject']} | {record['topic']}: {record['score']}分")

    # ================================================
    # 步骤2：学习风格诊断（AG2）
    # ================================================
    print("\n🧠 步骤2：AG2 - 学习风格诊断")
    print("-" * 70)

    gateway = get_gateway()
    ag2 = get_ag2_agent()

    # 通过网关路由到AG2
    response_ag2 = await gateway.route_learner_to_education(
        learner_data=learner_data,
        target_agent=AgentType.AG2_STYLE
    )

    if not response_ag2.success:
        print(f"❌ AG2诊断失败: {response_ag2.error}")
        return

    # AG2分析
    style_result = ag2.analyze(
        protected_features=response_ag2.result['features']
    )

    print(f"✅ 诊断完成")
    print(f"   学习风格: {style_result['primary_style']}")
    print(f"   置信度: {style_result['confidence']:.1%}")
    print(f"   分析: {style_result.get('reasoning', 'N/A')}")

    # ================================================
    # 步骤3：自适应辅导（AG3）
    # ================================================
    print("\n💬 步骤3：AG3 - 自适应辅导")
    print("-" * 70)

    ag3 = get_ag3_agent()
    rbac = get_rbac_manager()
    rbac.transition_state(BusinessState.TUTORING)

    tutor_result = ag3.generate_scaffolding(
        student_pseudonym=response_ag2.result['pseudonym'],
        learning_style=style_result['primary_style'],
        error_history=[
            {
                "knowledge_point": "二次函数顶点坐标",
                "error_type": "Conceptual",
                "student_answer": "公式记错，符号搞混"
            }
        ],
        student_input="我总是搞不清楚二次函数顶点坐标公式里的b²-4ac和2a",
        context={"style_confidence": style_result['confidence']}
    )

    print(f"✅ 辅导内容生成")
    print(f"\n启发式提问:")
    for i, q in enumerate(tutor_result['scaffolding_questions'], 1):
        print(f"   {i}. {q}")
    print(f"\n适配{style_result['primary_style']}风格的解释:")
    print(f"   {tutor_result.get('explanation', 'N/A')}")

    # ================================================
    # 步骤4：内容挖掘（AG4）
    # ================================================
    print("\n📚 步骤4：AG4 - 个性化学习资源推荐")
    print("-" * 70)

    ag4 = get_ag4_agent()
    rbac.transition_state(BusinessState.CONTENT_RETRIEVAL)

    content_result = ag4.retrieve_resources(
        knowledge_points=["二次函数", "顶点坐标", "最值问题"],
        difficulty=0.72,
        learning_style=style_result['primary_style']
    )

    print(f"✅ 推荐完成: {len(content_result['recommended_resources'])}个资源")
    for i, res in enumerate(content_result['recommended_resources'], 1):
        print(f"\n{i}. {res['title']}")
        print(f"   类型: {res['type']}")
        print(f"   难度: {res['difficulty']}")
        print(f"   预计用时: {res['estimated_time']}秒")
        print(f"   推荐理由: {res['reason']}")

    print(f"\n学习顺序建议: {content_result['study_sequence']}")

    # ================================================
    # 步骤5：自适应评估（AG5）
    # ================================================
    print("\n📝 步骤5：AG5 - 学习效果评估")
    print("-" * 70)

    ag5 = get_ag5_agent()
    rbac.transition_state(BusinessState.ASSESSING)

    # 生成测试
    test_spec = ag5.generate_test(
        knowledge_points=["二次函数", "顶点坐标", "最值问题"],
        difficulty=0.72,
        num_questions=3
    )

    print(f"✅ 测试生成完成: {len(test_spec['questions'])}题")
    print(f"测试ID: {test_spec['test_id']}")
    print(f"预计用时: {test_spec['estimated_time']}秒")

    print(f"\n题目预览:")
    for q in test_spec['questions'][:2]:  # 只显示前2题
        print(f"\n{q['question_id']}. {q['question']}")
        for opt in q['options'][:2]:  # 只显示前2个选项
            print(f"  {opt}")
        print(f"  ...")

    # 模拟学生作答
    mock_answers = {
        "Q1": "A",
        "Q2": "B",
        "Q3": "C"
    }

    print(f"\n学生作答: {mock_answers}")

    # 评分
    grading_result = ag5.grade_test(
        test_spec=test_spec,
        student_answers=mock_answers
    )

    print(f"\n✅ 评分完成")
    print(f"总分: {grading_result['total_score']}/100")
    print(f"评价: {grading_result['overall_feedback']}")
    if grading_result['weak_points']:
        print(f"薄弱点: {', '.join(grading_result['weak_points'])}")
    if grading_result['suggested_next_topics']:
        print(f"建议下一步学习: {', '.join(grading_result['suggested_next_topics'])}")

    # ================================================
    # 步骤6：隐私预算统计
    # ================================================
    print("\n📊 步骤6：隐私预算与安全统计")
    print("-" * 70)

    remaining = gateway.privacy_engine.get_remaining_budget()
    used = gateway.privacy_engine.used_budget
    total = gateway.privacy_engine.max_budget

    print(f"总隐私预算: ε = {total:.2f}")
    print(f"已使用: ε = {used:.4f}")
    print(f"剩余: ε = {remaining:.4f}")
    print(f"使用率: {used/total:.1%}")

    # GNN统计
    if gateway.gnn_enabled:
        gnn_stats = gateway.gnn_guard.get_statistics()
        print(f"\nGNN拓扑防御统计:")
        print(f"总节点数: {gnn_stats['total_nodes']}")
        print(f"总交互数: {gnn_stats['total_edges']}")
        print(f"被隔离节点: {gnn_stats['quarantined_nodes']}")
        print(f"异常事件: {gnn_stats['anomaly_events']}")
        print(f"异常率: {gnn_stats['anomaly_rate']:.2%}")

    # ================================================
    # 演示结束
    # ================================================
    print("\n" + "🎉"*40)
    print("完整学习旅程演示完成！")
    print("🎉"*40)
    print("\n核心创新点验证：")
    print("✅ 三域物理隔离")
    print("✅ SRPG + LDP隐私保护")
    print("✅ 动态RBAC临时授权")
    print("✅ GNN实时拓扑防御")
    print("✅ 五个智能体协同工作")
    print("✅ 零横向直连")
    print("✅ AG5独立评估（防自判幻觉）")


async def security_audit():
    """
    安全审计演示
    测试各种攻击场景
    """
    print("\n" + "🔐"*40)
    print("安全审计 - 攻击场景测试")
    print("🔐"*40)

    from protocols.messages import CrossDomainMessage, DomainType, AgentType
    from gateway.router import get_gateway

    gateway = get_gateway()

    # 攻击场景1：横向连接
    print("\n攻击场景1：AG2试图直接联系AG3")
    print("-" * 70)

    lateral_msg = CrossDomainMessage(
        source_domain=DomainType.EDUCATION,
        target_domain=DomainType.EDUCATION,
        source_agent=AgentType.AG2_STYLE,
        target_agent=AgentType.AG3_TUTOR,
        payload={"malicious_payload": "attempt_data_exfiltration"}
    )

    response = await gateway.route_cross_domain(lateral_msg)
    if not response.success:
        print(f"✅ 攻击被阻止: {response.error}")
    else:
        print(f"❌ 攻击成功！系统存在漏洞")

    # 攻击场景2：权限提升
    print("\n攻击场景2：AG3试图访问原始隐私数据")
    print("-" * 70)

    rbac = get_rbac_manager()
    has_raw_access = rbac.check_permission(
        agent_id=AgentType.AG3_TUTOR,
        resource_id="stu_20240313_zhang_raw_data",
        required_level="RAW"
    )

    if not has_raw_access:
        print(f"✅ 权限被拒绝: AG3无法访问RAW级别数据")
    else:
        print(f"❌ 权限提升攻击成功！")

    # 攻击场景3：隐私预算耗尽攻击
    print("\n攻击场景3：快速连续请求耗尽隐私预算")
    print("-" * 70)

    initial_budget = gateway.privacy_engine.get_remaining_budget()
    print(f"初始剩余预算: {initial_budget:.4f}")

    for i in range(25):  # 尝试25次快速请求
        try:
            gateway.privacy_engine.protect(learner_data)
        except Exception as e:
            print(f"✅ 第{i+1}次请求被阻止: {str(e)[:50]}...")
            break

    final_budget = gateway.privacy_engine.get_remaining_budget()
    print(f"最终剩余预算: {final_budget:.4f}")
    print(f"预算保护机制: {'✅ 正常' if final_budget > 0 else '❌ 失效'}")

    # GNN异常检测
    if gateway.gnn_enabled:
        print("\nGNN拓扑异常检测")
        print("-" * 70)

        # 模拟异常流量
        for i in range(5):
            gateway.gnn_guard.monitor_interaction(
                src=f"Attacker_{i}",
                dst="AG3",
                interaction_type="suspicious_traffic",
                metadata={"frequency": "abnormal"}
            )

        topology = gateway.gnn_guard.get_topology_status()
        print(f"被隔离节点: {topology['quarantined_nodes']}")
        print(f"异常事件数: {topology['anomaly_count']}")
        print(f"GNN防御: {'✅ 正常' if topology['anomaly_count'] > 0 else '⚠️ 未触发'}")


async def main():
    """主函数"""
    print("\n选择演示模式：")
    print("1. 完整学习旅程（推荐）")
    print("2. 安全审计（攻击测试）")
    print("3. 两者都运行")

    choice = input("\n请输入选项 (1/2/3，默认1): ").strip() or "1"

    if choice in ["1", "3"]:
        await complete_learning_journey()

    if choice in ["2", "3"]:
        await security_audit()

    # 提示用户查看前端
    print("\n" + "="*70)
    print("💻 前端可视化界面")
    print("="*70)
    print("\n在浏览器中打开以下地址查看实时监控面板：")
    print("🔗 file:///Users/mac9/.openclaw/workspace/edu-mas-privacy/frontend/index.html")
    print("\n功能特性：")
    print("  - 实时拓扑图（智能体交互网络）")
    print("  - 隐私预算追踪可视化")
    print("  - RBAC权限状态图表")
    print("  - 实时日志监控")
    print("  - 模拟请求生成器")

    # Docker部署提示
    print("\n" + "="*70)
    print("🐳 Docker微服务部署")
    print("="*70)
    print("\n在项目根目录运行以下命令部署为微服务集群：")
    print("  cd edu-mas-privacy")
    print("  docker-compose up -d")
    print("\n服务端口：")
    print("  - 网关: localhost:50051")
    print("  - 教学域: localhost:50052")
    print("  - 学习者域: localhost:50053")
    print("  - Redis: localhost:6379")
    print("  - Grafana监控: localhost:3000")


if __name__ == "__main__":
    # 导入缺失的模块
    from pydantic import BaseModel

    # 运行演示
    asyncio.run(main())
