# 🔒 零信任隐私保护四重防护体系

## 完整的隐私保护架构

本文档总结零信任隐私保护教育平台的**四层防御体系**，每层都能独立防护，多层协同形成纵深防御。

---

## 📊 四层防护总览

```
┌─────────────────────────────────────────────────────────────┐
│                     学生端（学习者域 - 高信域）                 │
│                  原始数据: 姓名、成绩、学习记录...              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  第1层: LDP（本地差分隐私）                                  │
│  • 在数据离开设备前添加拉普拉斯噪声                           │
│  • 公式: protected = raw + Laplace(0, sensitivity/epsilon)   │
│  • 参数: epsilon = 1.0                                       │
│  • 代码: gateway/privacy_engine.py → _add_laplace_noise()    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  第2层: SRPG（安全重构保护生成）                              │
│  • 神经网络编码 → 隐空间 → 添加噪声 → 解码                    │
│  • 平衡隐私保护和数据有用性                                   │
│  • 匿名化ID: SHA256哈希                                       │
│  • 代码: gateway/privacy_engine.py → SRPGEngine              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  第3层: 动态RBAC（基于角色的访问控制）                         │
│  • 基于业务状态机动态颁发临时权限                              │
│  • 数据降维: 每个智能体只能访问必需字段                         │
│  • 权限令牌: 5分钟过期，最多10次访问                           │
│  • 代码: gateway/rbac_manager.py → DynamicRBACManager        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  第4层: GNN拓扑防御（图神经网络流量监控）                       │
│  • 实时监控智能体交互拓扑                                      │
│  • 检测异常模式（Prompt攻击、横向连接、流量异常）               │
│  • 动态剪枝（隔离污染源）                                      │
│  • 代码: gateway/gnn_guard.py → GNNGuard                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  教学域智能体（低信域）                         │
│           AG2, AG3, AG4, AG5 只能访问脱敏数据                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛡️ 第1层：LDP（本地差分隐私）

### 核心功能
在数据**离开用户设备前**添加噪声，使攻击者无法反推原始数据。

### 技术实现
```python
# 拉普拉斯机制
def _add_laplace_noise(data, sensitivity=1.0):
    scale = sensitivity / self.epsilon  # epsilon = 1.0
    noise = np.random.laplace(0, scale, data.shape)
    return data + noise
```

### 防护效果
- **原始数据**: 学习时长 = 120分钟
- **加噪后**: 119.7 或 120.3 分钟
- **攻击者**: 无法确定真实值

### 详细文档
📖 `docs/PRIVACY_MECHANISMS_EXPLAINED.md` (第1章)

---

## 🧠 第2层：SRPG（安全重构保护生成）

### 核心功能
通过神经网络将噪声数据**重构**为可用特征，既保护隐私又保留有用性。

### 三步流程
```python
# 1. 特征编码
raw_features (64维) → encoded (32维隐空间)

# 2. LDP噪声注入
noisy_encoded = encoded + laplace_noise

# 3. 语义重构
reconstructed = decoder(noisy_encoded) (64维)
```

### 神经网络架构
```python
class LatentReconstructionHead(nn.Module):
    encoder: Linear(64 → 128) → ReLU → Linear(128 → 32)
    decoder: Linear(32 → 128) → ReLU → Linear(128 → 64)
```

### 匿名化ID
```python
pseudonym = sha256("stu_001")[:12]
# "pseudo_abc123"
```

### 详细文档
📖 `docs/PRIVACY_MECHANISMS_EXPLAINED.md` (第2章)

---

## 🔐 第3层：动态RBAC

### 核心功能
基于**业务状态机**动态颁发临时权限，智能体只能访问当前任务必需的数据。

### 状态机
```python
DIAGNOSING → 只有AG2活跃（学习风格识别）
TUTORING   → 只有AG3活跃（辅导）
ASSESSING  → 只有AG5活跃（评估）
```

### 数据降维规则
```python
AG2只能看: ["learning_style", "cognitive_level"]
AG3只能看: ["recent_errors", "style_tag", "weak_kcs"]
AG4只能看: ["knowledge_points", "difficulty_level"]
AG5只能看: ["assessment_config"]
```

### 权限令牌
```python
DataPermission(
    agent_id=AG3_TUTOR,
    resource_id="pseudo_abc123",
    privacy_level=RECONSTRUCTED,
    expires_at=now + 300秒,  # 5分钟后过期
    max_access=10              # 最多访问10次
)
```

### 详细文档
📖 `docs/PRIVACY_MECHANISMS_EXPLAINED.md` (第3章)

---

## 🕸️ 第4层：GNN拓扑防御

### 核心功能
使用图神经网络（GNN）**实时监控**智能体交互拓扑，检测和隔离异常行为。

### 监控的攻击类型
1. **Prompt注入攻击**: 恶意输入诱导泄露隐私
2. **横向连接攻击**: 智能体间非法直接通信
3. **流量异常攻击**: 异常高频访问或大量数据传输

### 检测机制
```python
# 1. 横向连接检测
if is_lateral_connection("AG2", "AG3"):
    quarantine("AG2")  # 立即隔离

