#!/bin/bash
# 依赖安装脚本

echo "🔧 安装项目依赖..."

# 检查Python版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python版本: $python_version"

# 安装核心依赖
echo "安装核心依赖..."
pip3 install pydantic 2>&1 | grep -v "Requirement already satisfied"
pip3 install torch 2>&1 | grep -v "Requirement already satisfied"
pip3 install numpy 2>&1 | grep -v "Requirement already satisfied"

# 安装隐私计算
echo "安装Opacus（差分隐私）..."
pip3 install opacus 2>&1 | grep -v "Requirement already satisfied"

# 安装GNN（可选，可能需要CUDA）
echo "安装PyTorch Geometric..."
pip3 install torch-geometric 2>&1 | grep -v "Requirement already satisfied" || echo "⚠️  torch-geometric安装失败，可能需要手动安装"

# 安装LangGraph和LangChain
echo "安装LangGraph和LangChain..."
pip3 install langgraph langchain langchain-openai 2>&1 | grep -v "Requirement already satisfied"

# 安装通信和存储
echo "安装gRPC和Redis..."
pip3 install grpcio grpcio-tools redis 2>&1 | grep -v "Requirement already satisfied"

# 安装其他工具
echo "安装其他工具..."
pip3 install python-dotenv 2>&1 | grep -v "Requirement already satisfied"

echo ""
echo "✅ 依赖安装完成！"
echo ""
echo "运行测试: python3 test_imports.py"
