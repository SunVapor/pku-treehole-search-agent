#!/usr/bin/env python3
"""
PKU Treehole Search Agent - Web Server
提供Web界面供校园网内访问
"""

import sys
import os
import json
import queue
import threading
import time
import secrets
from datetime import datetime
from flask import Flask, render_template, request, Response, jsonify, session
from flask_cors import CORS

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import TreeholeRAGAgent
from client import TreeholeClient

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(32))
CORS(app, supports_credentials=True)

# 任务队列
task_queue = queue.Queue()
# 存储活跃的SSE连接 {task_id: queue}
active_connections = {}
# 任务状态 {task_id: {"status": "pending/running/completed", "result": ...}}
task_status = {}
# 用户cookies存储目录
USER_COOKIES_DIR = os.path.join(os.path.dirname(__file__), "user_cookies")
os.makedirs(USER_COOKIES_DIR, exist_ok=True)

# 初始化默认Agent（用于未登录用户）
default_agent = None

def init_default_agent():
    """初始化默认Agent"""
    global default_agent
    try:
        default_agent = TreeholeRAGAgent(interactive=False)
        print("[Web Server] 默认Agent初始化成功")
        return True
    except Exception as e:
        print(f"[Web Server] 默认Agent初始化失败: {e}")
        return False

def get_user_cookies_file(user_id):
    """获取用户cookies文件路径"""
    return os.path.join(USER_COOKIES_DIR, f"user_{user_id}.json")

def create_user_agent(user_id):
    """为特定用户创建Agent实例"""
    try:
        cookies_file = get_user_cookies_file(user_id)
        agent = TreeholeRAGAgent(interactive=False, cookies_file=cookies_file)
        print(f"[Web Server] 用户 {user_id} 的Agent创建成功")
        return agent
    except Exception as e:
        print(f"[Web Server] 创建用户Agent失败: {e}")
        return None

def process_task(task_id, mode, params, user_id=None):
    """处理单个任务"""
    global task_status
    
    task_status[task_id]["status"] = "running"
    task_status[task_id]["start_time"] = datetime.now().isoformat()
    
    # 获取或创建Agent实例
    if user_id:
        agent = create_user_agent(user_id)
        if not agent:
            send_to_client(task_id, {
                "type": "error",
                "message": "创建用户Agent失败，请重新登录"
            })
            task_status[task_id]["status"] = "error"
            return
    else:
        agent = default_agent
        if not agent:
            send_to_client(task_id, {
                "type": "error",
                "message": "服务未初始化"
            })
            task_status[task_id]["status"] = "error"
            return
    
    # 创建流式输出回调
    def streaming_callback(content):
        """实时发送流式内容到客户端"""
        send_to_client(task_id, {
            "type": "stream",
            "content": content
        })
    
    # 创建进度信息回调
    def info_callback(message):
        """实时发送进度信息到客户端"""
        send_to_client(task_id, {
            "type": "info",
            "message": message
        })
    
    # 设置Agent的回调
    agent.stream_callback = streaming_callback
    agent.info_callback = info_callback
    
    # 发送开始消息
    send_to_client(task_id, {
        "type": "status",
        "message": "开始处理查询...",
        "status": "running"
    })
    
    try:
        result = None
        
        if mode == 1:
            # 手动检索
            keyword = params.get("keyword", "")
            question = params.get("question", "")
            
            send_to_client(task_id, {
                "type": "info",
                "message": f"模式: 手动检索\n关键词: {keyword}\n问题: {question}"
            })
            
            result = agent.mode_manual_search(keyword, question)
            
        elif mode == 2:
            # 智能自动检索
            question = params.get("question", "")
            
            send_to_client(task_id, {
                "type": "info",
                "message": f"模式: 智能自动检索\n问题: {question}"
            })
            
            # Hook agent的打印输出，转发到客户端
            result = agent.mode_auto_search(question)
            
            # 发送搜索历史
            if result.get("search_history"):
                history_msg = f"\n搜索过程 ({result['search_count']} 次):\n"
                for item in result["search_history"]:
                    history_msg += f"{item['iteration']}. {item['keyword']}"
                    if item.get('reason'):
                        history_msg += f" - {item['reason']}"
                    history_msg += "\n"
                send_to_client(task_id, {
                    "type": "search_history",
                    "message": history_msg
                })
            
        elif mode == 3:
            # 课程测评
            course = params.get("course", "")
            teacher = params.get("teacher", "")
            
            send_to_client(task_id, {
                "type": "info",
                "message": f"模式: 课程测评分析\n课程: {course}\n老师: {teacher}"
            })
            
            result = agent.mode_course_review(course, teacher)
        
        # 发送元数据（来源信息等）
        if result:
            send_to_client(task_id, {
                "type": "metadata",
                "sources": result.get("num_sources", 0)
            })
            
            task_status[task_id]["result"] = result
            task_status[task_id]["status"] = "completed"
        else:
            send_to_client(task_id, {
                "type": "error",
                "message": "未能获取结果"
            })
            task_status[task_id]["status"] = "error"
            
    except Exception as e:
        error_msg = f"处理出错: {str(e)}"
        send_to_client(task_id, {
            "type": "error",
            "message": error_msg
        })
        task_status[task_id]["status"] = "error"
        task_status[task_id]["error"] = str(e)
    
    finally:
        # 清除回调
        agent.stream_callback = None
        agent.info_callback = None
        send_to_client(task_id, {
            "type": "complete",
            "message": "查询完成"
        })
        task_status[task_id]["end_time"] = datetime.now().isoformat()

