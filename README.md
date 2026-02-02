# PKU Treehole Search Agent

基于北大树洞的检索增强智能问答系统，支持选课咨询、课程测评分析等功能。

## ⚡ 快速开始

### 一键启动（推荐）

```bash
git clone git@github.com:SunVapor/pku-treehole-search-agent.git
cd ./pku-treehole-search-agent
bash start.sh
```

脚本会自动：
1. 检查 Python 环境
2. 安装依赖
3. 引导你创建配置文件（输入学号、密码、API Key）

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

#### 模式 2: 自动关键词提取
- 只需输入自然语言问题
- AI 自动提取关键词并搜索

#### 模式 3: 课程测评分析 ⭐
专门为选课设计的深度分析模式：
- **输入**: 课程缩写 + 老师首字母（如：`计网` + `hq`）
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
MAX_SEARCH_RESULTS = 40    # 每次搜索最多获取帖子数
MAX_CONTEXT_POSTS = 30     # 发送给 LLM 的最大帖子数

# LLM 配置
TEMPERATURE = 0.7          # 生成温度（0.0-1.0）
MAX_RESPONSE_TOKENS = 4096 # 最大响应长度

# 缓存配置
ENABLE_CACHE = True        # 是否启用缓存
CACHE_EXPIRATION = 86400   # 缓存过期时间（秒）
```

## 📁 项目结构

```
pku-treehole-rag-agent/
├── README.md              # 项目文档
├── start.sh               # 一键启动脚本
├── config.py              # 配置模板
├── config_private.py      # 私有配置（自动创建）
├── client.py              # 树洞 API 客户端
├── agent.py               # RAG Agent 主逻辑
├── utils.py               # 工具函数
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

### 问题 1: 登录失败

**解决**:
```bash
rm cookies.json  # 删除旧 cookie
python3 agent.py  # 重新登录
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

