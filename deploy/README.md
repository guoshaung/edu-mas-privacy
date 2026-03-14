# 教育平台使用说明

## 快速开始

### 1. 启动系统

```bash
cd /Users/mac9/.openclaw/workspace/edu-mas-privacy
./deploy/start_all.sh
```

这将启动：
- **隐私网关服务** (端口 50051)
- **教学域服务** (端口 50052)
- **REST API服务器** (端口 8080)

### 2. 访问前端

在浏览器中打开：

**学生端：**
```
file:///Users/mac9/.openclaw/workspace/edu-mas-privacy/frontend/student_cn.html
```

**教师端：**
```
file:///Users/mac9/.openclaw/workspace/edu-mas-privacy/frontend/teacher_cn.html
```

### 3. 停止系统

```bash
./deploy/stop_all.sh
```

---

## 功能说明

### 学生端功能

1. **发送问题**
   - 在输入框输入问题，点击"发送"按钮
   - AI老师会根据学习风格提供个性化回复

2. **快捷问题**
   - 点击"❓ 不懂概念"快速提问
   - 点击"📝 作业帮助"获取作业指导
   - 点击"💡 看个例题"查看例题
   - 点击"📚 复习提醒"设置复习提醒

3. **离线模式**
   - 如果后端服务不可用，会自动切换到离线模式
   - 离线模式使用预设的回复

### 教师端功能

1. **查看学生列表**
   - 左侧显示所有学生
   - 可通过搜索框搜索学生

2. **学生详情**
   - 点击学生卡片查看详情
   - 包括学习风格、进度、薄弱点等

3. **管理功能**
   - 📚 查看学习路径
   - 📝 为学生生成测试
   - 🔔 发送学习提醒
   - 📊 导出学习报告

4. **系统监控**
   - GNN拓扑图显示系统架构
   - 实时日志显示系统运行状态
   - 自动接收学生消息通知

---

## 工作原理

### 数据流向

```
学生端 → REST API → 隐私网关 → 教学域智能体 → 隐私网关 → REST API → 学生端
```

### 隐私保护

1. **学生数据本地化**
   - 原始学习数据存储在学生端
   - 只发送经过隐私保护处理的数据

2. **多层保护**
   - LDP（本地差分隐私）：添加噪声
   - SRPG（安全重构）：特征重构
   - 动态RBAC：权限控制

3. **零信任架构**
   - 所有数据传输都经过网关验证
   - 智能体无法访问原始隐私数据

---

## 故障排查

### 问题1：后端服务无法启动

**检查端口占用：**
```bash
lsof -i :50051
lsof -i :50052
lsof -i :8080
```

**杀死占用进程：**
```bash
kill -9 <PID>
```

### 问题2：前端无法连接后端

**检查服务状态：**
```bash
curl http://localhost:8080/health
```

**查看日志：**
```bash
tail -f logs/gateway.log
tail -f logs/education.log
tail -f logs/rest_api.log
```

### 问题3：学生发送消息无响应

1. 检查后端服务是否运行
2. 打开浏览器开发者工具（F12）查看控制台错误
3. 确认 `api.js` 文件路径正确

---

## 开发调试

### 启动单个服务

**仅启动网关：**
```bash
python3 deploy/gateway_server.py --port 50051
```

**仅启动教学域：**
```bash
python3 deploy/education_server.py --port 50052
```

**仅启动REST API：**
```bash
python3 deploy/rest_api_server.py
```

### 查看API文档

在浏览器中打开：
```
http://localhost:8080/docs
```

这里可以看到所有可用的API接口和测试界面。

---

## 技术栈

- **前端：** HTML + JavaScript + Bootstrap 5
- **后端：** Python + FastAPI
- **通信：** gRPC + REST API
- **AI：** LangChain + OpenAI GPT-4
- **隐私保护：** LDP + SRPG + 动态RBAC

---

## 下一步改进

- [ ] 添加用户认证系统
- [ ] 实现WebSocket实时通信
- [ ] 添加数据库存储学生数据
- [ ] 完善错误处理和日志记录
- [ ] 添加单元测试
- [ ] 优化UI/UX设计
