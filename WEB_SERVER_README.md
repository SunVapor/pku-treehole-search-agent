# Web 界面服务

## 📱 快速访问

**校园网内访问**:
```
http://10.129.83.176:5000
```

用浏览器打开上述地址即可使用图形界面查询！

## ✨ 功能特性

### 三种查询模式

1. **手动检索** 🔍
   - 指定关键词
   - 输入你的问题
   - 适合明确搜索目标的场景

2. **智能检索** 🤖 (推荐)
   - 自然语言提问
   - AI 自动决策搜索策略
   - 支持多轮迭代搜索
   - 实时显示搜索过程

3. **课程测评** 📚
   - 输入课程 + 老师
   - 支持多老师横向对比
   - 深度测评分析

### 核心特性

- ✅ **任务队列**: 多人同时使用，自动排队处理
- ✅ **流式输出**: 实时显示 AI 回答过程
- ✅ **搜索可视化**: 清晰展示每次搜索的关键词和原因
- ✅ **响应式设计**: 支持手机、平板、电脑访问



## 🚀 部署和管理

### 部署为系统服务

```bash
cd ~/pku-treehole-search-agent
sudo bash deploy_web_server.sh
```

### 管理命令

```bash
# 查看服务状态
sudo systemctl status treehole-web-server

# 查看实时日志
tail -f ~/pku-treehole-search-agent/logs/web_server.log

# 重启服务
sudo systemctl restart treehole-web-server

# 停止服务
sudo systemctl stop treehole-web-server

# 查看队列统计
curl http://localhost:5000/api/queue
```

### 直接运行（调试模式）

```bash
cd ~/pku-treehole-search-agent
bash start_web_server.sh
```

## 📊 API 接口

### 提交任务

```http
POST /api/submit
Content-Type: application/json

{
  "mode": 2,
  "params": {
    "question": "你的问题"
  }
}
```

### 流式输出

```http
GET /api/stream/{task_id}
Accept: text/event-stream
```

返回 SSE 事件流：
```
data: {"type": "status", "message": "开始处理..."}
data: {"type": "search_history", "message": "..."}
data: {"type": "answer", "message": "...", "sources": 10}
data: {"type": "complete"}
```

### 查看队列

```http
GET /api/queue

Response:
{
  "queue_size": 2,
  "active_tasks": 1,
  "total_tasks": 15
}
```


## 📝 使用限制

- 同时活跃连接数: 无限制
- 单次查询超时: 120 秒
- 任务队列大小: 无限制
- SSE 心跳间隔: 30 秒

## 🐛 故障排查

### 无法访问页面

1. 检查服务状态:
   ```bash
   sudo systemctl status treehole-web-server
   ```

2. 检查端口占用:
   ```bash
   ss -tlnp | grep 5000
   ```

3. 查看错误日志:
   ```bash
   tail -50 ~/pku-treehole-search-agent/logs/web_server.error.log
   ```

### 查询无响应

1. 查看工作线程日志:
   ```bash
   tail -f ~/pku-treehole-search-agent/logs/web_server.log
   ```

2. 检查 Agent 是否正常初始化

3. 重启服务:
   ```bash
   sudo systemctl restart treehole-web-server
   ```


