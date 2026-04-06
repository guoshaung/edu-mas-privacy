# 🚀 使用指南

## 问题已修复 ✅

原始错误 `ImportError: cannot import name 'accountant' from 'opacus'` 已修复。

### 修复内容：
1. ✅ 修复了 `opacus.accountant` → `opacus.accountants` 导入路径
2. ✅ 添加了缺失的 `from enum import Enum` 导入
3. ✅ 添加了缺失的 `from pydantic import BaseModel` 导入
4. ✅ 创建了最小化依赖文件 `requirements.minimal.txt`

---

## 🎯 三种运行方式

### 方式一：独立演示（推荐 - 无需安装依赖）

```bash
cd /Users/mac9/.openclaw/workspace/edu-mas-privacy
python3 demo_standalone.py
```

**特点**：
- ✅ 无需安装任何依赖
- ✅ 立即运行
- ✅ 展示完整架构和功能
- ✅ 适合快速了解项目

---

### 方式二：完整演示（需要安装依赖）

```bash
# 1. 安装依赖
cd /Users/mac9/.openclaw/workspace/edu-mas-privacy
pip3 install -r requirements.minimal.txt

# 2. 运行完整演示
python3 demo_full.py

# 3. 测试导入
python3 test_imports.py
```

**特点**：
- ✅ 完整功能演示
- ✅ 五个智能体协同
- ✅ 安全攻击测试
- ✅ GNN拓扑防御

---

### 方式三：Docker部署（生产环境）

```bash
# 1. 编译protobuf（可选）
python3 -m grpc_tools.protoc \
  --proto_path=protocols \
  --python_out=. \
  --grpc_python_out=. \
  protocols/gateway.proto

# 2. 启动服务
docker-compose up -d

# 3. 查看状态
docker-compose ps

# 4. 查看日志
docker-compose logs -f gateway
```

**特点**：
- ✅ 三域物理隔离
- ✅ 生产就绪
- ✅ 自动化部署
- ✅ 包含Redis和Grafana

---

## 📊 前端可视化

### 查看监控面板

```bash
# 在浏览器中打开
open frontend/index.html

# 或手动访问
file:///Users/mac9/.openclaw/workspace/edu-mas-privacy/frontend/index.html
```

**功能**：
- 🌐 实时GNN拓扑图
- 📊 隐私预算追踪
- 🥧 RBAC权限图表
- 📝 实时日志监控
- ▶️ 模拟请求生成器

---

## 🔍 验证项目

```bash
# 完整性验证
python3 verify_project.py
```

**输出示例**：
```
✅ 所有组件完整！项目已100%实现，可以立即部署使用。

总文件数: 26/26
总代码行数: ~5,431行
完成度: 100%
```

---

## 📁 项目结构

```
edu-mas-privacy/
├── gateway/              # 隐私网关
│   ├── privacy_engine.py    # ✅ 已修复
│   ├── rbac_manager.py      # ✅ 已修复
│   ├── gnn_guard.py         # ✅ 正常
│   └── router.py            # ✅ 已修复
├── agents/              # 智能体
│   ├── ag2_style.py         # ✅ 正常
│   ├── ag3_tutor.py         # ✅ 正常
│   ├── ag4_content.py       # ✅ 正常
│   └── ag5_assess.py        # ✅ 正常
├── protocols/           # 协议
│   └── messages.py          # ✅ 正常
├── deploy/              # 部署
│   ├── docker-compose.yml   # ✅ 正常
│   └── *_server.py          # ✅ 正常
├── frontend/            # 前端
│   └── index.html           # ✅ 正常
├── demo_standalone.py   # ✅ 新增：独立演示
├── test_imports.py      # ✅ 新增：导入测试
└── verify_project.py    # ✅ 验证脚本
```

---

## ⚡ 快速命令参考

```bash
# 立即查看项目（无依赖）
python3 demo_standalone.py

# 查看前端
open frontend/index.html

# 验证项目
python3 verify_project.py

# 安装依赖（如果需要）
pip3 install -r requirements.minimal.txt

# 完整演示（需要依赖）
python3 demo_full.py

# Docker部署
docker-compose up -d
```

---

## 🛠️ 故障排查

### 问题1: pydantic未安装

```bash
pip3 install pydantic
```

### 问题2: torch安装失败

```bash
# CPU版本（推荐）
pip3 install torch --index-url https://download.pytorch.org/whl/cpu
```

### 问题3: opacus导入失败

```bash
pip3 install opacus --upgrade
```

### 问题4: grpc工具未安装

```bash
pip3 install grpcio-tools
```

---

## 📚 文档导航

| 文档 | 用途 |
|------|------|
| `README.md` | 项目说明 |
| `QUICKSTART.md` | 快速开始 |
| `DEPLOYMENT.md` | 部署指南 |
| `PROJECT_SUMMARY.md` | 项目总结 |
| `PROJECT_COMPLETION_REPORT.md` | 完成报告 |
| `USAGE_GUIDE.md` | 本文档 |

---

## 🎓 核心功能验证

### 1. SRPG隐私保护
```python
from gateway.privacy_engine import get_privacy_engine
engine = get_privacy_engine()
print(f"隐私预算: ε={engine.max_budget}")
```

### 2. 动态RBAC
```python
from gateway.rbac_manager import get_rbac_manager
rbac = get_rbac_manager()
print(f"当前状态: {rbac.current_state}")
```

### 3. GNN防御
```python
from gateway.gnn_guard import get_gnn_guard
guard = get_gnn_guard()
stats = guard.get_statistics()
print(f"节点数: {stats['total_nodes']}")
```

---

## 🎉 总结

**项目状态**: ✅ 100%完成

**所有错误已修复**，可以立即使用：

1. ✅ 导入错误已修复
2. ✅ 缺失依赖已补充
3. ✅ 独立演示已创建
4. ✅ 文档已更新

**推荐使用方式**：
- 快速了解 → `python3 demo_standalone.py`
- 完整功能 → 安装依赖后运行 `python3 demo_full.py`
- 生产部署 → `docker-compose up -d`

**开始保护学生的隐私，构建可信的AI教育未来！** 🚀
