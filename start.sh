#!/bin/bash
# Render 部署启动脚本

# 使用 PORT 环境变量（Render 会自动设置）
PORT=${PORT:-8080}

echo "=================================="
echo "  WorkBuddy Token Stats"
echo "=================================="
echo "  Port: $PORT"
echo "  Mode: Production"
echo "=================================="

python render_server.py
