#!/bin/bash
# WorkBuddy Token Stats 本地服务器启动脚本

echo "🚀 正在启动 Token 统计页面..."
echo ""
echo "启动后访问: http://localhost:3000"
echo "按 Ctrl+C 停止服务器"
echo ""

cd "$(dirname "$0")"
npx serve -l 3000 .
