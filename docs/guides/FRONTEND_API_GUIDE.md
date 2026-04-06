# 🎉 前端交互入口 & API 使用说明

## 📱 前端交互入口

### 主要交互界面

**文件**: `frontend/interactive.html`

**功能**：
- 🎮 **四个智能体交互面板**
  - AG2: 学习风格诊断
  - AG3: 智能辅导对话
  - AG4: 资源推荐
  - AG5: 学习评估

- 📊 **实时监控面板**
  - GNN拓扑图
  - 隐私预算追踪
  - 请求数统计
  - 异常检测计数

- 📝 **实时日志**
  - 系统操作日志
  - API调用记录
  - 错误追踪

### 使用方法

```bash
# 在浏览器中打开
open frontend/interactive.html

# 或手动访问
file:///Users/mac9/.openclaw/workspace/edu-mas-privacy/frontend/interactive.html
```

---

## 🤖 API 使用说明

### 1. 本项目使用的 API

#### ✅ 是的，使用了和我同款的 API

本项目使用的智能体实现**基于 LangChain + OpenAI API**：

```python
# AG2, AG3, AG4, AG5 都使用这些API：
from langchain_openai import ChatOpenAI           # OpenAI GPT模型
from langchain_core.prompts import ChatPromptTemplate  # 提示词模板
from langchain_core.memory import ConversationBufferMemory  # 对话记忆
from langchain_openai import OpenAIEmbeddings     # 文本嵌入（RAG）
```

**具体对应关系**：
- 我的底层：Claude (Anthropic)
- 项目底层：GPT-4 (OpenAI)
- 中间层：都是 LangChain 框架

### 2. API 调用流程

```
用户输入
    ↓
前端界面 (interactive.html)
    ↓
┌─────────────────────────────────────┐
│  方式一：前端模拟（当前默认）         │
│  - JavaScript 模拟响应               │
│  - 无需API密钥                       │
│  - 立即可用                          │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  方式二：真实API（需要配置）         │
│  - 后端Python服务                    │
│  - LangChain调用                     │
│  - OpenAI GPT API                   │
└─────────────────────────────────────┘
```

### 3. 配置真实 API

#### 步骤1: 获取 API 密钥

```bash
# 访问 OpenAI 平台
https://platform.openai.com/api-keys

# 创建新的API密钥
sk-...
```

#### 步骤2: 配置密钥

```bash
# 方式一：环境变量
export OPENAI_API_KEY="sk-..."

# 方式二：.env文件
echo "OPENAI_API_KEY=sk-..." > .env
```

#### 步骤3: 安装依赖

```bash
pip install -r requirements.minimal.txt
```

#### 步骤4: 启动服务

```bash
# 启动网关
python deploy/gateway_server.py --port 50051 &

# 启动教学域
python deploy/education_server.py --port 50052 &
```

---

## 🎮 交互功能详解

### AG2: 学习风格诊断

**输入**：
- 视觉偏好 (0-1)
- 听觉偏好 (0-1)
- 读写偏好 (0-1)
- 动觉偏好 (0-1)

**输出**：
- 主要学习风格
- 置信度
- 各维度得分

**前端调用**：
```javascript
function diagnoseLearningStyle() {
    const visual = parseFloat(document.getElementById('visual').value);
    const auditory = parseFloat(document.getElementById('auditory').value);
    // ... 获取其他特征
    
    // 模拟API调用
    const result = {
        style: 'Visual',
        confidence: 0.85
    };
}
```

### AG3: 智能辅导对话

**输入**：
- 用户问题文本
- 学习风格

**输出**：
- 启发式提问
- 个性化解释
- 学习建议

**前端调用**：
```javascript
function sendMessage() {
    const message = document.getElementById('user-input').value;
    
    // 显示用户消息
    chatBox.innerHTML += `<div class="chat-message chat-user">${message}</div>`;
    
    // 模拟AG3响应
    const response = getTutoringResponse(message, learningStyle);
    chatBox.innerHTML += `<div class="chat-message chat-agent">${response}</div>`;
}
```

### AG4: 资源推荐

