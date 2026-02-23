#!/bin/bash
# 使用 systemd 部署邮件机器人为系统服务

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SERVICE_FILE="treehole-email-bot.service"

echo "=========================================="
echo "  部署树洞邮件机器人"
echo "=========================================="
echo ""

# 检查是否有 root 权限
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  此脚本需要 root 权限"
    echo "请使用: sudo bash deploy_service.sh"
    exit 1
fi

# 创建日志目录
mkdir -p "$PROJECT_DIR/logs"
chown ubuntu:ubuntu "$PROJECT_DIR/logs"

# 复制 service 文件到 systemd 目录
echo "1. 安装 systemd 服务..."
cp "$SCRIPT_DIR/$SERVICE_FILE" /etc/systemd/system/

# 重新加载 systemd
echo "2. 重新加载 systemd..."
systemctl daemon-reload

# 启用开机自启
echo "3. 启用开机自启..."
systemctl enable treehole-email-bot.service

# 启动服务
echo "4. 启动服务..."
systemctl start treehole-email-bot.service

# 检查状态
echo ""
echo "=========================================="
echo "  部署完成！"
echo "=========================================="
echo ""
echo "📊 服务状态:"
systemctl status treehole-email-bot.service --no-pager
echo ""
echo "📝 常用命令:"
echo "  - 查看状态: sudo systemctl status treehole-email-bot"
echo "  - 查看日志: tail -f $PROJECT_DIR/logs/bot.log"
echo "  - 停止服务: sudo systemctl stop treehole-email-bot"
echo "  - 重启服务: sudo systemctl restart treehole-email-bot"
echo "  - 禁用服务: sudo systemctl disable treehole-email-bot"
echo ""