def send_to_client(task_id, data):
    """发送数据到指定客户端"""
    if task_id in active_connections:
        try:
            active_connections[task_id].put(data)
        except:
            pass

def worker_thread():
    """后台工作线程，处理队列中的任务"""
    print("[Web Server] 工作线程启动")
    
    while True:
        try:
            task = task_queue.get(timeout=1)
            task_id = task["task_id"]
            mode = task["mode"]
            params = task["params"]
            user_id = task.get("user_id")
            
            print(f"[Web Server] 开始处理任务 {task_id}, 模式 {mode}, 用户 {user_id or '未登录'}")
            process_task(task_id, mode, params, user_id)
            print(f"[Web Server] 任务 {task_id} 处理完成")
            
            task_queue.task_done()
            
        except queue.Empty:
            continue
        except Exception as e:
            print(f"[Web Server] 工作线程错误: {e}")
            continue

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/submit', methods=['POST'])
def submit_task():
    """提交查询任务"""
    data = request.json
    mode = data.get("mode", 2)
    params = data.get("params", {})
    
    # 从session获取user_id（如果已登录）
    user_id = session.get("user_id")
    
    # 生成任务ID
    task_id = f"{int(time.time() * 1000)}_{threading.get_ident()}"
    
    # 创建任务
    task = {
        "task_id": task_id,
        "mode": mode,
        "params": params,
        "user_id": user_id,
        "submit_time": datetime.now().isoformat()
    }
    
    # 添加到队列
    task_queue.put(task)
    
    # 初始化任务状态
    task_status[task_id] = {
        "status": "pending",
        "mode": mode,
        "params": params,
        "user_id": user_id,
        "submit_time": task["submit_time"]
    }
    
    return jsonify({
        "success": True,
        "task_id": task_id,
        "message": "任务已提交到队列"
    })

@app.route('/api/stream/<task_id>')
def stream(task_id):
    """SSE流式输出"""
    def generate():
        # 创建消息队列
        msg_queue = queue.Queue()
        active_connections[task_id] = msg_queue
        
        try:
            # 发送初始连接消息
            yield f"data: {json.dumps({'type': 'connected', 'task_id': task_id})}\n\n"
            
            # 持续发送消息
            while True:
                try:
                    msg = msg_queue.get(timeout=30)  # 30秒超时
                    yield f"data: {json.dumps(msg)}\n\n"
                    
                    # 如果是完成消息，退出
                    if msg.get("type") == "complete":
                        break
                        
                except queue.Empty:
                    # 发送心跳
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                    
        finally:
            # 清理连接
            if task_id in active_connections:
                del active_connections[task_id]
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/status/<task_id>')
def get_status(task_id):
    """获取任务状态"""
    if task_id in task_status:
        return jsonify({
            "success": True,
            "status": task_status[task_id]
        })
    else:
        return jsonify({
            "success": False,
            "message": "任务不存在"
        }), 404

@app.route('/api/queue')
def get_queue_status():
    """获取队列状态"""
    return jsonify({
        "queue_size": task_queue.qsize(),
        "active_tasks": len(active_connections),
        "total_tasks": len(task_status)
    })

