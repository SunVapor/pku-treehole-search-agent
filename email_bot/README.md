# 树洞邮件机器人

通过邮件远程查询北大树洞，随时随地获取课程信息！

## 📧 快速开始

### 1. 首次部署（重要！）

**⚠️ 必须先交互式登录一次，保存 cookies**:

```bash
# 在主项目目录运行
cd ~/pku-treehole-search-agent
python3 agent.py

# 按提示输入账号密码和 Mobile Token（6位数字）
# 登录成功后会保存 cookies 到 ~/.treehole_cookies.json
```

### 2. 配置邮箱

```bash
cd ~/pku-treehole-search-agent/email_bot
cp email_config_template.py email_config.py
# 编辑 email_config.py 填入你的邮箱和授权码
```

### 3. 启动机器人

```bash
# 测试运行
bash start_email_bot.sh

# 或部署为系统服务（开机自启）
sudo bash deploy_service.sh
```

### 4. 发送测试邮件

用手机发邮件到配置的邮箱，主题包含"树洞"，30秒内收到回复！

---

## 📮 邮件格式

### 模式 1: 手动检索 🔍

**主题**: `树洞 手动检索`（或包含"手动"）

**正文**（每行一个参数）:
```
计网
这门课怎么样？
```

- 第 1 行：关键词
- 第 2+ 行：你的问题

### 模式 2: 自动检索 🤖

**主题**: `树洞 自动检索`（或只包含"树洞"）

**正文**:
```
我想了解计算机图形学这门课，作业多吗？
```

- 直接写问题，AI 自动提取关键词

### 模式 3: 课程测评 📚

**主题**: `树洞 课程测评`（或包含"测评"/"课程"）

**正文**（每行一个参数）:
```
计网
hq
```

- 第 1 行：课程缩写
- 第 2 行：老师姓名首字母

---

## 🎯 主题识别规则

- 包含 **"手动"** → 手动检索模式
- 包含 **"测评"** 或 **"课程"** → 课程测评模式
- 其他（包含"树洞"）→ 自动检索模式（默认）

---

## 📱 手机使用示例

打开 QQ 邮箱 APP，写邮件：

**示例 1 - 快速查课程**:
```
主题: 树洞 自动检索
正文: 数据结构这门课怎么样
```

**示例 2 - 精确搜索**:
```
主题: 树洞 手动
正文:
人工智能
老师讲课清楚吗？
```

**示例 3 - 详细测评**:
```
主题: 树洞 测评
正文:
计网
hq
```

发送后，几分钟内收到 Markdown 格式的详细回复！

---

## 🚀 部署方式

### 方法 1: 直接运行（测试）

```bash
cd ~/pku-treehole-search-agent/email_bot
bash start_email_bot.sh
```

按 `Ctrl+C` 停止。

### 方法 2: Screen 后台运行

```bash
# 创建会话
screen -S treehole-bot

# 启动机器人
cd ~/pku-treehole-search-agent/email_bot
bash start_email_bot.sh

# Ctrl+A 然后 D 脱离（机器人继续运行）

# 重新连接
screen -r treehole-bot
```

### 方法 3: systemd 服务（推荐）

```bash
# 部署为系统服务
cd ~/pku-treehole-search-agent/email_bot
sudo bash deploy_service.sh

# 管理服务
sudo systemctl status treehole-email-bot   # 查看状态
sudo systemctl restart treehole-email-bot  # 重启
sudo systemctl stop treehole-email-bot     # 停止
```

---

## 📊 监控和日志

### 查看实时日志

```bash
# systemd 日志
tail -f ~/pku-treehole-search-agent/logs/bot.log

# 错误日志
tail -f ~/pku-treehole-search-agent/logs/bot.error.log

# screen 会话
screen -r treehole-bot
```

### 日志示例

```
[EmailBot] 邮件机器人启动中...
[EmailBot] 监听邮箱: your_email@qq.com
[EmailBot] 检查间隔: 30秒
[Agent] ✓ 树洞 RAG Agent 初始化成功
[EmailBot] 树洞 Agent 初始化成功
[EmailBot] 发现 1 封未读邮件
[EmailBot] 处理邮件: 树洞 自动检索 (来自 user@example.com)
[EmailBot] 查询模式: 2
[Agent] ✓ 找到 12 个不重复的帖子
[EmailBot] 已发送回复到 user@example.com
```

