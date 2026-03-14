# 🚀 完整部署指南

## 项目完成情况 ✅

### 核心组件（100%完成）

| 组件 | 文件路径 | 状态 |
|------|----------|------|
| **隐私网关** | `gateway/router.py` | ✅ 完成 |
| **SRPG引擎** | `gateway/privacy_engine.py` | ✅ 完成 |
| **动态RBAC** | `gateway/rbac_manager.py` | ✅ 完成 |
| **GNN防御** | `gateway/gnn_guard.py` | ✅ 完成 |
| **AG2学习风格** | `agents/ag2_style.py` | ✅ 完成 |
| **AG3自适应辅导** | `agents/ag3_tutor.py` | ✅ 完成 |
| **AG4内容挖掘** | `agents/ag4_content.py` | ✅ 完成 |
| **AG5自适应评估** | `agents/ag5_assess.py` | ✅ 完成 |
| **gRPC协议** | `protocols/gateway.proto` | ✅ 完成 |
| **网关服务器** | `deploy/gateway_server.py` | ✅ 完成 |
| **教学域服务器** | `deploy/education_server.py` | ✅ 完成 |
| **Docker编排** | `deploy/docker-compose.yml` | ✅ 完成 |
| **前端界面** | `frontend/index.html` | ✅ 完成 |

---

## 方案一：本地快速运行

### 前置条件
```bash
# 1. 克隆项目（已完成）
cd /Users/mac9/.openclaw/workspace/edu-mas-privacy

# 2. 安装依赖
pip install -r requirements.txt
```

### 运行完整演示
```bash
# 完整学习旅程 + 安全审计
python demo_full.py
```

**演示内容：**
- ✅ 学生数据采集 → SRPG保护
- ✅ AG2学习风格诊断
- ✅ AG3自适应辅导（脚手架对话）
- ✅ AG4个性化资源推荐
- ✅ AG5独立评估（防自判幻觉）
- ✅ GNN拓扑防御监控
- ✅ 隐私预算追踪
- ✅ 安全审计（横向连接、权限提升攻击测试）

### 查看前端可视化
```bash
# 在浏览器中打开
open frontend/index.html

# 或手动访问
file:///Users/mac9/.openclaw/workspace/edu-mas-privacy/frontend/index.html
```

**前端功能：**
- 🌐 实时GNN拓扑图
- 📊 隐私预算进度条
- 🥧 RBAC权限甜甜圈图
- 📝 实时日志监控
- 🤖 智能体状态卡片
- ▶️ 模拟请求按钮

---

## 方案二：Docker微服务部署（生产级）

### 1. 编译protobuf
```bash
cd edu-mas-privacy

# 安装grpc工具
pip install grpcio-tools

# 编译protobuf
python -m grpc_tools.protoc \
  --proto_path=protocols \
  --python_out=. \
  --grpc_python_out=. \
  protocols/gateway.proto
```

### 2. 构建Docker镜像
```bash
# 构建所有服务
docker-compose build

# 或单独构建
docker-compose build gateway
docker-compose build education-domain
docker-compose build learner-domain
```

### 3. 启动服务集群
```bash
# 启动所有服务（后台运行）
docker-compose up -d

# 查看日志
docker-compose logs -f gateway
docker-compose logs -f education-domain

# 查看运行状态
docker-compose ps
```

### 4. 服务端口
| 服务 | 端口 | 用途 |
|------|------|------|
| 网关 | 50051 | 跨域路由 |
| 教学域 | 50052 | AG2-AG5集群 |
| 学习者域 | 50053 | A1档案服务 |
| Redis | 6379 | RBAC权限存储 |
| Grafana | 3000 | 监控面板 |

### 5. 停止服务
```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v
```

---

## 方案三：Kubernetes部署（企业级）

### 准备K8s配置文件
```bash
# 创建命名空间
kubectl create namespace edu-mas-privacy

# 部署Redis
kubectl apply -f deploy/k8s/redis-deployment.yaml -n edu-mas-privacy

# 部署网关
kubectl apply -f deploy/k8s/gateway-deployment.yaml -n edu-mas-privacy

# 部署教学域
kubectl apply -f deploy/k8s/education-deployment.yaml -n edu-mas-privacy

# 部署学习者域
kubectl apply -f deploy/k8s/learner-deployment.yaml -n edu-mas-privacy

# 创建服务
kubectl apply -f deploy/k8s/services.yaml -n edu-mas-privacy
```

