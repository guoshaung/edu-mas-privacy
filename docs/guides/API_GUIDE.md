# API 使用说明

## 🤖 智能体API说明

### 1. 本项目使用的API

#### LangChain API（用于智能体实现）

本项目**确实使用LangChain的API**来实现智能体功能，主要包括：

```python
# AG2, AG3, AG4, AG5 都使用了以下LangChain API：
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.memory import ConversationBufferMemory
```

**具体使用的API**：
- `ChatOpenAI` - OpenAI的GPT模型接口
- `ChatPromptTemplate` - 提示词模板
- `ConversationBufferMemory` - 对话记忆管理
- `OpenAIEmbeddings` - 文本嵌入向量（用于RAG）

### 2. API调用流程

```
用户请求
    ↓
前端界面 (interactive.html)
    ↓
JavaScript (模拟或真实调用)
    ↓
智能体 Python 代码
    ↓
LangChain API
    ↓
OpenAI GPT API
    ↓
返回结果
```

### 3. 需要的API密钥

要运行完整的智能体功能，需要配置OpenAI API密钥：

```bash
# 设置环境变量
export OPENAI_API_KEY="your-api-key-here"

# 或创建 .env 文件
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

---

## 📡 前端交互方式

### 方式一：纯前端模拟（当前实现）

**文件**: `frontend/interactive.html`

**特点**：
- ✅ 无需后端服务
- ✅ 立即可用
- ✅ JavaScript模拟所有API调用
- ✅ 展示完整交互流程

**使用方法**：
```bash
# 在浏览器中打开
open frontend/interactive.html
```

---

### 方式二：真实API调用（需要配置）

#### 步骤1: 配置API密钥

创建 `frontend/config.js`：
```javascript
const API_CONFIG = {
    // OpenAI API配置
    openai: {
        apiKey: 'your-openai-api-key',
        baseURL: 'https://api.openai.com/v1',
        model: 'gpt-4o-mini'
    },
    
    // 本地后端配置
    backend: {
        gatewayUrl: 'http://localhost:50051',
        educationUrl: 'http://localhost:50052'
    }
};
```

#### 步骤2: 创建API调用函数

```javascript
// AG2 学习风格诊断
async function diagnoseLearningStyle(features) {
    const response = await fetch('/api/ag2/diagnose', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({features})
    });
    return await response.json();
}

// AG3 智能辅导
async function chat(message, style) {
    const response = await fetch('/api/ag3/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message, style})
    });
    return await response.json();
}

// AG4 资源推荐
async function recommend(knowledgePoint, difficulty, style) {
    const response = await fetch('/api/ag4/recommend', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({knowledgePoint, difficulty, style})
    });
    return await response.json();
}

// AG5 生成测试
async function generateTest(knowledgePoint, difficulty, count) {
    const response = await fetch('/api/ag5/generate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({knowledgePoint, difficulty, count})
    });
    return await response.json();
}
```

#### 步骤3: 启动后端服务

```bash
# 安装依赖
pip install -r requirements.minimal.txt

# 设置API密钥
export OPENAI_API_KEY="your-key"

# 启动网关服务
python deploy/gateway_server.py --port 50051

# 启动教学域服务
python deploy/education_server.py --port 50052
```

---

## 🔌 完整API端点

### 网关服务 (端口 50051)

```protobuf
// 隐私网关服务
service PrivacyGateway {
    // 路由跨域请求
    rpc RouteCrossDomain (CrossDomainRequest) returns (CrossDomainResponse);
    
    // 学习者域 → 教学域路由
    rpc RouteLearnerToEducation (LearnerDataRequest) returns (AgentResponse);
    
    // 获取拓扑状态
    rpc GetTopologyStatus (TopologyRequest) returns (TopologyResponse);
    
    // 健康检查
    rpc HealthCheck (HealthCheckRequest) returns (HealthCheckResponse);
}
```

### 教学域服务 (端口 50052)

```protobuf
// 智能体服务
service AgentService {
    // 处理智能体请求
    rpc ProcessRequest (AgentRequestGRPC) returns (AgentResponseGRPC);
    
    // 健康检查
    rpc HealthCheck (HealthCheckRequest) returns (HealthCheckResponse);
}
```

### HTTP API（可选封装）

```javascript
// HTTP API 端点（如果需要RESTful接口）
POST /api/v1/agents/ag2/diagnose
POST /api/v1/agents/ag3/chat
POST /api/v1/agents/ag4/recommend
POST /api/v1/agents/ag5/generate-test
GET  /api/v1/gateway/topology
GET  /api/v1/gateway/privacy-budget
```

---

## 💡 使用建议

### 开发/演示阶段
使用 `frontend/interactive.html`（纯前端模拟）

**优点**：
- 无需配置API密钥
- 无需启动后端服务
- 立即展示交互流程
- 适合演示和展示

### 生产环境
配置真实API + 后端服务

**优点**：
- 真实的GPT模型调用
- 完整的隐私保护流程
- 生产级部署
- 真实智能体协作

---

## 🔑 获取API密钥

### OpenAI API
1. 访问 https://platform.openai.com/
2. 注册/登录账号
3. 进入 API Keys 页面
4. 创建新的API密钥
5. 复制密钥并配置到项目

```bash
# 配置密钥
export OPENAI_API_KEY="sk-..."
```

---

## 📊 API调用示例

### AG2 学习风格诊断

**请求**：
```json
{
    "agent_type": "AG2_Style",
    "task_type": "diagnose",
    "data": {
        "protected_features": {
            "visual": 0.85,
            "auditory": 0.60,
            "reading": 0.70,
            "kinesthetic": 0.65
        }
    }
}
```

**响应**：
```json
{
    "success": true,
    "result": {
        "learning_style": "Visual",
        "confidence": 0.85
    }
}
```

### AG3 智能辅导

**请求**：
```json
{
    "agent_type": "AG3_Tutor",
    "task_type": "tutor",
    "data": {
        "student_pseudonym": "pseudo_abc123",
        "learning_style": "Visual",
        "student_input": "我不理解二次函数的顶点公式"
    }
}
```

**响应**：
```json
{
    "success": true,
    "result": {
        "scaffolding_questions": [
            "你能试着画个二次函数的图像吗？",
            "观察图像的开口方向，你能发现什么规律？"
        ],
        "explanation": "对于Visual型学习者，建议多使用图像和可视化工具..."
    }
}
```

---

## 🚀 快速开始

### 立即体验（无需配置）

```bash
# 打开交互式前端
open frontend/interactive.html
```

### 完整功能（需要API密钥）

```bash
# 1. 配置API密钥
export OPENAI_API_KEY="your-key"

# 2. 安装依赖
pip install -r requirements.minimal.txt

# 3. 启动服务
python deploy/gateway_server.py &
python deploy/education_server.py &

# 4. 访问前端
open frontend/interactive.html
```

---

## 📝 总结

**当前实现**：
- ✅ 使用LangChain API实现智能体
- ✅ 使用OpenAI GPT模型
- ✅ 提供纯前端模拟版本
- ✅ 支持真实API调用

**前端入口**：
- 🌐 `frontend/interactive.html` - 完整交互界面
- 📊 `frontend/index.html` - 监控面板

**API密钥**：
- 🔑 需要OpenAI API密钥才能运行真实智能体
- 💡 可以先用模拟版本了解功能

---

*更新时间: 2026-03-13 22:54*
