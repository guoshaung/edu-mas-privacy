# EduMAS 个性化教育隐私与版权保护平台

<div align="center">

![EduMAS Logo](./docs/assets/edumas-logo.svg)

<br />

![License](https://img.shields.io/badge/License-MIT-f4b400?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Privacy%20Gateway-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Agent%20Orchestration-6C5CE7?style=for-the-badge)
![Multi-Agent](https://img.shields.io/badge/Multi--Agent-Education%20MAS-1F2A44?style=for-the-badge)
![Privacy](https://img.shields.io/badge/Privacy-SRPG%20Dual%20Stream-17A673?style=for-the-badge)
![Copyright](https://img.shields.io/badge/Copyright-Dynamic%20Compliance-D95C5C?style=for-the-badge)
![FedGNN](https://img.shields.io/badge/FedGNN-Risk%20Modeling-2F80ED?style=for-the-badge)

<br />

**面向个性化教育的端云协同多智能体系统原型**  
**聚焦学生隐私保护、教师题库版权保护与联合治理决策**

</div>

---

## 项目定位

EduMAS 是一个面向个性化教育场景的多智能体系统原型。系统以学生本地侧为交互入口，以云端多智能体为教学执行主体，围绕：

- 个性诊断
- 学习规划
- 自适应辅导
- 知识检验
- 心理支持（后续扩展）

构建完整学习闭环。

与普通教育 Demo 不同，本项目的重点不只是“做一个能回答问题的教学系统”，而是把**隐私保护**与**版权治理**提升为架构级约束，在多智能体协同过程中同时处理：

- 学生侧敏感数据如何最小必要开放
- 教师侧题库资源如何按授权粒度使用
- 多轮交互下如何动态评估隐私与版权风险

当前仓库已经具备统一入口、学生端、教师端、隐私测试页、SRPG 双流演示页、算法展示页、公共题库管理页和多阶段网关接口，适合演示、联调和后续论文原型扩展。

---

## 核心亮点

### 1. 多智能体教育工作流

系统围绕以下主流程展开：

1. AG2 性格与学习风格诊断
2. AG3 学习规划与自适应辅导
3. AG4 公共题库与知识文档检索
4. AG5 知识检验与盲评估

教学链路以“诊断 -> 规划 -> 辅导 -> 检验”为主线，形成学生侧可体验的闭环工作台。

### 2. 隐私保护方法

项目当前的隐私治理由三个层次组成：

- **SRPG 双流融合机制**
  将学生输入拆分为逻辑流与去敏流，分别服务教学语义与个体敏感特征治理。
- **动态隐私信任评估**
  \[
  T_{p}(t)=\alpha T_{\text{base}}-\beta D_{t}-\gamma R_{\text{gnn}}-\lambda E_{t}
  \]
  用于描述当前学生数据在多轮交互中的可开放程度。
- **联邦风险建模**
  本地 FedGNN 监控通信时序、频率、语义分布和梯度摘要，并把风险分数回注到网关控制中。

### 3. 版权保护方法

教师端题库不再只是“上传后供系统随便使用”，而是带有明确版权属性和授权范围：

- 版权等级
- 授权范围
- 是否允许学生查看原文
- 是否允许系统生成衍生内容

项目当前使用动态版权合规评估函数：

\[
C_{r}(t)=\mu R_{c}+\nu R_{a}+\xi R_{p}+\rho R_{e}+\sigma R_{i}
\]

并结合题库交付策略决定：

- 返回原文
- 仅返回摘要
- 触发替代生成
- 阻断访问

### 4. 联合治理决策

系统不把隐私和版权简单混成一个总分，而是分别计算后再由治理层决定：

- 正常放行
- 加强脱敏后放行
- 摘要输出
- 替代生成
- 阻断

这使得系统更适合作为**凌驾于 MAS 之上的治理层框架**进行表达和扩展。

---

## 当前原型能力

### 已实现或已接通

- 统一登录页（学生 / 教师角色分流）
- 学生主页、学生页面、隐私测试页、SRPG 双流演示页、算法展示页
- 引导式个性诊断与本地画像持久化
- 学习规划接口与 LangGraph 状态机
- 自适应辅导接口与 AG3 新策略骨架
- 知识检验接口与 AG5 盲评估协议
- 教师公共题库管理与版权标签录入
- AG4 基于本地公共题库的检索与交付策略控制
- 隐私攻击演示页（提示注入、身份恢复、属性推断、成员推断、链接重识别、权限提升）
- 治理评分接口与算法展示页联动

### 正在完善或可继续扩展

- 心理咨询与情绪支持模块
- 更真实的 SRPG 差分隐私参数控制与可视化
- 更强的教师题库导入与公式识别
- 更完整的日志审计、治理看板与实验记录
- 版权水印 / 溯源与更细粒度的传播控制

---

## 技术栈

### 后端与网关

- `Python 3.12`
- `FastAPI`
- `Pydantic`
- `LangGraph`
- `LangChain`
- `Uvicorn`

### 机器学习与安全建模

- `NumPy`
- `PyTorch`
- `scikit-learn`
- `NetworkX`
- `Opacus`

### 前端与交互

- `React`
- `HTML / CSS / JavaScript`
- `localStorage`
- `MathJax`

### 系统与演示

- 本地静态页面服务
- 8010 云端治理与教学网关
- 教师端题库管理与多智能体工作台
- 学生端 SRPG / 隐私攻击 / 算法展示

---

## 系统结构

```text
app.py
├─ login.html / login_app.jsx         # 统一登录入口
├─ frontend/                          # 学生端、教师端与演示页面
├─ gateway/                           # 隐私网关、治理评分、规划/辅导/检验接口
├─ agents/                            # AG2~AG5 智能体核心逻辑
├─ protocols/                         # 共享消息协议
├─ data/                              # 公共题库与本地数据
├─ docs/assets/                       # Logo 与静态资源
├─ docs/guides/                       # 说明文档
├─ docs/reports/                      # 阶段记录与报告
└─ scripts/maintenance/               # 校验与维护脚本
```

---

## 主要页面入口

启动项目后，可重点查看以下页面：

- `http://127.0.0.1:8000/login.html`
- `http://127.0.0.1:8000/frontend/student_hub.html`
- `http://127.0.0.1:8000/frontend/student_profile.html`
- `http://127.0.0.1:8000/frontend/srpg_demo.html`
- `http://127.0.0.1:8000/frontend/algorithm_showcase.html`
- `http://127.0.0.1:8000/frontend/privacy_lab.html`
- `http://127.0.0.1:8000/frontend/teacher_workspace.html`
- `http://127.0.0.1:8000/frontend/teacher_question_bank.html`

---

## 启动方式

### 1. 启动前端静态页面

```bash
python app.py
```

默认访问：

```text
http://127.0.0.1:8000/login.html
```

### 2. 启动 8010 云端网关

```bash
.\.venv\Scripts\python.exe deploy\planning_gateway_api.py
```

网关健康检查：

```text
http://127.0.0.1:8010/health
```

---

## 当前说明

- 这是一个**研究型原型系统**，不是面向生产环境部署的商业化成品。
- 页面、网关、Agent 和治理公式已经形成较完整主链路，适合课程设计、项目汇报、论文原型展示与后续继续深化。
- 当前代码中既包含可运行模块，也包含部分 Demo 化演示逻辑；后续可继续围绕“隐私治理 + 版权治理 + MAS 教育工作流”三条主线推进。

---

## 后续建议方向

- 将 SRPG 双流演示页进一步接入实时差分隐私参数调节
- 把治理评分结果接入更多学生端 / 教师端可视化面板
- 增加实验日志页，记录 `T_p(t)`、`C_r(t)` 与联合策略的变化曲线
- 强化 AG4 的版权传播控制、水印与可追踪性
- 增加心理咨询与情绪支持工作流