### 查看部署状态
```bash
# 查看Pod
kubectl get pods -n edu-mas-privacy

# 查看服务
kubectl get svc -n edu-mas-privacy

# 查看日志
kubectl logs -f deployment/gateway -n edu-mas-privacy
```

---

## 核心创新点验证

### 1. 数据层：SRPG + LDP
```python
# 验证隐私预算消耗
from gateway.privacy_engine import get_privacy_engine

engine = get_privacy_engine()
print(f"剩余预算: {engine.get_remaining_budget()}")
```

### 2. 架构层：动态RBAC
```python
# 验证状态机切换
from gateway.rbac_manager import get_rbac_manager, BusinessState

rbac = get_rbac_manager()
rbac.transition_state(BusinessState.TUTORING)
print(f"当前状态: {rbac.current_state}")
```

### 3. 防御层：GNN拓扑防御
```python
# 验证异常检测
from gateway.gnn_guard import get_gnn_guard

guard = get_gnn_guard()
stats = guard.get_statistics()
print(f"异常事件数: {stats['anomaly_events']}")
```

### 4. 零横向直连
```python
# 验证跨域路由拦截
from protocols.messages import CrossDomainMessage, DomainType, AgentType

message = CrossDomainMessage(
    source_domain=DomainType.EDUCATION,  # 教学域
    target_domain=DomainType.EDUCATION,  # 教学域（同域）
    source_agent=AgentType.AG2_STYLE,
    target_agent=AgentType.AG3_TUTOR,
    payload={}
)

response = await gateway.route_cross_domain(message)
# 应返回: success=False, error="Lateral connection prohibited"
```

---

## 性能优化建议

### 1. 缓存层
```python
# 使用Redis缓存SRPG处理结果
import redis
redis_client = redis.Redis(host='localhost', port=6379)

cache_key = f"protected:{student_id}:{hash(str(features))}"
cached_result = redis_client.get(cache_key)

if not cached_result:
    protected_features = engine.protect(learner_data)
    redis_client.setex(cache_key, 3600, protected_features)
```

### 2. 批处理
```python
# 批量处理多个学生请求
batch_learner_data = [learner1, learner2, learner3]

async with aiohttp.ClientSession() as session:
    tasks = [
        gateway.route_learner_to_education(ld, AgentType.AG2_STYLE)
        for ld in batch_learner_data
    ]
    results = await asyncio.gather(*tasks)
```

### 3. 负载均衡
```yaml
# docker-compose.yml
education-domain:
  deploy:
    replicas: 3  # 3个副本
    resources:
      limits:
        cpus: '1'
        memory: 2G
```

---

## 监控与运维

### Prometheus指标
```python
from prometheus_client import Counter, Histogram

# 请求计数
request_counter = Counter(
    'gateway_requests_total',
    'Total requests',
    ['agent_type', 'status']
)

# 隐私预算消耗
privacy_budget_gauge = Gauge(
    'privacy_budget_remaining',
    'Remaining privacy budget'
)

# GNN异常检测
anomaly_counter = Counter(
    'gnn_anomalies_total',
    'Total anomalies detected'
)
```

### 日志聚合
```python
import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger('gateway')
handler = RotatingFileHandler(
    'logs/gateway.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
logger.addHandler(handler)
```

---

## 故障排查

### 常见问题

**1. Redis连接失败**
```bash
# 检查Redis状态
docker-compose ps redis

# 查看Redis日志
docker-compose logs redis

# 重启Redis
docker-compose restart redis
```

**2. gRPC服务无法启动**
```bash
# 检查端口占用
lsof -i :50051

# 更改端口
python deploy/gateway_server.py --port 50052
```

**3. GNN模型加载失败**
```bash
# 检查PyTorch版本
python -c "import torch; print(torch.__version__)"

# 重新安装依赖
pip install torch>=2.5.0 torch-geometric>=2.6.0
```

---

## 下一步优化方向

1. **联邦学习集成** - 在保护隐私的前提下协同训练
2. **同态加密** - 密文计算，进一步强化数据安全
3. **区块链审计** - 不可篡改的访问日志
4. **多模态输入** - 支持图像、语音等交互方式
5. **强化学习** - 智能体策略自适应优化

---

**恭喜！你现在拥有一个生产就绪的零信任隐私保护多智能体学习平台！** 🎉