# 2. GNN异常检测
anomaly_scores = gnn_model(graph)
if anomaly_scores[node] > 0.7:
    quarantine(node)  # 动态剪枝
```

### 可视化监控
- 🟢 **绿色节点**: 正常
- 🔴 **红色节点**: 被隔离
- ⚠️ **橙色节点**: 高异常分数
- 📊 **边粗细**: 交互频率

### 详细文档
📖 `docs/GNN_GUARD_EXPLAINED.md`

---

## 🔄 四层协同工作示例

### 场景：学生问问题

#### 第1层：LDP保护
```python
# 学生本地
raw_data = {"study_time": 120, "visual_score": 0.85}

# 添加LDP噪声
noisy_data = {
    "study_time": 119.7,      # 添加了噪声
    "visual_score": 0.84      # 添加了噪声
}
```

#### 第2层：SRPG重构
```python
# 特征编码
encoded = encoder(noisy_data)  # [0.82, 0.15, 0.67, ...]

# 匿名化ID
pseudonym = hash("stu_001")  # "pseudo_abc123"

# 输出保护特征
protected = ProtectedFeatures(
    student_pseudonym="pseudo_abc123",
    reconstructed_features={"latent_0": 0.81, ...}
)
```

#### 第3层：RBAC控制
```python
# 当前状态: TUTORING (AG3辅导中)
rbac.transition_state(TUTORING)

# AG3请求访问
permission = rbac.grant_permission(
    agent_id=AG3_TUTOR,
    resource_id="pseudo_abc123",
    privacy_level=RECONSTRUCTED
)

# 检查：AG3只能访问 recent_errors 字段
allowed_fields = ["recent_errors", "style_tag"]
```

#### 第4层：GNN监控
```python
# 监控交互
allowed, reason = gnn_guard.monitor_interaction(
    src="A1",
    dst="privacy_gateway",
    interaction_type="data_transfer"
)

# 检查：是否横向连接
if is_lateral_connection(src, dst):
    return False, "检测到非法横向连接"

# 定期GNN检测
if interaction_count % 10 == 0:
    anomaly_scores = gnn_detector(graph)
    if anomaly_scores.any() > threshold:
        quarantine(anomalous_nodes)
```

---

## 🎯 防护效果对比

### 单层防护 vs 四层防护

| 攻击类型 | 无防护 | 仅LDP | LDP+SRPG | +RBAC | +GNN |
|---------|--------|-------|----------|-------|------|
| 直接窃取原始数据 | ✅ | ❌ | ❌ | ❌ | ❌ |
| 反推噪声数据 | ✅ | ⚠️ | ❌ | ❌ | ❌ |
| 越权访问数据 | ✅ | ✅ | ✅ | ❌ | ❌ |
| Prompt注入攻击 | ✅ | ✅ | ✅ | ✅ | ❌ |
| 横向连接攻击 | ✅ | ✅ | ✅ | ✅ | ❌ |
| 大规模流量攻击 | ✅ | ✅ | ✅ | ⚠️ | ❌ |

**图例**: ✅ 易受攻击, ⚠️ 部分防护, ❌ 有效防护

---

## 📊 性能与开销

### 计算开销

| 层级 | 机制 | CPU开销 | 内存开销 | 延迟 |
|-----|------|---------|----------|------|
| LDP | 噪声生成 | <1ms | 可忽略 | <1ms |
| SRPG | 神经网络推理 | ~10ms | ~50MB | ~10ms |
| RBAC | 权限检查 | <1ms | ~1MB (Redis) | <1ms |
| GNN | 图检测 | ~50ms (每10次) | ~100MB | ~5ms平均 |
| **总计** | - | **<65ms** | **~150MB** | **<20ms** |

### 隐私损失

| 层级 | 隐私预算消耗 | 累计消耗 |
|-----|-------------|----------|
| LDP | epsilon/10 | 0.1 |
| SRPG | epsilon/10 | 0.2 |
| RBAC | 0 | 0.2 |
| GNN | 0 | 0.2 |

**总隐私预算**: epsilon = 1.0 (可配置)

---

## 🛠️ 如何修改和扩展

### 修改LDP参数
```python
# gateway/privacy_engine.py
class SRPGEngine:
    def __init__(self):
        # 调整epsilon值
        self.epsilon = 0.5  # 更强隐私保护（数据质量下降）
        # 或
        self.epsilon = 2.0  # 更弱隐私保护（数据质量更好）
