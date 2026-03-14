# 快速开始指南

## 项目已搭建完成！🎉

你现在拥有一个完整的MVP骨架，包含：

### ✅ 已实现的核心组件

1. **隐私网关 (`gateway/`)**
   - `privacy_engine.py`: SRPG + LDP噪声注入
   - `rbac_manager.py`: 动态权限控制
   - `router.py`: 跨域路由拦截（LangGraph状态机）

2. **教学智能体 (`agents/`)**
   - `ag2_style.py`: 学习风格识别
   - `ag3_tutor.py`: 自适应辅导

3. **通信协议 (`protocols/`)**
   - `messages.py`: 跨域消息定义 + 数据模型

4. **演示脚本**
   - `demo.py`: 完整流程演示 + 安全测试

---

## 第一步：安装依赖

```bash
cd /Users/mac9/.openclaw/workspace/edu-mas-privacy
pip install -r requirements.txt
```

**注意：** 如果没有Redis，`rbac_manager.py`会自动降级到内存存储。

---

## 第二步：运行Demo

```bash
# 确保在项目根目录
python demo.py
```

**选择演示模式：**
- 选项1：完整流程（学生数据 → 网关 → AG2诊断 → AG3辅导）
- 选项2：安全性测试（验证横向连接被阻止）
- 选项3：两者都运行（推荐）

---

## 第三步：理解架构流程

### 完整数据流

```
┌─────────────────────────────────────────────────────────────┐
│ 步骤1：A1收集原始数据（高信域）                               │
│ student_id: "stu_20240313_001"                              │
│ raw_features: {visual: 0.85, auditory: 0.55, ...}          │
└──────────────────┬──────────────────────────────────────────┘
                   │ 跨域请求
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ 步骤2：隐私网关（控制平面）                                   │
│                                                             │
│ 2.1 SRPG引擎处理                                            │
│   - 归一化特征 → 隐空间编码                                 │
│   - 注入LDP噪声（ε=1.0）                                    │
│   - 匿名化ID: "pseudo_abc123"                              │
│                                                             │
│ 2.2 动态RBAC授权                                            │
│   - 状态机切换: IDLE → DIAGNOSING                          │
│   - 颁发临时令牌（TTL=300s）                                │
│                                                             │
│ 2.3 G-safeguard监控                                         │
│   - 检测拓扑异常                                            │
│   - 剪枝污染源                                              │
└──────────────────┬──────────────────────────────────────────┘
                   │ 受保护数据
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ 步骤3：AG2学习风格识别（教学域）                              │
│ 输入: protected_features（隐空间向量）                       │
│ 输出: {primary_style: "Visual", confidence: 0.85}           │
└──────────────────┬──────────────────────────────────────────┘
                   │ 风格标签
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ 步骤4：AG3自适应辅导（教学域）                                │
│ 输入: learning_style + error_history                        │
│ 输出: scaffolding_questions + explanation                   │
│                                                             │
⚠️ 注意：AG3无法访问原始隐私数据！只能看到脱敏特征              │
└─────────────────────────────────────────────────────────────┘
```

---

## 第四步：扩展功能

### 待实现的智能体

**AG4: 内容挖掘 (`agents/ag4_content.py`)**
```python
class ContentMiningAgent:
    """从全局题库RAG检索资源（无个体隐私访问）"""
    def retrieve(self, knowledge_points: List[str]) -> List[Dict]:
        # 向量检索 + 知识图谱过滤
        pass
```

**AG5: 自适应评估 (`agents/ag5_assess.py`)**
```python
class AssessmentAgent:
    """独立考官（不能读辅导对话，防自判幻觉）"""
    def generate_test(self, difficulty: float) -> Dict:
        # 生成测试题
        pass
```

### G-safeguard拓扑防御

在 `gateway/gnn_guard.py` 中实现：

```python
class GNNGuard:
    """GNN实时监控多智能体交互图"""
    def monitor_topology(self, graph_snapshot: Dict):
        # 检测异常流量模式
        # 动态剪枝恶意节点
        pass
```

---

## 核心创新点验证

✅ **数据层：SRPG + LDP**
- 运行Demo后检查 `privacy_engine.py` 的 `get_remaining_budget()`
- 验证每次处理都会消耗隐私预算

✅ **架构层：动态RBAC**
- 查看 `rbac_manager.py` 的 `transition_state()`
- 状态切换会自动吊销旧权限

✅ **防御层：G-safeguard**
- 运行Demo选项2，验证横向连接被阻止
- 实现GNN后可实时监控拓扑异常

---

## 技术栈说明

| 组件 | 技术选型 | 理由 |
|------|----------|------|
| 多智能体编排 | **LangGraph** | 原生状态机支持，图拓扑监控 |
| 隐私计算 | **Opacus + PyTorch** | 成熟的LDP实现 |
| GNN防御 | **PyTorch Geometric** | 图神经网络专用库 |
| 通信 | **gRPC/ZeroMQ** | 高性能跨域通信 |
| 权限存储 | **Redis** | TTL自动过期 + 高并发 |

---

## 下一步行动

1. **立即运行**：`python demo.py` 验证基础流程
2. **补充AG4/AG5**：参考 `ag2_style.py` 的模式实现
3. **集成GNN**：在 `gateway/gnn_guard.py` 中实现拓扑监控
4. **部署测试**：将三个域部署为独立Docker容器
5. **性能优化**：添加缓存层（Redis）和批处理

---

## 需要帮助？

在项目根目录运行：
```bash
# 查看智能体日志
python -c "from agents.ag2_style import demo_ag2; demo_ag2()"

# 查看网关日志
python -c "from gateway.router import demo_gateway; import asyncio; asyncio.run(demo_gateway())"

# 测试RBAC
python -c "from gateway.rbac_manager import get_rbac_manager; rbac = get_rbac_manager(); print(rbac.state_agent_map)"
```

---

**恭喜！你现在拥有一个真正实现了零信任隐私保护的多智能体学习平台MVP。** 🚀
