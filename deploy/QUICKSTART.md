# 🚀 快速启动指南

## 一键启动

```bash
cd /Users/mac9/.openclaw/workspace/edu-mas-privacy
./deploy/start_all.sh
```

## 访问系统

### 学生端
在浏览器打开：
```
file:///Users/mac9/.openclaw/workspace/edu-mas-privacy/frontend/student_cn.html
```

### 教师端
在浏览器打开：
```
file:///Users/mac9/.openclaw/workspace/edu-mas-privacy/frontend/teacher_cn.html
```

## 测试功能

### 方式1：手动测试

1. **学生端发送消息**
   - 在输入框输入："二次函数的顶点公式怎么理解？"
   - 点击"发送 📤"
   - 等待AI老师回复

2. **教师端查看**
   - 点击左侧学生卡片（如"张同学"）
   - 查看学生详情和学习进度
   - 点击"📚 查看学习路径"等按钮测试功能

### 方式2：自动测试

```bash
python3 deploy/test_message_flow.py
```

这会自动测试：
- ✅ 网关连接
- ✅ 学生消息发送
- ✅ AI老师回复
- ✅ REST API接口

## 停止系统

```bash
./deploy/stop_all.sh
```

## 查看日志

```bash
# 实时查看所有日志
tail -f logs/gateway.log
tail -f logs/education.log
tail -f logs/rest_api.log

# 或者在后台运行
./deploy/start_all.sh
```

## 故障排查

### 问题：端口被占用

```bash
# 查看占用端口的进程
lsof -i :50051
lsof -i :50052
lsof -i :8080

# 杀死进程
kill -9 <PID>
```

### 问题：前端无法连接后端

1. 确认后端服务已启动
2. 检查浏览器控制台（F12）是否有错误
3. 确认 `api.js` 文件存在

### 问题：没有收到AI回复

1. 检查后端服务状态：`curl http://localhost:8080/health`
2. 查看日志：`tail -f logs/rest_api.log`
3. 确认OpenAI API密钥已配置（如果需要）

## 系统架构

```
┌─────────────┐
│  学生端网页  │
└──────┬──────┘
       │ HTTP
┌──────▼──────┐
│ REST API    │ (端口 8080)
│  服务器     │
└──────┬──────┘
       │ gRPC
┌──────▼──────┐
│  隐私网关   │ (端口 50051)
└──────┬──────┘
       │ gRPC
┌──────▼──────┐
│ 教学域服务  │ (端口 50052)
│ AG3辅导     │
└─────────────┘
```

## 下一步

- 📖 详细文档：`deploy/README.md`
- 🧪 测试脚本：`deploy/test_message_flow.py`
- 🔧 修改配置：编辑各服务器的启动参数

## 需要帮助？

运行测试脚本查看详细信息：
```bash
python3 deploy/test_message_flow.py
```

查看日志排查问题：
```bash
tail -100 logs/gateway.log
tail -100 logs/education.log
tail -100 logs/rest_api.log
```
