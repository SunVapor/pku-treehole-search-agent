#!/bin/bash
# 直接运行Web服务器（非服务模式）

cd "$(dirname "$0")"

echo "=========================================="
echo "  PKU Treehole Search Agent - Web Server"
echo "=========================================="
echo ""
echo "启动中..."
echo ""

python3 web_server.py