@app.route('/api/login', methods=['POST'])
def login():
    """用户登录树洞"""
    data = request.json
    username = data.get("username")
    password = data.get("password")
    
    if not username or not password:
        return jsonify({
            "success": False,
            "message": "用户名和密码不能为空"
        }), 400
    
    try:
        # 生成用户ID（使用username作为唯一标识）
        import hashlib
        user_id = hashlib.md5(username.encode()).hexdigest()[:16]
        
        # 创建用户特定的cookies文件
        cookies_file = get_user_cookies_file(user_id)
        
        # 创建临时client进行登录
        client = TreeholeClient(cookies_file=cookies_file)
        
        # 尝试OAuth登录
        result = client.oauth_login(username, password)
        
        if result.get("success") == "true" or result.get("success") == True:
            # 登录成功，执行SSO登录获取token
            token = result.get("token")
            if token:
                sso_response = client.sso_login(token)
                # 保存cookies
                client.save_cookies()
                
                # 设置session
                session['user_id'] = user_id
                session['username'] = username
                session.permanent = True  # 使session持久化
                
                return jsonify({
                    "success": True,
                    "message": "登录成功",
                    "username": username
                })
            else:
                return jsonify({
                    "success": False,
                    "message": "登录失败：未获取到token"
                }), 401
        else:
            return jsonify({
                "success": False,
                "message": result.get("msg", "登录失败，请检查用户名和密码")
            }), 401
            
    except Exception as e:
        print(f"[Web Server] 登录错误: {e}")
        return jsonify({
            "success": False,
            "message": f"登录出错: {str(e)}"
        }), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    """用户登出"""
    user_id = session.get('user_id')
    if user_id:
        # 可选：删除用户cookies文件
        # cookies_file = get_user_cookies_file(user_id)
        # if os.path.exists(cookies_file):
        #     os.remove(cookies_file)
        
        session.clear()
        return jsonify({
            "success": True,
            "message": "登出成功"
        })
    else:
        return jsonify({
            "success": False,
            "message": "未登录"
        }), 400

@app.route('/api/login_by_token', methods=['POST'])
def login_by_token():
    """使用Token直接登录"""
    data = request.json
    token = data.get("token")
    
    if not token:
        return jsonify({
            "success": False,
            "message": "Token不能为空"
        }), 400
    
    try:
        # 生成用户ID（使用token的hash作为唯一标识）
        import hashlib
        user_id = hashlib.md5(token.encode()).hexdigest()[:16]
        
        # 创建用户特定的cookies文件
        cookies_file = get_user_cookies_file(user_id)
        
        # 创建临时client
        client = TreeholeClient(cookies_file=cookies_file)
        
        # 直接设置token到session和cookies
        client.authorization = token
        client.session.cookies.update({"pku_token": token})
        client.session.headers.update({"authorization": f"Bearer {token}"})
        
        # 验证token是否有效（尝试获取未读消息）
        try:
            test_response = client.un_read()
            if test_response.status_code != 200:
                return jsonify({
                    "success": False,
                    "message": "Token无效或已过期"
                }), 401
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"Token验证失败: {str(e)}"
            }), 401
        
        # Token有效，保存cookies
        client.save_cookies()
        
        # 设置session
        session['user_id'] = user_id
        session['username'] = f"Token用户({user_id})"
        session.permanent = True  # 使session持久化
        
        return jsonify({
            "success": True,
            "message": "Token登录成功",
            "username": session['username']
        })
            
    except Exception as e:
        print(f"[Web Server] Token登录错误: {e}")
        return jsonify({
            "success": False,
            "message": f"登录出错: {str(e)}"
        }), 500

@app.route('/api/check_login')
def check_login():
    """检查登录状态"""
    user_id = session.get('user_id')
    username = session.get('username')
    
    if user_id:
        return jsonify({
            "logged_in": True,
            "username": username
        })
    else:
        return jsonify({
            "logged_in": False
        })

def main():
    """主函数"""
    print("=" * 60)
    print("PKU Treehole Search Agent - Web Server")
    print("=" * 60)
    
    # 初始化默认Agent
    if not init_default_agent():
        print("[Web Server] 默认Agent初始化失败，请检查配置")
        return
    
    # 启动工作线程
    worker = threading.Thread(target=worker_thread, daemon=True)
    worker.start()
    
    # 启动Web服务器
    host = "0.0.0.0"  # 监听所有接口
    port = 5000
    
    print(f"\n[Web Server] 服务器启动成功！")
    print(f"[Web Server] 内网访问地址: http://10.129.83.176:{port}")
    print(f"[Web Server] 本地访问地址: http://localhost:{port}")
    print(f"\n按 Ctrl+C 停止服务器\n")
    
    app.run(host=host, port=port, debug=False, threaded=True)

if __name__ == "__main__":
    main()
