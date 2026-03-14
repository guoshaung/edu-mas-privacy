#!/bin/bash

# 一键启动整个教育平台系统
# 包含：网关服务、教学域服务、REST API服务器

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "================================================================"
echo "🚀 启动零信任隐私保护多智能体学习平台"
echo "================================================================"
echo ""

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python3"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖..."
pip install -q fastapi uvicorn grpcio grpcio-tools pydantic 2>/dev/null || true

# 创建日志目录
mkdir -p logs

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "第 1 步: 启动隐私网关服务 (端口 50051)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 deploy/gateway_server.py --port 50051 > logs/gateway.log 2>&1 &
GATEWAY_PID=$!
echo "✅ 网关服务已启动 (PID: $GATEWAY_PID)"
echo "   日志文件: logs/gateway.log"

# 等待网关启动
sleep 3

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "第 2 步: 启动教学域服务 (端口 50052)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 deploy/education_server.py --port 50052 > logs/education.log 2>&1 &
EDUCATION_PID=$!
echo "✅ 教学域服务已启动 (PID: $EDUCATION_PID)"
echo "   日志文件: logs/education.log"

# 等待教学域服务启动
sleep 3

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "第 3 步: 启动REST API服务器 (端口 8080)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 deploy/rest_api_server.py > logs/rest_api.log 2>&1 &
REST_API_PID=$!
echo "✅ REST API服务器已启动 (PID: $REST_API_PID)"
echo "   日志文件: logs/rest_api.log"

# 等待REST API启动
sleep 2

echo ""
echo "================================================================"
echo "✅ 所有服务启动完成！"
echo "================================================================"
echo ""
echo "📍 服务地址："
echo "   • 学生端: http://localhost:8080/frontend/student_cn.html"
echo "   • 教师端: http://localhost:8080/frontend/teacher_cn.html"
echo "   • REST API: http://localhost:8080/api"
echo "   • API文档: http://localhost:8080/docs"
echo ""
echo "📊 后端服务："
echo "   • 隐私网关: localhost:50051"
echo "   • 教学域服务: localhost:50052"
echo ""
echo "🛑 停止服务："
echo "   运行: ./deploy/stop_all.sh"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 实时日志监控"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "运行以下命令查看日志："
echo "  tail -f logs/gateway.log      # 网关日志"
echo "  tail -f logs/education.log    # 教学域日志"
echo "  tail -f logs/rest_api.log     # REST API日志"
echo ""

# 保存PID以便后续关闭
echo "$GATEWAY_PID" > logs/gateway.pid
echo "$EDUCATION_PID" > logs/education.pid
echo "$REST_API_PID" > logs/rest_api.pid

echo "✅ 进程ID已保存到 logs/*.pid"
echo ""
echo "🎉 系统已就绪！在浏览器中打开前端页面开始使用。"
echo "================================================================"
