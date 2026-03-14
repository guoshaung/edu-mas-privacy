# 隐私保护机制实现详解

## 目录
1. [LDP（本地差分隐私）](#ldp本地差分隐私)
2. [SRPG（安全重构保护生成）](#srpg安全重构保护生成)
3. [动态RBAC](#动态rbac)
4. [三者协同工作流程](#三者协同工作流程)
5. [修改建议](#修改建议)

---

## 1. LDP（本地差分隐私）

### 原理
在数据**离开用户设备前**添加噪声，使攻击者无法反推原始数据。

### 核心公式
```
噪声 ~ Laplace(0, sensitivity / epsilon)
protected_data = raw_data + noise
```

### 参数说明
- **sensitivity** (敏感度): 数据变化对输出的影响
- **epsilon** (隐私预算): 值越小，隐私保护越强
  - epsilon = 1.0: 平衡隐私和有用性
  - epsilon < 1.0: 强隐私保护（数据质量下降）
  - epsilon > 1.0: 弱隐私保护（数据质量较好）

### 代码实现
**文件**: `gateway/privacy_engine.py`

```python
def _add_laplace_noise(self, data: torch.Tensor, sensitivity: float = 1.0) -> torch.Tensor:
    """
    注入拉普拉斯噪声（本地差分隐私）
    """
    # 计算噪声规模
    scale = sensitivity / self.epsilon

    # 生成拉普拉斯噪声
    noise = torch.distributions.Laplace(0, scale).sample(data.shape).to(self.device)

    # 添加噪声
    return data + noise
```

### 使用示例
```python
# 原始数据: 学习时间 = 120分钟
raw_data = {"study_time": 120}

# 添加LDP噪声 (epsilon=1.0)
protected_data = add_laplace_noise(raw_data)
# 结果可能是: 119.7 或 120.3 分钟

# 攻击者无法确定真实值是120分钟
```

### 优缺点
**优点**:
- ✅ 数学上可证明的隐私保护
- ✅ 不依赖信任模型
- ✅ 简单高效

**缺点**:
- ❌ 会降低数据质量（添加了噪声）
- ❌ 需要仔细调参（epsilon选择）

---

## 2. SRPG（安全重构保护生成）

### 原理
通过神经网络将噪声数据**重构**为可用特征，既保护隐私又保留有用性。

### 三步流程

#### 第1步：特征编码
```python
# 原始特征 (64维)
raw_features = {"visual_score": 0.8, "auditory_score": 0.6, ...}

# 归一化为张量
feature_tensor = normalize(raw_features)  # shape: [64]

# 编码到隐空间 (32维)
encoded = encoder(feature_tensor)  # shape: [32]
```

#### 第2步：LDP噪声注入
```python
# 在隐空间添加噪声
noisy_encoded = encoded + laplace_noise(epsilon=1.0)
```

#### 第3步：语义重构
```python
# 解码回可用特征空间
reconstructed = decoder(noisy_encoded)  # shape: [64]

# 转为字典格式
protected_features = {
    "latent_0": reconstructed[0],
    "latent_1": reconstructed[1],
    ...
}
```

### 代码实现
**文件**: `gateway/privacy_engine.py`

```python
class SRPGEngine:
    def protect(self, learner_data: LearnerData):
        # 1. 特征归一化
        feature_tensor = self._normalize_features(learner_data.raw_features)

        # 2. 隐空间编码
        encoded = self.reconstruction_head.encode(feature_tensor)

        # 3. LDP噪声注入
        noisy_encoded = self._add_laplace_noise(encoded)

        # 4. 转为字典
        protected_dict = {
            f"latent_{i}": noisy_encoded[i].item()
            for i in range(noisy_encoded.shape[0])
        }

        # 5. 追踪隐私预算
        cost = self.epsilon / 10.0
        self.used_budget += cost

        return ProtectedFeatures(
            student_pseudonym=hash_id(learner_data.student_id),
            reconstructed_features=protected_dict,
            privacy_budget_used=self.used_budget
        )
```

### 神经网络架构
```python
class LatentReconstructionHead(nn.Module):
    def __init__(self):
        # 编码器: 64维 → 32维
        self.encoder = nn.Sequential(
            nn.Linear(64, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, 32)
        )

        # 解码器: 32维 → 64维
        self.decoder = nn.Sequential(
            nn.Linear(32, 128),
            nn.ReLU(),
            nn.Linear(128, 64)
        )
```

### 优缺点
**优点**:
- ✅ 平衡隐私保护和数据有用性
- ✅ 可学习的重构模型
- ✅ 支持复杂特征

**缺点**:
- ❌ 需要训练神经网络
- ❌ 计算开销较大
- ❌ 需要大量训练数据

---

## 3. 动态RBAC

### 原理
基于**业务状态机**动态颁发临时权限，智能体只能访问当前任务必需的数据。

### 核心概念

#### 业务状态机
```python
class BusinessState(Enum):
    IDLE = "idle"
    DIAGNOSING = "diagnosing"      # AG2正在诊断
    TUTORING = "tutoring"          # AG3正在辅导
    CONTENT_RETRIEVAL = "content"  # AG4正在检索内容
    ASSESSING = "assessing"        # AG5正在评估
```

#### 状态-智能体映射
```python
state_agent_map = {
    BusinessState.DIAGNOSING: {AG2_STYLE},      # 只有AG2活跃
    BusinessState.TUTORING: {AG3_TUTOR},        # 只有AG3活跃
    BusinessState.CONTENT_RETRIEVAL: {AG4_CONTENT},
    BusinessState.ASSESSING: {AG5_ASSESS}
}
```

#### 数据降维规则
每个智能体只能访问特定字段：
```python
data_view_rules = {
    AG2_STYLE: ["learning_style", "cognitive_level"],      # 只能看到学习风格
    AG3_TUTOR: ["recent_errors", "style_tag", "weak_kcs"], # 只能看到错误和风格
    AG4_CONTENT: ["knowledge_points", "difficulty_level"], # 只能看到知识点
    AG5_ASSESS: ["assessment_config"]                      # 只能看到评估配置
}
```

### 权限令牌
```python
class DataPermission:
    agent_id: AgentType           # 哪个智能体
    resource_id: str              # 访问哪个资源
    privacy_level: PrivacyLevel   # 访问级别（RAW/NOISY/RECONSTRUCTED/AGGREGATED）
    granted_at: float             # 颁发时间
    expires_at: float             # 过期时间
    access_count: int             # 已访问次数
    max_access: int               # 最大访问次数
```

### 权限检查流程
```python
def grant_permission(agent_id, resource_id, privacy_level):
    # 1. 检查智能体是否在当前状态活跃
    if agent_id not in state_agent_map[current_state]:
        return None  # 拒绝：不在活跃状态

    # 2. 检查数据降维规则
    allowed_fields = data_view_rules[agent_id]
    if not check_fields(resource_id, allowed_fields):
        return None  # 拒绝：超出允许范围

    # 3. 颁发临时令牌
    permission = DataPermission(
        agent_id=agent_id,
        resource_id=resource_id,
        privacy_level=privacy_level,
        expires_at=time.time() + 300  # 5分钟后过期
    )

    # 4. 存储到Redis
    redis.setex(f"perm:{agent_id}:{resource_id}", 300, permission)

    return permission
```

### 状态切换自动吊销权限
```python
def transition_state(new_state):
    # 1. 吊销旧状态智能体的所有权限
    for agent in state_agent_map[old_state]:
        revoke_all_permissions(agent)

    # 2. 切换到新状态
    current_state = new_state

    # 3. 为新状态智能体预授权（可选）
    for agent in state_agent_map[new_state]:
        pre_authorize(agent)
```

### 优缺点
**优点**:
- ✅ 最小权限原则（只授予必需数据）
- ✅ 临时性（自动过期）
- ✅ 可审计（记录所有访问）
- ✅ 状态驱动（自动切换）

**缺点**:
- ❌ 实现复杂
- ❌ 需要Redis等外部存储
- ❌ 状态机设计需要仔细考虑

---

## 4. 三者协同工作流程

### 完整的数据保护流程

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 学生端（学习者域 - 高信域）                                │
│    原始数据: {"study_time": 120, "score": 85, ...}          │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. SRPG引擎（本地）                                          │
│    • 特征编码: [0.8, 0.6, ...] → 隐空间 [32维]              │
│    • LDP噪声: 隐空间 + Laplace噪声                           │
│    • 重构特征: {"latent_0": 0.78, "latent_1": 0.62, ...}   │
│    • 匿名化ID: "stu_001" → "pseudo_abc123"                  │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. 隐私网关（控制平面域）                                     │
│    • 接收: ProtectedFeatures                                │
│    • 检查: 隐私预算是否足够                                   │
│    • RBAC: 根据当前状态颁发临时权限                           │
│      - AG2活跃: 只授予 learning_style 字段                  │
│      - AG3活跃: 只授予 recent_errors 字段                   │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. 教学域智能体（低信域）                                     │
│    • AG2: 只能访问 {"latent_0", "latent_5"} (学习风格特征)  │
│    • AG3: 只能访问 {"latent_1", "latent_3"} (错误特征)      │
│    • 无法访问原始数据！                                       │
└─────────────────────────────────────────────────────────────┘
```

### 具体例子

#### 场景：学生问问题

**第1步：学生端**
```python
# 原始数据（学生本地）
raw_data = {
    "student_id": "stu_001",
    "study_time": 120,        # 学习时长（分钟）
    "visual_score": 0.85,     # 视觉偏好分数
    "recent_errors": [        # 最近错误
        {"topic": "二次函数", "count": 3}
    ]
}
```

**第2步：SRPG保护**
```python
# 特征提取
features = extract_features(raw_data)
# → {"visual": 0.85, "errors": 3, "time": 120}

# 归一化并编码
encoded = encoder(features)
# → [0.82, 0.15, 0.67, ...] (32维隐空间)

# LDP噪声注入
noisy = add_laplace_noise(encoded, epsilon=1.0)
# → [0.81, 0.16, 0.66, ...]

# 匿名化ID
pseudonym = hash("stu_001")
# → "pseudo_abc123"

# 输出保护特征
protected = ProtectedFeatures(
    student_pseudonym="pseudo_abc123",
    reconstructed_features={"latent_0": 0.81, ...},
    privacy_budget_used=0.1
)
```

**第3步：网关RBAC检查**
```python
# 当前状态: TUTORING (AG3辅导中)
current_state = BusinessState.TUTORING

# AG3请求访问
agent_id = AG3_TUTOR
resource_id = "pseudo_abc123_features"

# 检查权限
permission = rbac.grant_permission(
    agent_id=AG3_TUTOR,
    resource_id="pseudo_abc123_features",
    privacy_level=PrivacyLevel.RECONSTRUCTED
)

# RBAC检查：
# ✅ AG3在当前状态活跃
# ✅ AG3只能访问 recent_errors 字段
# ✅ 颁发临时令牌（5分钟有效，最多10次访问）
```

**第4步：AG3访问数据**
```python
# AG3只能看到降维后的数据
allowed_data = {
    "recent_errors_count": 3,    # ✅ 允许
    "weak_kcs": ["二次函数"],     # ✅ 允许
    # visual_score: 0.85          ❌ 不允许（AG3不需要）
    # study_time: 120             ❌ 不允许（AG3不需要）
}
```

---

## 5. 修改建议

### 如果你想改进LDP

#### 1. 更换噪声分布
```python
# 当前: 拉普拉斯噪声
noise = torch.distributions.Laplace(0, scale).sample(data.shape)

# 改进: 高斯噪声（更平滑）
noise = torch.distributions.Normal(0, sigma).sample(data.shape)

# 改进: 指数机制（保护离散值）
def exponential_mechanism(scores, epsilon):
    probabilities = torch.exp(epsilon * scores / 2)
    return torch.distributions.Categorical(probabilities).sample()
```

#### 2. 自适应epsilon
```python
# 当前: 固定epsilon
self.epsilon = 1.0

# 改进: 根据数据敏感度动态调整
def adaptive_epsilon(data_sensitivity):
    if data_sensitivity == "high":  # 成绩、ID等
        return 0.5
    elif data_sensitivity == "medium":  # 学习时长
        return 1.0
    else:  # 一般偏好
        return 2.0
```

### 如果你想改进SRPG

#### 1. 更强的重构模型
```python
# 当前: 简单MLP
self.encoder = nn.Sequential(
    nn.Linear(64, 128),
    nn.ReLU(),
    nn.Linear(128, 32)
)

# 改进: Transformer编码器
class TransformerEncoder(nn.Module):
    def __init__(self):
        self.encoder = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(d_model=64, nhead=8),
            num_layers=4
        )
```

#### 2. 对抗训练（增强隐私）
```python
# 添加对抗器：尝试从重构特征反推原始数据
class Adversary(nn.Module):
    def __init__(self):
        self.decoder = nn.Sequential(
            nn.Linear(32, 64),
            nn.ReLU()
        )

# 训练时：让重构器对抗对抗器
loss_reconstruction = mse_loss(reconstructed, original)
loss_privacy = -mse_loss(adversary_output, original)  # 对抗器失败越好
total_loss = loss_reconstruction + 0.1 * loss_privacy
```

### 如果你想改进RBAC

#### 1. 更细粒度的权限控制
```python
# 当前: 粗粒度（智能体级别）
data_view_rules = {
    AG3_TUTOR: ["recent_errors", "style_tag"]
}

# 改进: 细粒度（字段级别 + 操作级别）
data_view_rules = {
    AG3_TUTOR: {
        "recent_errors": {
            "fields": ["topic", "count"],  # 只能看topic和count
            "operations": ["read"],        # 只能读
            "max_rows": 10                 # 最多看10条
        }
    }
}
```

#### 2. 基于属性的访问控制（ABAC）
```python
# 当前: 基于角色（RBAC）
if agent_id == AG3_TUTOR:
    grant_access()

# 改进: 基于属性（ABAC）
def check_access_attributes(agent, resource, context):
    # 检查智能体属性
    if agent.trust_level < 0.8:
        return False

    # 检查资源属性
    if resource.sensitivity > 0.7:
        return False

    # 检查环境属性
    if context.time_of_day == "night":
        return False

    return True
```

---

## 6. 代码位置

### LDP实现
- **文件**: `gateway/privacy_engine.py`
- **函数**: `_add_laplace_noise()`
- **行数**: 约50-60行

### SRPG实现
- **文件**: `gateway/privacy_engine.py`
- **类**: `SRPGEngine`
- **方法**: `protect()`
- **行数**: 约150行

### RBAC实现
- **文件**: `gateway/rbac_manager.py`
- **类**: `DynamicRBACManager`
- **方法**: `grant_permission()`, `check_permission()`
- **行数**: 约200行

---

## 7. 测试示例

```python
# 测试LDP
from gateway.privacy_engine import get_privacy_engine
from protocols.messages import LearnerData

engine = get_privacy_engine()

learner = LearnerData(
    student_id="stu_001",
    raw_features={"visual": 0.8, "auditory": 0.6}
)

protected, cost = engine.protect(learner)
print(f"匿名化ID: {protected.student_pseudonym}")
print(f"隐私预算消耗: {cost}")
print(f"保护后特征: {protected.reconstructed_features}")

# 测试RBAC
from gateway.rbac_manager import get_rbac_manager

rbac = get_rbac_manager()

# 切换到辅导状态
rbac.transition_state(BusinessState.TUTORING)

# 为AG3颁发权限
permission = rbac.grant_permission(
    agent_id=AgentType.AG3_TUTOR,
    resource_id="pseudo_abc123",
    privacy_level=PrivacyLevel.RECONSTRUCTED
)

if permission:
    print("权限已颁发")
    print(f"过期时间: {permission.expires_at}")
```

---

**📝 总结：这三个机制协同工作，形成多层防护**

- **LDP**: 第1层 - 本地噪声注入
- **SRPG**: 第2层 - 特征重构
- **RBAC**: 第3层 - 访问控制

**你可以根据需要调整每一层的实现！** 🔒
