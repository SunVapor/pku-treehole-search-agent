#!/bin/bash
# 邮件机器人启动脚本

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "  树洞邮件机器人"
echo "=========================================="
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python 3"
    exit 1
fi

# 检查依赖
echo "检查依赖..."
pip3 install -q markdown 2>/dev/null || {
    echo "⚠️  安装 markdown 库失败，将只发送纯文本邮件"
}

# 检查配置文件
if [ ! -f "$PROJECT_DIR/config_private.py" ]; then
    echo "❌ 未找到 $PROJECT_DIR/config_private.py"
    echo "请先运行 bash start.sh 创建配置文件"
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/email_config.py" ]; then
    echo "❌ 未找到 email_config.py"
    echo "请先配置邮箱信息: cp email_config_template.py email_config.py"
    exit 1
fi

# 启动机器人
echo ""
echo "启动邮件机器人..."
echo ""

python3 bot_email.py
