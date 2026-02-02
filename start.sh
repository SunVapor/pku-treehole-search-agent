#!/bin/bash
# 快速启动脚本 - 运行此脚本快速开始使用

echo "=========================================="
echo "  PKU 树洞 RAG Agent"
echo "  快速启动向导"
echo "=========================================="
echo ""

# 步骤 1: 检查是否在正确的目录
if [ ! -f "agent.py" ]; then
    echo "❌ 错误: 请在项目根目录下运行此脚本"
    exit 1
fi

# 步骤 2: 检查 Python
echo "步骤 1/5: 检查 Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python 3。请安装 Python 3.8+"
    exit 1
fi
echo "✓ Python 已找到: $(python3 --version)"
echo ""

# 步骤 3: 安装依赖
echo "步骤 2/5: 安装依赖..."
pip3 install -q requests
echo "✓ 依赖已安装"
echo ""

# 步骤 4: 检查配置文件
echo "步骤 3/5: 检查配置文件..."
if [ ! -f "config_private.py" ]; then
    echo ""
    echo "📝 未找到 config_private.py，开始创建配置文件..."
    echo ""
    
    # 交互式输入配置信息
    echo "请输入以下信息（按 Ctrl+C 可退出）:"
    echo ""
    
    # 读取用户名
    read -p "请输入您的学号 (如: 2100012345): " USERNAME
    if [ -z "$USERNAME" ]; then
        echo "❌ 学号不能为空"
        exit 1
    fi
    
    # 读取密码（隐藏输入）
    read -s -p "请输入您的密码: " PASSWORD
    echo ""
    if [ -z "$PASSWORD" ]; then
        echo "❌ 密码不能为空"
        exit 1
    fi
    
    # 读取 API Key
    echo ""
    echo "请访问 https://platform.deepseek.com/ 获取 API Key"
    read -p "请输入您的 DeepSeek API Key (如: sk-xxx...): " DEEPSEEK_API_KEY
    if [ -z "$DEEPSEEK_API_KEY" ]; then
        echo "❌ API Key 不能为空"
        exit 1
    fi
    
    # 创建 config_private.py
    echo ""
    echo "正在创建 config_private.py..."
    cat > config_private.py << EOF
"""
Private configuration file for PKU Treehole RAG Agent.
This file is gitignored for security.
"""

# ==================== Treehole Credentials ====================
# Your PKU credentials for Treehole login
USERNAME = "$USERNAME"
PASSWORD = "$PASSWORD"

# ==================== DeepSeek API Configuration ====================
# Get your API key from: https://platform.deepseek.com/
DEEPSEEK_API_KEY = "$DEEPSEEK_API_KEY"
DEEPSEEK_API_BASE = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"  # or "deepseek-reasoner"

# ==================== Agent Configuration ====================
# Maximum number of posts to retrieve per search
MAX_SEARCH_RESULTS = 40

# Maximum number of posts to include in context for LLM
MAX_CONTEXT_POSTS = 30

# Temperature for LLM generation (0.0 - 1.0)
# Lower = more focused, Higher = more creative
TEMPERATURE = 0.7

# Maximum tokens for LLM response
MAX_RESPONSE_TOKENS = 4096

# ==================== Rate Limiting ====================
# Delay between search requests (seconds)
SEARCH_DELAY = 1.0

# Maximum retries for failed requests
MAX_RETRIES = 3

# ==================== Cache Configuration ====================
# Enable caching of search results
ENABLE_CACHE = True

# Cache directory
CACHE_DIR = "data/cache"

# Cache expiration time (seconds), 1 day = 86400
CACHE_EXPIRATION = 86400
EOF
    
    echo "✓ config_private.py 已创建"
    echo ""
else
    echo "✓ config_private.py 已存在"
    echo ""
fi



echo "=========================================="
echo "  设置完成！"
echo "=========================================="
echo ""
echo "🚀 接下来的步骤：python3 agent.py"
echo ""
echo "=========================================="
