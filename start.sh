#!/bin/bash
# WorkBuddy Token Stats 启动脚本

echo "=========================================="
echo "  🚀 WorkBuddy Token 使用量统计"
echo "=========================================="
echo ""
echo "启动服务器后访问: http://localhost:8080"
echo ""
echo "功能说明:"
echo "  - 自动读取 ~/.workbuddy/traces/ 获取最新数据"
echo "  - 支持自定义日期范围"
echo "  - 实时更新，点击按钮刷新即可获取最新数据"
echo ""
echo "按 Ctrl+C 停止服务器"
echo "=========================================="

cd "$(dirname "$0")"
python3 server.py