---

## ⚙️ 配置说明

编辑 `email_config.py`:

```python
# 邮箱配置
EMAIL_ADDRESS = "your_email@qq.com"
EMAIL_AUTH_CODE = "your_auth_code"  # QQ邮箱授权码

# 检查间隔（秒）
CHECK_INTERVAL = 30

# 主题关键词
SUBJECT_PREFIX = "树洞"

# 每次搜索的帖子数
MAX_POSTS_PER_SEARCH = 20
```

**获取 QQ 邮箱授权码**:
1. 登录 QQ 邮箱网页版
2. 设置 → 账户 → POP3/IMAP/SMTP 服务
3. 开启 IMAP/SMTP 服务
4. 生成授权码（不是 QQ 密码！）

---

## 🔧 故障排除

### 问题 1: 服务启动失败，日志显示 "EOF when reading a line"

**原因**: 服务运行在非交互模式，但 cookies 已过期，无法自动登录

**解决方案**:
```bash
# 1. 停止服务
sudo systemctl stop treehole-email-bot

# 2. 删除旧 cookies
rm ~/.treehole_cookies.json

# 3. 交互式登录，保存新 cookies
cd ~/pku-treehole-search-agent
python3 agent.py
# 输入 Mobile Token（6位数字）

# 4. 重启服务
sudo systemctl restart treehole-email-bot
```

### 问题 2: 收不到回复

**检查**:
1. 邮件主题是否包含"树洞"
2. 查看日志: `tail -f ~/pku-treehole-search-agent/logs/bot.log`
3. 检查邮箱授权码是否正确
4. 检查网络连接

### 问题 3: 服务无法启动

```bash
# 查看详细错误
sudo systemctl status treehole-email-bot -l

# 查看错误日志
cat ~/pku-treehole-search-agent/logs/bot.error.log

# 手动测试
cd ~/pku-treehole-search-agent/email_bot
python3 bot_email.py
```

### 问题 4: 回复内容出错

**检查**:
1. 主项目的 `config_private.py` 是否配置正确
2. DeepSeek API Key 是否有效
3. 树洞账号是否能正常登录
4. Cookies 文件 `~/.treehole_cookies.json` 是否存在且有效

---

## 📂 文件说明

```
email_bot/
├── README.md                      # 本文档
├── bot_email.py                   # 邮件机器人主程序
├── email_config_template.py       # 配置模板
├── email_config.py                # 邮箱配置（需自行创建）
├── start_email_bot.sh             # 启动脚本
├── deploy_service.sh              # systemd 部署脚本
├── treehole-email-bot.service     # systemd 服务配置
└── test_email_bot.py              # 测试脚本
```

**重要**:
- Cookies 文件统一保存在 `~/.treehole_cookies.json`（用户主目录）
- 主程序和邮件机器人共享同一个 cookies 文件
- 不再使用项目目录中的 `cookies.json` 文件

---

## 🔒 安全建议

1. ✅ `email_config.py` 已加入 `.gitignore`
2. ⚠️ 不要泄露邮箱授权码
3. 💡 定期更换授权码
4. 🔍 监控日志，及时发现异常
5. 🛡️ 可添加发件人白名单过滤

---

## 📈 性能优化

1. **调整检查间隔**: 减少频繁检查（`CHECK_INTERVAL = 60`）
2. **启用缓存**: 避免重复搜索（已自动启用）
3. **限制并发**: 防止同时处理过多邮件

---

## 🆘 获取帮助

如有问题:
1. 查看日志文件
2. 运行测试脚本: `python3 test_email_bot.py`
3. 检查主项目 README.md
4. 提交 GitHub Issue

---

## 📝 更新日志

### v2.0 - 新邮件格式
- ✨ 主题中指定模式
- ✨ 正文按行填写参数，无需参数名
- ✨ 更简洁直观的使用方式

### v1.0 - 初始版本
- ✅ 邮件监听和回复
- ✅ 三种查询模式
- ✅ systemd 服务支持
