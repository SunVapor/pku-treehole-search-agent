#!/bin/bash
# 部署Web服务器为systemd服务

echo "正在部署 PKU Treehole Web Server 服务..."

# 复制服务文件
sudo cp treehole-web-server.service /etc/systemd/system/

# 重新加载systemd
sudo systemctl daemon-reload

# 启用服务
sudo systemctl enable treehole-web-server

# 启动服务
sudo systemctl start treehole-web-server

# 显示状态
echo ""
echo "服务状态："
sudo systemctl status treehole-web-server --no-pager | head -15

echo ""
echo "✓ Web服务器已部署！"
echo ""
echo "访问地址："
echo "  内网: http://10.129.83.176:5000"
echo "  本机: http://localhost:5000"
echo ""
echo "管理命令："
echo "  查看状态: sudo systemctl status treehole-web-server"
echo "  查看日志: tail -f ~/pku-treehole-search-agent/logs/web_server.log"
echo "  重启服务: sudo systemctl restart treehole-web-server"
echo "  停止服务: sudo systemctl stop treehole-web-server"
