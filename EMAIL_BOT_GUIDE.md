# 树洞邮件机器人使用指南

## 📧 邮件格式

### 模式 1: 手动关键词检索

**主题**: `[树洞] 课程咨询`

**正文**:
```
keyword:计网 这门课怎么样？
```

### 模式 2: 自动关键词提取

**主题**: `[树洞] 课程咨询`

**正文**:
```
我想了解计算机图形学这门课，作业多吗？
```

### 模式 3: 课程测评分析

**主题**: `[树洞] 课程测评`

**正文**:
```
course:计网 teacher:hq
```

## 🚀 部署方式

### 方法 1: 直接运行（测试用）

```bash
cd ~/pku-treehole-search-agent
bash start_email_bot.sh
```

按 Ctrl+C 停止。

### 方法 2: 使用 screen（后台运行）

```bash
# 安装 screen
sudo apt install screen -y

# 创建新会话
screen -S treehole-bot

# 启动机器人
cd ~/pku-treehole-search-agent
bash start_email_bot.sh

# 按 Ctrl+A 然后按 D 脱离会话（机器人继续运行）

# 重新连接
screen -r treehole-bot

# 查看所有会话
screen -ls

# 停止机器人：连接会话后按 Ctrl+C
```

### 方法 3: systemd 服务（开机自启）

```bash
# 部署为系统服务
cd ~/pku-treehole-search-agent
sudo bash deploy_service.sh

# 查看状态
sudo systemctl status treehole-email-bot

# 查看日志
tail -f ~/pku-treehole-search-agent/logs/bot.log

# 停止服务
sudo systemctl stop treehole-email-bot

# 重启服务
sudo systemctl restart treehole-email-bot
```

## 📊 监控和日志

### 查看实时日志

```bash
# 方法1: 使用 screen
screen -r treehole-bot

# 方法2: 使用 systemd 日志
tail -f ~/pku-treehole-search-agent/logs/bot.log

# 查看错误日志
tail -f ~/pku-treehole-search-agent/logs/bot.error.log
```

### 日志示例

```
[EmailBot] 邮件机器人启动中...
[EmailBot] 监听邮箱: 1902572878@qq.com
[EmailBot] 检查间隔: 30秒
[Agent] ✓ 树洞 RAG Agent 初始化成功
[EmailBot] 树洞 Agent 初始化成功
[EmailBot] 邮件机器人已启动，开始监听...
[EmailBot] 按 Ctrl+C 停止
[EmailBot] 发现 1 封未读邮件
[EmailBot] 处理邮件: [树洞] 课程咨询 (来自 user@example.com)
[EmailBot] 查询模式: 2
[EmailBot] 问题: 我想了解计算机图形学
[Agent] ✓ 正在从问题中提取关键词...
[Agent] ✓ 提取的关键词: ['计算机图形学']
[Agent] ✓ 找到 12 个不重复的帖子
[EmailBot] 已发送回复到 user@example.com
[EmailBot] 查询处理完成
```

## ⚙️ 配置修改

编辑 `email_config.py`:

```python
# 修改检查间隔（秒）
CHECK_INTERVAL = 60  # 改为 1 分钟检查一次

# 修改主题前缀
SUBJECT_PREFIX = "[BOT]"  # 只处理 [BOT] 开头的邮件

# 修改每次搜索的帖子数
MAX_POSTS_PER_SEARCH = 30
```

修改后需要重启服务：
```bash
sudo systemctl restart treehole-email-bot
```

## 🔧 故障排除

### 问题 1: 收不到回复

**检查**:
1. 邮件主题是否以 `[树洞]` 开头
2. 查看日志是否有错误: `tail -f logs/bot.log`
3. 检查邮箱授权码是否正确

### 问题 2: 服务无法启动

**检查**:
```bash
# 查看详细错误
sudo systemctl status treehole-email-bot -l

# 查看错误日志
cat logs/bot.error.log

# 手动测试
cd ~/pku-treehole-search-agent
python3 bot_email.py
```

### 问题 3: 回复内容出错

**检查**:
1. `config_private.py` 是否配置正确
2. DeepSeek API Key 是否有效
3. 网络连接是否正常

## 📱 手机使用示例

1. 在手机上打开 QQ 邮箱 APP
2. 写邮件给 `1902572878@qq.com`
3. 主题: `[树洞] 课程咨询`
4. 正文: `我想了解操作系统这门课`
5. 发送

几分钟后（检查间隔时间内）会收到回复邮件。

## 🔒 安全建议

1. **不要把授权码泄露给他人**
2. **定期更换授权码**
3. **可以设置白名单**（在 `bot_email.py` 中添加发件人过滤）
4. **监控日志**，及时发现异常

## 📈 性能优化

1. **调整检查间隔**: 减少不必要的检查
2. **启用缓存**: 避免重复搜索相同关键词
3. **限制邮件处理数量**: 防止同时处理过多邮件

## 🆘 获取帮助

如有问题，查看日志文件或联系管理员。
