# PKU Treehole Search Agent

基于北大树洞的 RAG（检索增强生成）智能问答系统，支持选课咨询、课程测评分析等功能。

**🆕 新功能：Web 图形界面** - 校园网内访问 `http://10.129.83.176:5000`，流式输出，实时可视化！  
**🆕 新功能：邮件机器人** - 通过邮件远程查询，随时随地获取课程信息！

## ⚡ 快速开始

### 方式 1: 命令行交互

```bash
git clone git@github.com:SunVapor/pku-treehole-search-agent.git
cd ./pku-treehole-search-agent
bash start.sh
```

### 方式 2: Web 图形界面 🆕⭐

**校园网内直接访问**: `http://10.129.83.176:5000`

或自行部署:
```bash
cd ~/pku-treehole-search-agent

# 部署为系统服务
sudo bash deploy_web_server.sh

# 访问地址
# 内网: http://10.129.83.176:5000
# 本机: http://localhost:5000
```

**特性**:
- ✅ 图形界面，无需命令行
- ✅ 实时流式输出
- ✅ 搜索过程可视化
- ✅ 任务队列管理
- ✅ 支持手机/平板/电脑

详见 [WEB_SERVER_README.md](WEB_SERVER_README.md)

### 方式 3: 邮件机器人 🆕

通过邮件远程查询，无需登录服务器！

```bash
cd ~/pku-treehole-search-agent/email_bot

# 1. 配置邮箱
cp email_config_template.py email_config.py
# 编辑 email_config.py 填入邮箱信息

# 2. 启动邮件机器人
bash start_email_bot.sh

# 或部署为系统服务（开机自启）
sudo bash deploy_service.sh
```

发送邮件到配置的邮箱，主题包含 `树洞` 即可自动回复！

详见 [email_bot/README.md](email_bot/README.md)

### 手动配置

1. **安装依赖**
   ```bash
   pip install requests
   ```

2. **配置账号**
   ```bash
   cp config.py config_private.py
   ```
   
   编辑 `config_private.py`：
   ```python
   USERNAME = "你的学号"
   PASSWORD = "你的密码"
   DEEPSEEK_API_KEY = "sk-xxx..."  # 从 https://platform.deepseek.com/ 获取
   ```

3. **运行 Agent**
   ```bash
   python3 agent.py
   ```

## 🎯 功能特性

### 三种智能模式

#### 模式 1: 手动关键词检索
- 用户提供关键词 + 问题
- 适合明确知道要搜什么的场景

#### 模式 2: 智能自动检索 🆕⭐
- **只需输入自然语言问题**
- **LLM 自主决策搜索策略**
- **支持多轮迭代搜索（最多 3 次）**
- **工作流程**：
  1. LLM 分析问题并决定搜索关键词
  2. 执行搜索并分析结果
  3. 如信息不足，LLM 可再次搜索（换用不同关键词）
  4. 迭代直至获取充分信息
  5. 综合所有搜索结果给出最终回答
- **类似 MCP 工具调用模式**：LLM 像使用工具一样调用搜索功能

#### 模式 3: 课程测评分析 ⭐
专门为选课设计的深度分析模式：
- **输入**: 课程缩写 + 老师首字母（如：`计网` + `hq`）
- **多老师横向对比**: 老师输入支持多个（如：`hq,zhx,yyx` 或 `hq zhx yyx`）
- **智能爬取**: 自动获取帖子的所有评论
- **智能筛选**: 优先洞主评论，筛选包含课程名的内容
- **多维分析**: 课程难度、教学质量、考核方式、选课建议等

### 核心特性

- ✅ 流式输出（实时显示 AI 回答）
- ✅ 检索内容预览（先看数据源，再看分析）
- ✅ 搜索结果缓存（避免重复请求）
- ✅ Cookie 持久化（免重复登录）
- ✅ 智能 Token 优化


## ⚙️ 配置说明

常用配置参数（在 `config_private.py` 中修改）：

```python
# 搜索配置
MAX_SEARCH_RESULTS = 40       # 每次搜索最多获取帖子数
MAX_CONTEXT_POSTS = 30        # 发送给 LLM 的最大帖子数
MAX_COMMENTS_PER_POST = 10    # 每个帖子最多包含评论数
MAX_SEARCH_ITERATIONS = 3     # 智能检索最大搜索次数 🆕

# LLM 配置
TEMPERATURE = 0.7             # 生成温度（0.0-1.0）
MAX_RESPONSE_TOKENS = 4096    # 最大响应长度

# 缓存配置
ENABLE_CACHE = True           # 是否启用缓存
CACHE_EXPIRATION = 86400      # 缓存过期时间（秒）
```

## 📁 项目结构

