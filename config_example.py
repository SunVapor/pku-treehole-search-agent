"""
配置文件示例 - 请复制此文件为 config_private.py 并填入真实值

使用方法：
    cp config_example.py config_private.py
    # 然后编辑 config_private.py，填入你的真实配置
"""

# ==================== Treehole Credentials ====================
# Your PKU credentials for Treehole login
USERNAME = "<USERNAME>"
PASSWORD = "<PASSWORD>"

# ==================== DeepSeek API Configuration ====================
# Get your API key from: https://platform.deepseek.com/
DEEPSEEK_API_KEY = "<DEEPSEEK_API_KEY>"
DEEPSEEK_API_BASE = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"  # or "deepseek-reasoner"

# ==================== Agent Configuration ====================
# Maximum number of posts to retrieve per search
MAX_SEARCH_RESULTS = 40

# Maximum number of posts to include in context for LLM
MAX_CONTEXT_POSTS = 30

# Maximum number of comments to include per post (for mode 1 & 2)
# Set to 0 to disable comments, -1 for unlimited
MAX_COMMENTS_PER_POST = 5

# Maximum number of search iterations in mode_auto_search (智能检索模式)
MAX_SEARCH_ITERATIONS = 5

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