**输入**：
- 知识点（如"二次函数"）
- 难度等级 (0-1)
- 学习风格

**输出**：
- 视频资源
- 交互式实验
- 练习题

**前端调用**：
```javascript
function recommendResources() {
    const knowledgePoint = document.getElementById('knowledge-point').value;
    const difficulty = parseFloat(document.getElementById('difficulty').value);
    const style = document.getElementById('learning-style').value;
    
    // 模拟RAG检索
    const resources = [
        {type: 'video', title: `${knowledgePoint}基础讲解`},
        {type: 'interactive', title: `${knowledgePoint}可视化实验`},
        {type: 'exercise', title: `${knowledgePoint}练习题`}
    ];
}
```

### AG5: 学习评估

**输入**：
- 知识点
- 难度等级
- 题目数量

**输出**：
- 测试题目
- 答案选项
- 预计用时

**前端调用**：
```javascript
function generateTest() {
    const knowledgePoint = document.getElementById('test-knowledge').value;
    const difficulty = parseFloat(document.getElementById('test-difficulty').value);
    const count = parseInt(document.getElementById('question-count').value);
    
    // 模拟测试生成
    const questions = generateQuestions(knowledgePoint, difficulty, count);
}
```

---

## 📊 API 端点总览

### HTTP API (如果使用RESTful封装)

```
POST /api/v1/agents/ag2/diagnose
    → 学习风格诊断

POST /api/v1/agents/ag3/chat
    → 智能辅导对话

POST /api/v1/agents/ag4/recommend
    → 资源推荐

POST /api/v1/agents/ag5/generate-test
    → 生成测试

GET /api/v1/gateway/topology
    → 获取拓扑状态

GET /api/v1/gateway/privacy-budget
    → 获取隐私预算

GET /api/v1/gateway/anomalies
    → 获取异常记录
```

### gRPC API (生产环境)

```
service PrivacyGateway {
    rpc RouteCrossDomain (CrossDomainRequest) returns (CrossDomainResponse);
    rpc RouteLearnerToEducation (LearnerDataRequest) returns (AgentResponse);
    rpc GetTopologyStatus (TopologyRequest) returns (TopologyResponse);
}

service AgentService {
    rpc ProcessRequest (AgentRequestGRPC) returns (AgentResponseGRPC);
}
```

---

## 🔑 API 密钥配置

### OpenAI API

```bash
# 获取密钥
1. 访问 https://platform.openai.com/
2. 登录/注册
3. 进入 API Keys
4. 创建新密钥

# 配置密钥
export OPENAI_API_KEY="sk-..."
```

### LangSmith (可选，用于调试)

```bash
# LangSmith用于追踪LangChain调用
export LANGCHAIN_TRACING_V2="true"
export LANGCHAIN_API_KEY="lsv2-..."
export LANGCHAIN_PROJECT="edu-mas-privacy"
```

---

## 💡 使用建议

### 开发/演示
```bash
# 使用前端模拟版本（无需API密钥）
open frontend/interactive.html
```

### 生产环境
```bash
# 1. 配置API密钥
export OPENAI_API_KEY="sk-..."

# 2. 安装依赖
pip install -r requirements.minimal.txt

# 3. 启动服务
python deploy/gateway_server.py &
python deploy/education_server.py &

# 4. 访问前端
open frontend/interactive.html
```

---

## 📚 相关文档

- `API_GUIDE.md` - 详细API使用说明
- `USAGE_GUIDE.md` - 快速开始指南
- `DEPLOYMENT.md` - 部署指南

---

## 🎯 总结

### 前端交互入口
- 🌐 **主要界面**: `frontend/interactive.html`
- 📊 **监控面板**: `frontend/index.html`

### API 使用
- ✅ **是的，使用和我同款的 LangChain API**
- 🤖 **底层模型**: OpenAI GPT-4（我是Claude）
- 🔧 **框架**: LangChain（相同）
- 💬 **调用方式**: gRPC / HTTP

### 立即体验
```bash
# 无需配置，立即体验
open frontend/interactive.html
```

---

*更新时间: 2026-03-13 22:54*
