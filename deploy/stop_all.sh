#!/bin/bash

# 停止所有服务

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "================================================================"
echo "🛑 停止零信任隐私保护多智能体学习平台"
echo "================================================================"
echo ""

# 读取PID并停止服务
for service in gateway education rest_api; do
    PID_FILE="logs/${service}.pid"

    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "⏹️  停止 $service 服务 (PID: $PID)..."
            kill "$PID"
            echo "✅ $service 已停止"
        else
            echo "⚠️  $service 服务未运行 (PID: $PID)"
        fi
        rm -f "$PID_FILE"
    else
        echo "⚠️  未找到 $service 的PID文件"
    fi
done

# 备用：通过端口名杀死进程
echo ""
echo "🧹 清理可能残留的进程..."
pkill -f "gateway_server.py" 2>/dev/null && echo "✅ 已清理网关进程" || true
pkill -f "education_server.py" 2>/dev/null && echo "✅ 已清理教学域进程" || true
pkill -f "rest_api_server.py" 2>/dev/null && echo "✅ 已清理REST API进程" || true

echo ""
echo "================================================================"
echo "✅ 所有服务已停止"
echo "================================================================"
