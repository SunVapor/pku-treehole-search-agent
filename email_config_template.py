"""
邮件服务配置文件模板

复制此文件为 email_config.py 并填入你的配置
"""

# QQ邮箱配置
EMAIL_ADDRESS = "your_email@qq.com"  # 你的 QQ 邮箱
EMAIL_AUTH_CODE = "your_auth_code"   # QQ 邮箱授权码（不是登录密码！）
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465
IMAP_SERVER = "imap.qq.com"

# 检查间隔（秒）
CHECK_INTERVAL = 30

# 邮件处理配置
SUBJECT_PREFIX = "[树洞]"  # 只处理这个前缀开头的邮件
MAX_POSTS_PER_SEARCH = 20  # 每次搜索最多处理的帖子数

# 如何获取 QQ 邮箱授权码：
# 1. 登录 QQ 邮箱网页版
# 2. 设置 -> 账户 -> POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务
# 3. 开启 IMAP/SMTP 服务
# 4. 生成授权码（不是你的 QQ 密码！）
