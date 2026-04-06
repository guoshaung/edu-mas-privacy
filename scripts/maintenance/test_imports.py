#!/usr/bin/env python3
"""
简化的导入测试脚本
验证所有模块能否正确导入
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*70)
print("🔍 测试项目导入")
print("="*70 + "\n")

# 测试1: 基础导入
print("1. 测试基础模块导入...")
try:
    from pydantic import BaseModel
    print("   ✅ pydantic导入成功")
except ImportError as e:
    print(f"   ❌ pydantic导入失败: {e}")
    sys.exit(1)

# 测试2: 协议模块
print("\n2. 测试协议模块...")
try:
    from protocols.messages import (
        LearnerData, AgentType, DomainType,
        ProtectedFeatures, PrivacyLevel
    )
    print("   ✅ 协议模块导入成功")
except Exception as e:
    print(f"   ❌ 协议模块导入失败: {e}")
    sys.exit(1)

# 测试3: 隐私引擎
print("\n3. 测试隐私引擎...")
try:
    from gateway.privacy_engine import SRPGEngine, get_privacy_engine
    engine = get_privacy_engine()
    print(f"   ✅ 隐私引擎导入成功")
    print(f"   - 隐私预算: ε={engine.max_budget}")
    print(f"   - 剩余预算: ε={engine.get_remaining_budget():.4f}")
except Exception as e:
    print(f"   ❌ 隐私引擎导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试4: RBAC管理器
print("\n4. 测试RBAC管理器...")
try:
    from gateway.rbac_manager import DynamicRBACManager, get_rbac_manager, BusinessState
    rbac = get_rbac_manager()
    print(f"   ✅ RBAC管理器导入成功")
    print(f"   - 当前状态: {rbac.current_state}")
except Exception as e:
    print(f"   ❌ RBAC管理器导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试5: GNN防御
print("\n5. 测试GNN防御...")
try:
    from gateway.gnn_guard import GNNGuard, get_gnn_guard
    guard = get_gnn_guard()
    print(f"   ✅ GNN防御导入成功")
    stats = guard.get_statistics()
    print(f"   - 节点数: {stats['total_nodes']}")
except Exception as e:
    print(f"   ❌ GNN防御导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试6: 网关路由器
print("\n6. 测试网关路由器...")
try:
    from gateway.router import PrivacyGateway, get_gateway
    gateway = get_gateway()
    print(f"   ✅ 网关路由器导入成功")
    print(f"   - GNN启用: {gateway.gnn_enabled}")
except Exception as e:
    print(f"   ❌ 网关路由器导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试7: 智能体
print("\n7. 测试智能体导入...")
try:
    from agents.ag2_style import LearningStyleAgent, get_ag2_agent
    from agents.ag3_tutor import AdaptiveTutorAgent, get_ag3_agent
    from agents.ag4_content import ContentMiningAgent, get_ag4_agent
    from agents.ag5_assess import AssessmentAgent, get_ag5_agent

    ag2 = get_ag2_agent()
    ag3 = get_ag3_agent()
    ag4 = get_ag4_agent()
    ag5 = get_ag5_agent()

    print(f"   ✅ 所有智能体导入成功")
    print(f"   - AG2: {ag2.agent_type}")
    print(f"   - AG3: {ag3.agent_type}")
    print(f"   - AG4: {ag4.agent_type}")
    print(f"   - AG5: {ag5.agent_type}")
except Exception as e:
    print(f"   ❌ 智能体导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试8: 简单功能测试
print("\n8. 测试基本功能...")
try:
    # 创建测试数据
    learner_data = LearnerData(
        student_id="test_student",
        demographic={"age": 15},
        raw_features={
            "visual": 0.8,
            "auditory": 0.6
        }
    )
    print(f"   ✅ 学习者数据创建成功")

    # 测试SRPG保护
    protected_features, cost = engine.protect(learner_data)
    print(f"   ✅ SRPG保护成功")
    print(f"   - 匿名化ID: {protected_features.student_pseudonym}")
    print(f"   - 消耗预算: {cost:.4f}")

    # 测试RBAC授权
    from protocols.messages import DataPermission
    permission = rbac.grant_permission(
        agent_id=AgentType.AG2_STYLE,
        resource_id=protected_features.student_pseudonym,
        privacy_level=PrivacyLevel.RECONSTRUCTED
    )
    print(f"   ✅ RBAC授权成功")
    if permission:
        print(f"   - 令牌有效期: {permission.expires_at - permission.granted_at:.0f}秒")

except Exception as e:
    print(f"   ❌ 功能测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 总结
print("\n" + "="*70)
print("🎉 所有测试通过！项目导入成功！")
print("="*70)

print("\n下一步:")
print("  1. 安装完整依赖: pip install -r requirements.txt")
print("  2. 运行基础演示: python demo.py")
print("  3. 运行完整演示: python demo_full.py")
print("  4. 查看前端界面: open frontend/index.html")