```
pku-treehole-search-agent/
├── README.md              # 项目文档
├── start.sh               # 一键启动脚本
├── config.py              # 配置模板
├── config_private.py      # 私有配置（自动创建）
├── client.py              # 树洞 API 客户端
├── agent.py               # RAG Agent 主逻辑
├── utils.py               # 工具函数
├── email_bot/             # 邮件机器人 🆕
│   ├── README.md          # 邮件机器人文档
│   ├── bot_email.py       # 邮件机器人主程序
│   ├── email_config_template.py  # 配置模板
│   └── ...                # 其他脚本和配置
└── data/cache/            # 搜索结果缓存
```

## 🔧 API 实现细节

### 树洞搜索 API

**端点**: `GET /chapi/api/v3/hole/list_comments`

**参数**:
- `keyword`: 搜索关键词
- `page`: 页码
- `limit`: 每页帖子数
- `comment_limit`: 每个帖子返回的评论数

**响应格式**:
```json
{
  "code": 20000,
  "data": {
    "list": [
      {
        "pid": 8001234,
        "text": "帖子内容",
        "comment_total": 45,
        "comment_list": [...]
      }
    ],
    "total": 15
  }
}
```

### 认证系统

#### 登录流程
1. **OAuth 登录**: `oauth_login(username, password)` → 获取 token
2. **SSO 登录**: `sso_login(token)` → 获取 authorization
3. **额外验证**（如需要）:
   - SMS 验证: `send_message()` + `login_by_message(code)`
   - Mobile Token: `login_by_token(code)` ⚠️ 注意：参数名为 `code`

#### Cookie 持久化
- Cookie 文件统一保存在 `~/.treehole_cookies.json`
- 跨项目目录共享（主程序和邮件机器人共用）
- 自动加载和保存，避免频繁登录

#### 非交互模式 🆕
```python
# 后台服务部署时使用非交互模式
agent = TreeholeRAGAgent(interactive=False)

# 交互模式（命令行使用）
agent = TreeholeRAGAgent(interactive=True)  # 默认
```

**用途**:
- `interactive=False`: 无法读取 stdin，登录失败时直接返回（适合systemd服务）
- `interactive=True`: 可以提示用户输入验证码/token（适合命令行）

**首次部署**:
```bash
# 1. 先交互式登录一次，保存 cookies
python3 agent.py

# 2. 然后部署为服务（会自动使用保存的 cookies）
cd email_bot && sudo bash deploy_service.sh
```

### 评论获取 API

**端点**: `GET /chapi/api/v3/hole/{pid}/comments`

**参数**:
- `page`: 页码
- `limit`: 每页评论数

**特性**:
- 课程测评模式会自动获取**所有评论**
- 支持分页，自动合并结果
- 筛选包含课程名的评论

## 🚨 故障排除

### 问题 1: 登录失败 / 需要令牌验证

**现象**: 登录时提示 "Mobile token:" 或 "请进行令牌验证"

**解决方案**:
```bash
# 删除旧 cookie
rm ~/.treehole_cookies.json

# 交互式重新登录
python3 agent.py

# 输入你的 PKU 手机令牌（6位数字，从 PKU Helper App 获取）
```

**邮件机器人部署**:
```bash
# 1. 先在命令行交互式登录，保存 cookies
python3 agent.py

# 2. 然后重启邮件机器人服务
sudo systemctl restart treehole-email-bot
```

### 问题 2: DeepSeek API 错误

**检查**:
- API Key 是否正确
- 网络连接是否正常
- 账户余额是否充足

### 问题 3: 搜索限流

**解决**: 增加请求延迟
```python
# 在 config_private.py 中
SEARCH_DELAY = 2.0  # 从 1.0 改为 2.0
```

### 问题 4: 邮件机器人无法启动

**检查日志**:
```bash
# 查看服务状态
sudo systemctl status treehole-email-bot

# 查看详细日志
tail -f ~/pku-treehole-search-agent/logs/bot.log
```

**常见原因**:
- **EOF when reading a line**: Cookies 已过期，需要交互式重新登录
- **Failed to login**: 检查 `config_private.py` 中的账号密码
- **IMAP/SMTP error**: 检查 `email_config.py` 中的邮箱授权码

## 💡 注意事项

1. **隐私安全**
   - `config_private.py` 已加入 `.gitignore`
   - 不要将包含密码的文件提交到 Git

2. **费用控制**
   - DeepSeek API 按 Token 计费
   - 通过 `MAX_CONTEXT_POSTS` 控制成本

3. **搜索缓存**
   - 默认缓存 24 小时
   - 缓存文件保存在 `data/cache/`

## 📝 开源协议

MIT License