```

### 改进SRPG模型
```python
# 使用Transformer替代MLP
from transformers import BertModel

class TransformerReconstructionHead(nn.Module):
    def __init__(self):
        self.encoder = BertModel.from_pretrained('bert-base-uncased')
        # ...
```

### 扩展RBAC规则
```python
# gateway/rbac_manager.py
data_view_rules = {
    # 添加新的智能体
    AG6_ANALYTICS: ["aggregated_stats", "trends"],

    # 更细粒度的字段控制
    AG3_TUTOR: {
        "recent_errors": {"max_rows": 10},  # 最多看10条
        "weak_kcs": {"max_count": 5}        # 最多看5个
    }
}
```

### 增强GNN检测
```python
# gateway/gnn_guard.py
# 添加更多异常特征
node_features = [
    node_type,
    domain,
    message_frequency,
    avg_data_size,
    time_since_last_msg,
    failed_attempts,
    # 添加更多特征...
    reputation_score,
    trust_level
]
```

---

## 📈 监控和审计

### 审计日志

每层都有详细的审计日志：

```python
# LDP: 隐私预算使用
ldp_log = {
    "timestamp": 1234567890,
    "student_id": "pseudo_abc123",
    "epsilon_used": 0.1,
    "budget_remaining": 0.9
}

# RBAC: 权限授予
rbac_log = {
    "timestamp": 1234567890,
    "agent_id": "AG3_TUTOR",
    "resource_id": "pseudo_abc123",
    "action": "grant",
    "expires_at": 1234568190
}

# GNN: 异常检测
gnn_log = {
    "timestamp": 1234567890,
    "type": "lateral_connection",
    "src": "AG2",
    "dst": "AG3",
    "severity": "critical",
    "action": "quarantine"
}
```

### 可视化仪表板

教师端提供实时监控：
- GNN拓扑图
- 隐私预算使用情况
- 活跃权限列表
- 被隔离节点列表

---

## 🧪 测试验证

### 单元测试
```bash
# 测试LDP
pytest tests/test_ldp.py

# 测试SRPG
pytest tests/test_srpg.py

# 测试RBAC
pytest tests/test_rbac.py

# 测试GNN
pytest tests/test_gnn.py
```

### 集成测试
```bash
# 完整流程测试
python3 deploy/test_message_flow.py
```

### 压力测试
```bash
# 模拟攻击场景
python3 tests/attack_simulation.py
```

---

## 📚 相关文档

### 核心文档
- 📖 [LDP+SRPG+RBAC详解](docs/PRIVACY_MECHANISMS_EXPLAINED.md)
- 📖 [GNN防护详解](docs/GNN_GUARD_EXPLAINED.md)
- 📖 [API文档](docs/API_REFERENCE.md)
- 📖 [部署指南](docs/DEPLOYMENT_GUIDE.md)

### 代码文件
- 🔧 `gateway/privacy_engine.py` (LDP + SRPG)
- 🔧 `gateway/rbac_manager.py` (RBAC)
- 🔧 `gateway/gnn_guard.py` (GNN)
- 🔧 `gateway/router.py` (网关路由)

---

## 🎓 最佳实践

### 开发建议
1. **渐进式部署**: 先部署LDP，逐步添加其他层
2. **参数调优**: 根据实际场景调整epsilon、阈值等参数
3. **监控告警**: 设置异常告警，及时响应
4. **定期审计**: 检查审计日志，发现潜在问题

### 安全建议
1. **最小权限**: 智能体只授予必需的最小权限
2. **临时权限**: 权限令牌设置较短过期时间
3. **隔离响应**: 检测到异常立即隔离节点
4. **纵深防御**: 依赖多层防护，而非单层

---

## 🔮 未来改进方向

### 短期（1-3个月）
- [ ] 添加联邦学习支持
- [ ] 实现同态加密
- [ ] 优化GNN模型性能
- [ ] 添加更多异常检测特征

### 中期（3-6个月）
- [ ] 支持多租户隔离
- [ ] 实现可信执行环境（TEE）
- [ ] 添加隐私预算拍卖机制
- [ ] 支持差分隐私合成数据

### 长期（6-12个月）
- [ ] 零知识证明
- [ ] 安全多方计算（MPC）
- [ ] 区块链审计追踪
- [ ] 自适应隐私保护

---

## 📞 联系方式

- **GitHub**: https://github.com/guoshaung/edu-mas-privacy
- **Email**: 3515394691@qq.com
- **Issues**: https://github.com/guoshaung/edu-mas-privacy/issues

---

**🔒 四重防护，纵深防御，零信任架构！**

**每个层级都能独立防护，多层协同形成坚不可摧的隐私保护体系！**
