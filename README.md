# 🎓 零信任隐私保护多智能体学习平台

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Status: Active](https://img.shields.io/badge/Status-Active-success.svg)]()

## 📖 项目简介

这是一个基于**零信任架构**的隐私保护在线教育平台，利用多智能体系统为学生提供个性化辅导，同时通过**LDP（本地差分隐私）**、**SRPG（安全重构保护生成）**和**动态RBAC**等技术保护学生隐私数据。

### 🎯 核心特性

- 🔒 **零信任隐私保护** - 学生原始数据永不离开本地设备
- 🤖 **多智能体协作** - AG2-AG5智能体协同工作
- 🎨 **学习风格适配** - 支持Visual、Aural、ReadWrite、Kinesthetic四种学习风格
- 💡 **启发式教学** - 不直接给答案，而是引导学生思考
- 🌐 **实时交互** - WebSocket实时通信，即时反馈
- 📊 **学习分析** - 智能诊断学习问题，生成个性化学习路径

## 🏗️ 系统架构

```
┌─────────────┐
│  学生端网页  │ ← 学习者域（高信域）
└──────┬──────┘
       │ HTTPS
┌──────▼──────┐
│ REST API    │ ← 控制平面
│  服务器     │
└──────┬──────┘
       │ gRPC
┌──────▼──────┐
│  隐私网关   │ ← 动态RBAC + 隐私验证
└──────┬──────┘
       │ gRPC
┌──────▼──────┐
│ 教学域服务  │ ← 教学域（低信域）
│ AG2-AG5     │
└─────────────┘
```

### 智能体分工

- **A1_Profile** - 学生档案管理（学习者域）
- **AG2_Style** - 学习风格识别
- **AG3_Tutor** - 自适应辅导（教学核心）
- **AG4_Content** - 内容挖掘与推荐
- **AG5_Assess** - 自适应评估

## 🚀 快速开始

### 前置要求

- Python 3.8+
- 现代浏览器（Chrome、Firefox、Safari）

### 1. 克隆项目

```bash
git clone https://github.com/你的用户名/edu-mas-privacy.git
cd edu-mas-privacy
```

### 2. 启动API服务器

```bash
python3 deploy/simple_api_server.py
```

服务器将运行在 `http://localhost:8080`

### 3. 打开前端页面

**学生端：**
```bash
open frontend/student_cn.html
```

**教师端：**
```bash
open frontend/teacher_cn.html
```

**测试页面：**
```bash
open frontend/test_student.html
```

### 4. 测试功能

在测试页面：
1. 点击"测试连接"验证API可用
2. 选择学习风格
3. 输入问题并发送
4. 查看个性化AI回复

## 📚 使用示例

### 学生提问示例

**输入：**
```
二次函数的顶点公式怎么理解？
```

**AI回复（Visual风格）：**
```
很好！二次函数确实是一个重要概念。让我们用图像来理解：

**顶点公式的几何意义：**

1. **图像特征**：抛物线开口由a决定
   - a > 0：开口向上（像笑脸😊）
   - a < 0：开口向下（像哭脸😢）

2. **顶点坐标**：(-b/2a, f(-b/2a))

**思考题：**
• 如果a=2，b=4，顶点x坐标是多少？
• 你能画出y = x² - 4x + 3的图像吗？
```

## 🔧 技术栈

- **前端：** HTML5 + JavaScript + Bootstrap 5
- **后端：** Python + FastAPI + gRPC
- **AI：** 启发式教学算法 + 学习风格适配
- **隐私保护：** LDP + SRPG + 动态RBAC

## 📁 项目结构

```
edu-mas-privacy/
├── agents/              # 智能体实现
├── deploy/             # 部署脚本
├── frontend/           # 前端页面
├── gateway/            # 隐私网关
├── protocols/          # 通信协议
├── data/               # 数据集
└── docs/               # 文档
```

## 🧪 测试

运行测试脚本：

```bash
python3 deploy/test_message_flow.py
```

或使用测试页面：`frontend/test_student.html`

## 📖 文档

- [快速开始指南](QUICKSTART.md)
- [部署文档](DEPLOYMENT.md)
- [API文档](API_GUIDE.md)
- [测试结果](TEST_RESULTS.md)

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 👨‍💻 作者

Your Name

## 🙏 致谢

感谢所有贡献者和开源项目的支持！

---

**⚠️ 注意：** 本项目为教育演示项目，生产环境使用需要额外的安全加固和性能优化。
