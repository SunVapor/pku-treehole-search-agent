"""
PKU Treehole RAG Agent

Main agent class implementing two retrieval modes:
1. Manual keyword search: User provides keywords directly
2. Auto keyword extraction: LLM extracts keywords from user query
"""

import json
import os
import re
import time
from typing import List, Dict, Any, Optional

import requests

from client import TreeholeClient
from utils import (
    format_posts_batch,
    save_json,
    load_json,
    get_cache_key,
    is_cache_valid,
    smart_truncate_posts,
    print_header,
    print_separator,
)

# Agent debug message prefix
AGENT_PREFIX = "[Agent] "

try:
    from config_private import (
        USERNAME,
        PASSWORD,
        DEEPSEEK_API_KEY,
        DEEPSEEK_API_BASE,
        DEEPSEEK_MODEL,
        MAX_SEARCH_RESULTS,
        MAX_CONTEXT_POSTS,
        MAX_COMMENTS_PER_POST,
        MAX_SEARCH_ITERATIONS,
        TEMPERATURE,
        MAX_RESPONSE_TOKENS,
        SEARCH_DELAY,
        ENABLE_CACHE,
        CACHE_DIR,
        CACHE_EXPIRATION,
    )
except ImportError:
    from config import (
        USERNAME,
        PASSWORD,
        DEEPSEEK_API_KEY,
        DEEPSEEK_API_BASE,
        DEEPSEEK_MODEL,
        MAX_SEARCH_RESULTS,
        MAX_CONTEXT_POSTS,
        MAX_COMMENTS_PER_POST,
        MAX_SEARCH_ITERATIONS,
        TEMPERATURE,
        MAX_RESPONSE_TOKENS,
        SEARCH_DELAY,
        ENABLE_CACHE,
        CACHE_DIR,
        CACHE_EXPIRATION,
    )


class TreeholeRAGAgent:
    """
    RAG Agent for PKU Treehole with DeepSeek integration.
    Supports manual and automatic keyword-based retrieval.
    """

    def __init__(self, interactive=True, cookies_file=None):
        """Initialize the agent with Treehole client and DeepSeek API.
        
        Args:
            interactive (bool): Whether to allow interactive prompts for login verification.
                              Set to False when running as a service.
            cookies_file (str): Path to user-specific cookies file. If None, uses default.
        """
        self.client = TreeholeClient(cookies_file=cookies_file)
        self.api_key = DEEPSEEK_API_KEY
        self.api_base = DEEPSEEK_API_BASE
        self.model = DEEPSEEK_MODEL
        self._all_comments_cache: Dict[int, List[Dict[str, Any]]] = {}
        self.stream_callback = None  # Optional callback for streaming output
        self.info_callback = None  # Callback for progress/info messages
        
        # Ensure login
        if not self.client.ensure_login(USERNAME, PASSWORD, interactive=interactive):
            raise RuntimeError("Failed to login to Treehole. Try running interactively first to save cookies.")
        
        # Create cache directory
        if ENABLE_CACHE:
            os.makedirs(CACHE_DIR, exist_ok=True)
        
        print(f"{AGENT_PREFIX}✓ 树洞 RAG Agent 初始化成功")

    def search_treehole(
        self, 
        keyword: str, 
        max_results: int = MAX_SEARCH_RESULTS,
        use_cache: bool = ENABLE_CACHE
    ) -> List[Dict[str, Any]]:
        """
        Search Treehole for posts matching keyword.
        
        Args:
            keyword (str): Search keyword.
            max_results (int): Maximum number of results to return.
            use_cache (bool): Whether to use cached results.
            
        Returns:
            list: List of post dictionaries.
        """
        # Check cache first
        if use_cache:
            cache_key = get_cache_key(keyword)
            cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
            
            if is_cache_valid(cache_file, CACHE_EXPIRATION):
                print(f"{AGENT_PREFIX}使用缓存结果: {keyword}")
                return load_json(cache_file)
        
        print(f"{AGENT_PREFIX}正在搜索树洞: {keyword}")
        
        # Call search API
        try:
            search_result = self.client.search_posts(
                keyword, 
                limit=max_results,
                comment_limit=10  # Get up to 10 comments per post from the search API
            )
            
            if search_result.get("success"):
                posts = search_result["data"]["data"]
                
                # The search API already includes comments in comment_list
                # We just need to ensure the format is consistent
                enriched_posts = []
                for post in posts[:max_results]:
                    # Comments are already included from the search API
                    # If you need ALL comments (not just the preview), uncomment below:
                    # if post.get("comment_total", 0) > len(post.get("comments", [])):
                    #     # Fetch all comments if needed
                    #     try:
                    #         comments_result = self.client.get_comment(post["pid"])
                    #         if comments_result.get("success"):
                    #             post["comments"] = comments_result["data"]["data"]
                    #     except Exception as e:
                    #         print(f"Warning: Failed to fetch all comments for post {post.get('pid')}: {e}")
                    
                    enriched_posts.append(post)
                
                # Cache results
                if use_cache:
                    save_json(enriched_posts, cache_file)
                
                msg = f"✓ 找到 {len(enriched_posts)} 个帖子"
                print(f"{AGENT_PREFIX}{msg}")
                if self.info_callback:
                    self.info_callback(msg)
                
                return enriched_posts
            else:
                msg = f"搜索失败: {search_result.get('message', '未知错误')}"
                print(f"{AGENT_PREFIX}{msg}")
                if self.info_callback:
                    self.info_callback(msg)
                return []
                
        except Exception as e:
            print(f"{AGENT_PREFIX}搜索树洞时出错: {e}")
            return []

    @staticmethod
    def parse_teacher_input(teacher_input: str) -> List[str]:
        """
        Parse teacher input string to a deduplicated list.
        Supports separators: comma/space/Chinese comma/slash/semicolon.
        """
        if not teacher_input:
            return []
        tokens = re.split(r"[,\s，、/;；]+", teacher_input.strip())
        teachers: List[str] = []
        seen = set()
        for token in tokens:
            teacher = token.strip()
            if teacher and teacher not in seen:
                seen.add(teacher)
                teachers.append(teacher)
        return teachers

    @staticmethod
    def _contains_keyword(text: str, keyword: str) -> bool:
        """
        Case-insensitive containment check for mixed Chinese/English text.
        Empty keyword always matches.
        """
        if not keyword:
            return True
        return keyword.lower() in (text or "").lower()

    @staticmethod
    def _build_course_search_keyword(course_abbr: str, teacher_keyword: str) -> str:
        """Build search query for course review."""
        parts = [course_abbr]
        if teacher_keyword:
            parts.append(teacher_keyword)
        parts.append("测评")
        return " ".join(parts)

    def _fetch_all_comments_for_post(self, post: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch all comments for a post, using in-memory cache to avoid
        repeated network calls across multi-teacher comparisons.
        """
        pid = post.get("pid")
        if not pid:
            return post.get("comments") or post.get("comment_list") or []

        if pid in self._all_comments_cache:
            return self._all_comments_cache[pid]

        comment_total = post.get("comment_total", 0)
        existing_comments = post.get("comments") or post.get("comment_list") or []
        all_comments = list(existing_comments)

        if comment_total > len(existing_comments):
            print(f"{AGENT_PREFIX}  正在获取帖子 #{pid} 的全部 {comment_total} 条评论...")
            comments_result = self.client.get_comment(pid, limit=100)

            if comments_result.get("success"):
                all_comments = comments_result["data"]["data"]
                last_page = comments_result["data"].get("last_page", 1)
                for page in range(2, last_page + 1):
                    page_result = self.client.get_comment(pid, page=page, limit=100)
                    if page_result.get("success"):
                        all_comments.extend(page_result["data"]["data"])
            else:
                all_comments = list(existing_comments)

        self._all_comments_cache[pid] = all_comments
        return all_comments

    def _extract_course_reviews_from_posts(
        self,
        posts: List[Dict[str, Any]],
        course_abbr: str,
        teacher_keyword: str = "",
    ) -> List[Dict[str, Any]]:
        """
        Extract course reviews from posts/comments with optional teacher filter.
        """
        course_reviews: List[Dict[str, Any]] = []
        seen_reviews = set()

        def add_review(review: Dict[str, Any]) -> None:
            text = (review.get("text") or "").strip()
            if not text:
                return
            key = (review.get("pid"), review.get("type"), text)
            if key in seen_reviews:
                return
            seen_reviews.add(key)
            course_reviews.append(review)

        for post in posts:
            pid = post.get("pid")
            post_text = post.get("text", "")
            post_has_course = course_abbr in post_text
            post_has_teacher = self._contains_keyword(post_text, teacher_keyword)
            post_relevant = post_has_course and post_has_teacher

            if post_relevant:
                add_review(
                    {
                        "pid": pid,
                        "type": "post",
                        "text": post_text,
                        "is_lz": True,
                    }
                )

            try:
                comments = self._fetch_all_comments_for_post(post)
                post["comments"] = comments

                for comment in comments:
                    comment_text = comment.get("text", "")
                    is_lz = comment.get("is_lz", 0) == 1
                    comment_has_course = course_abbr in comment_text
                    comment_has_teacher = self._contains_keyword(comment_text, teacher_keyword)

                    include_comment = False
                    if not teacher_keyword and is_lz:
                        include_comment = True
                    elif comment_has_course and comment_has_teacher:
                        include_comment = True
                    elif is_lz and post_relevant and (comment_has_course or comment_has_teacher):
                        include_comment = True

                    if include_comment:
                        add_review(
                            {
                                "pid": pid,
                                "type": "comment",
                                "text": comment_text,
                                "is_lz": is_lz,
                                "name_tag": comment.get("name_tag", "Anonymous"),
                            }
                        )

                time.sleep(0.05)  # Small delay between requests

            except Exception as e:
                print(f"{AGENT_PREFIX}  警告: 获取帖子 {pid} 的评论失败: {e}")
                continue

        return course_reviews

    def call_deepseek(
        self, 
        user_message: str, 
        system_message: Optional[str] = None,
        temperature: float = TEMPERATURE,
        stream: bool = True,
        callback: Optional[callable] = None
    ) -> str:
        """
        Call DeepSeek API for chat completion.
        
        Args:
            user_message (str): User's message.
            system_message (str): System message (optional).
            temperature (float): Temperature for generation.
            stream (bool): Whether to use streaming output.
            callback (callable): Optional callback function for streaming chunks.
            
        Returns:
            str: LLM response (accumulated if streaming).
        """
        messages = []
        
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        messages.append({"role": "user", "content": user_message})
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": MAX_RESPONSE_TOKENS,
            "stream": stream,
        }
        
        try:
            if stream:
                # Streaming response
                response = requests.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=120,
                    stream=True,
                )
                response.raise_for_status()
                
                full_content = ""
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            data_str = line_str[6:]
                            if data_str.strip() == '[DONE]':
                                break
                            try:
                                chunk = json.loads(data_str)
                                if 'choices' in chunk and len(chunk['choices']) > 0:
                                    delta = chunk['choices'][0].get('delta', {})
                                    content = delta.get('content', '')
                                    if content:
                                        # Use instance callback first, then parameter callback
                                        cb = self.stream_callback or callback
                                        if cb:
                                            cb(content)
                                        else:
                                            print(content, end='', flush=True)
                                        full_content += content
                            except json.JSONDecodeError:
                                continue
                
                if not (self.stream_callback or callback):
                    print()  # New line after streaming
                return full_content
            else:
                # Non-streaming response
                response = requests.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=60,
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
            
        except Exception as e:
            print(f"{AGENT_PREFIX}调用 DeepSeek API 时出错: {e}")
            return f"抱歉，调用 DeepSeek API 时出错: {e}"

    def mode_manual_search(self, keyword: str, user_question: str) -> Dict[str, Any]:
        """
        Mode 1: Manual keyword search.
        User provides keyword directly, agent searches and answers.
        
        Args:
            keyword (str): Search keyword provided by user.
            user_question (str): User's question.
            
        Returns:
            dict: Response containing answer and sources.
        """
        print_header("模式 1: 手动关键词检索")
        
        # Step 1: Search Treehole
        posts = self.search_treehole(keyword)
        
        if not posts:
            return {
                "answer": f"抱歉，没有找到关于「{keyword}」的相关树洞内容。",
                "keyword": keyword,
                "sources": [],
            }
        
        msg = f"✓ 找到 {len(posts)} 个帖子"
        print(f"{AGENT_PREFIX}{msg}")
        if self.info_callback:
            self.info_callback(msg)
        
        # Step 2: Select top posts for context (increased token limit)
        context_posts = smart_truncate_posts(posts[:MAX_CONTEXT_POSTS], max_comments=MAX_COMMENTS_PER_POST, max_tokens=10000)
        msg = f"✓ 使用 {len(context_posts)} 个帖子作为上下文"
        print(f"{AGENT_PREFIX}{msg}")
        if self.info_callback:
            self.info_callback(msg)
        
        # Step 3: Display retrieved content
        print_separator("-")
        print("\n【检索到的内容】\n")
        for i, post in enumerate(context_posts, 1):
            print(f"{i}. 帖子 #{post.get('pid')} - {post.get('text', '')[:60]}...")
            comments = post.get('comments') or post.get('comment_list') or []
            if comments:
                comment_info = f"前{MAX_COMMENTS_PER_POST}条" if MAX_COMMENTS_PER_POST > 0 else "全部"
                print(f"   评论数: {len(comments)} ({comment_info})")
        print_separator("-")
        
        # Step 4: Format posts as text
        context_text = format_posts_batch(context_posts, include_comments=True, max_comments=MAX_COMMENTS_PER_POST)
        
        # Step 5: Construct prompt
        system_message = """你是一个北大树洞问答助手。你的任务是根据提供的树洞帖子内容，回答用户的问题。

注意事项：
1. 只基于提供的树洞内容回答，不要编造信息
2. 如果树洞内容不足以回答问题，诚实地告知用户
3. 可以综合多个帖子的观点给出全面的回答
4. 保持客观，如果有不同观点要都提及
5. 回答要有条理，使用markdown格式时只能使用单级列表，不能出现多级列表"""

        user_message = f"""树洞内容：

{context_text}

---

用户问题：{user_question}

请基于以上树洞内容回答用户的问题。"""

        # Step 6: Call LLM with streaming
        print("\n【LLM回答】\n")
        answer = self.call_deepseek(user_message, system_message, stream=True)
        
        return {
            "answer": answer,
            "keyword": keyword,
            "sources": [{"pid": p.get("pid"), "text": p.get("text", "")[:100] + "..."} for p in context_posts],
            "num_sources": len(context_posts),
        }

    def mode_auto_search(self, user_question: str) -> Dict[str, Any]:
        """
        Mode 2: Automatic keyword extraction with intelligent iterative search.
        LLM can decide to search multiple times until satisfied.
        
        Args:
            user_question (str): User's question.
            
        Returns:
            dict: Response containing answer and sources.
        """
        print_header("模式 2: 智能自动检索（支持多轮搜索）")
        
        # Define the search tool for LLM
        search_tool = {
            "type": "function",
            "function": {
                "name": "search_treehole",
                "description": "在北大树洞中搜索相关帖子。如果当前信息不足以回答问题，可以使用不同的关键词多次调用此函数。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keyword": {
                            "type": "string",
                            "description": "搜索关键词，精准的1-2个词，不要包含多个概念"
                        },
                        "reason": {
                            "type": "string",
                            "description": "为什么需要搜索这个关键词（可选）"
                        }
                    },
                    "required": ["keyword"]
                }
            }
        }
        
        # Initialize conversation
        messages = [
            {
                "role": "system",
                "content": f"""你是一个北大树洞问答助手。你可以通过调用 search_treehole 函数来搜索树洞中的相关内容。

工作流程：
1. 分析用户问题，确定最核心的搜索关键词
2. 调用 search_treehole，关键词之间用空格连接
3. 分析搜索结果，判断信息是否足够
4. 如果信息不足，可以换用不同的关键词再次搜索
5. 信息充足后，基于所有搜索结果回答用户问题

注意事项：
- 每次调用只搜索1-2个关键词，且最好拆分为最基本的概念，例如"户外探索给分"拆分为"户外探索 给分"
- 只基于搜索到的树洞内容回答，不要编造信息
- 搜索次数建议不超过 {MAX_SEARCH_ITERATIONS/2} 次
- 如果树洞内容不足以回答问题，诚实地告知用户
- 保持客观，综合多个观点"""
            },
            {
                "role": "user",
                "content": f"用户问题：{user_question}"
            }
        ]
        
        all_searched_posts = []
        search_history = []  # 记录搜索历史
        search_count = 0
        max_searches = MAX_SEARCH_ITERATIONS
        
        msg = "✓ LLM 开始分析问题..."
        print(f"{AGENT_PREFIX}{msg}")
        if self.info_callback:
            self.info_callback(msg)
        
        # Iterative search loop
        while search_count < max_searches:
            # Call LLM with function calling
            response = self._call_deepseek_with_tools(messages, [search_tool], stream=False)
            
            # Check if LLM wants to use the search tool
            if response.get("tool_calls"):
                for tool_call in response["tool_calls"]:
                    if tool_call["function"]["name"] == "search_treehole":
                        search_count += 1
                        import json
                        args = json.loads(tool_call["function"]["arguments"])
                        keyword = args.get("keyword", "")
                        reason = args.get("reason", "")
                        
                        # 记录搜索历史
                        search_history.append({
                            "iteration": search_count,
                            "keyword": keyword,
                            "reason": reason
                        })
                        
                        # 临时禁用info_callback，避免search_treehole内部重复输出
                        temp_callback = self.info_callback
                        self.info_callback = None
                        
                        # Perform search - 每次搜索30个帖子（不再按总次数平均分配）
                        posts = self.search_treehole(keyword, max_results=min(MAX_SEARCH_RESULTS, 30))
                        all_searched_posts.extend(posts)
                        
                        # 恢复info_callback
                        self.info_callback = temp_callback
                        
                        # 合并搜索信息到一个消息
                        search_msg = f"[第{search_count}次搜索] 关键词: {keyword}"
                        if reason:
                            search_msg += f"\n搜索原因: {reason}"
                        search_msg += f"\n✓ 找到 {len(posts)} 个帖子"
                        
                        print(f"\n{AGENT_PREFIX}{search_msg}")
                        if self.info_callback:
                            self.info_callback(search_msg)
                        
                        # Format search results for LLM
                        if posts:
                            # 增加token限制以包含更多帖子
                            context_posts = smart_truncate_posts(posts[:30], max_comments=MAX_COMMENTS_PER_POST, max_tokens=8192)
                            context_text = format_posts_batch(context_posts, include_comments=True, max_comments=MAX_COMMENTS_PER_POST)
                            result_summary = f"搜索到 {len(posts)} 个帖子。以下是前 {len(context_posts)} 个：\n\n{context_text}"
                        else:
                            result_summary = f"未找到关于「{keyword}」的相关帖子。"
                        
                        # Add assistant's tool call and tool result to messages
                        # Note: omit 'content' key entirely when None (some API versions reject null)
                        assistant_msg = {
                            "role": "assistant",
                            "tool_calls": response["tool_calls"]
                        }
                        if response.get("content"):
                            assistant_msg["content"] = response["content"]
                        messages.append(assistant_msg)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "name": "search_treehole",
                            "content": result_summary
                        })
                        
                        time.sleep(SEARCH_DELAY)
                
                # Continue the loop to let LLM decide next action
                continue
            else:
                # LLM doesn't want to search anymore, prepare for final answer
                break
        else:
            # Max searches reached
            pass
        
        # Deduplicate all searched posts
        unique_posts = {post["pid"]: post for post in all_searched_posts}.values()
        unique_posts = list(unique_posts)
        
        msg = f"✓ 总共找到 {len(unique_posts)} 个不重复的帖子，正在生成回答..."
        print(f"\n{AGENT_PREFIX}{msg}")
        if self.info_callback:
            self.info_callback(msg)
        
        # Generate final answer with streaming, reusing the existing conversation context.
        # The messages list already contains all tool results (treehole posts), so we simply
        # append a final user turn asking for the answer — no need to re-send the posts.
        print_separator("-")
        print("\n【最终回答】\n")
        
        messages.append({
            "role": "user",
            "content": "好的，你已经完成了所有搜索。请现在基于你已经检索到的所有树洞内容，用中文给出完整、有条理的回答。只使用已检索到的内容，不要编造信息；如果信息不足请诚实说明。"
        })
        
        response = self._call_deepseek_with_tools(messages, tools=[], stream=True)
        final_answer = response.get("content") or ""
        
        print("\n")
        print_separator("-")
        
        return {
            "answer": final_answer,
            "search_count": search_count,
            "search_history": search_history,
            "keywords": [],
            "sources": [{"pid": p.get("pid"), "text": p.get("text", "")[:100] + "..."} for p in unique_posts[:20]],
            "num_sources": len(unique_posts),
        }
    
    def _call_deepseek_with_tools(self, messages: List[Dict], tools: List[Dict], stream: bool = False) -> Dict:
        """
        Call DeepSeek API with function calling support.
        
        Args:
            messages: Conversation messages.
            tools: Available tools/functions.
            stream: Whether to stream the response. When True and no tool_calls,
                    streams content via self.stream_callback and returns accumulated text.
            
        Returns:
            Response dict with content or tool_calls.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": TEMPERATURE,
            "max_tokens": MAX_RESPONSE_TOKENS,
            "stream": stream,
        }
        
        if tools:
            data["tools"] = tools
            data["tool_choice"] = "auto"
        
        try:
            if stream:
                response = requests.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=120,
                    stream=True,
                )
                response.raise_for_status()
                
                full_content = ""
                tool_calls_raw = None
                
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            data_str = line_str[6:]
                            if data_str.strip() == '[DONE]':
                                break
                            try:
                                chunk = json.loads(data_str)
                                if 'choices' in chunk and len(chunk['choices']) > 0:
                                    delta = chunk['choices'][0].get('delta', {})
                                    # 流式 tool_calls 在第一个 chunk 里
                                    if delta.get('tool_calls') and tool_calls_raw is None:
                                        tool_calls_raw = delta['tool_calls']
                                    content = delta.get('content', '')
                                    if content:
                                        if self.stream_callback:
                                            self.stream_callback(content)
                                        else:
                                            print(content, end='', flush=True)
                                        full_content += content
                            except json.JSONDecodeError:
                                continue
                
                if tool_calls_raw:
                    return {"content": None, "tool_calls": tool_calls_raw}
                return {"content": full_content, "tool_calls": None}
            else:
                response = requests.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=120,
                )
                response.raise_for_status()
                result = response.json()
                
                choice = result["choices"][0]
                message = choice["message"]
                
                return {
                    "content": message.get("content"),
                    "tool_calls": message.get("tool_calls"),
                }
            
        except requests.exceptions.HTTPError as e:
            error_detail = ""
            try:
                error_detail = e.response.json().get("error", {}).get("message", e.response.text)
            except Exception:
                error_detail = str(e)
            print(f"{AGENT_PREFIX}错误: DeepSeek API 调用失败 - {error_detail}")
            return {"content": None, "tool_calls": None}
        except Exception as e:
            print(f"{AGENT_PREFIX}错误: DeepSeek API 调用失败 - {e}")
            return {"content": None, "tool_calls": None}

    def mode_course_review(self, course_abbr: str, teacher_initials: str) -> Dict[str, Any]:
        """
        Mode 3: Single-teacher course review analysis.
        """
        parsed_teachers = self.parse_teacher_input(teacher_initials)
        if len(parsed_teachers) > 1:
            return self.mode_course_review_compare(course_abbr, parsed_teachers)

        teacher = parsed_teachers[0] if parsed_teachers else teacher_initials.strip()
        teacher_display = teacher if teacher else "未指定老师"

        print_header("模式 3: 课程测评分析")

        # Step 1: Construct search keyword
        search_keyword = self._build_course_search_keyword(course_abbr, teacher)
        msg = f"搜索关键词: {search_keyword}"
        print(f"{AGENT_PREFIX}{msg}")
        if self.info_callback:
            self.info_callback(msg)

        # Step 2: Search Treehole
        posts = self.search_treehole(search_keyword, max_results=MAX_SEARCH_RESULTS)

        if not posts:
            return {
                "answer": f"抱歉，没有找到关于「{course_abbr} {teacher_display}」课程的测评内容。",
                "course": course_abbr,
                "teacher": teacher,
                "sources": [],
            }

        msg = f"✓ 找到 {len(posts)} 个帖子"
        print(f"{AGENT_PREFIX}{msg}")
        if self.info_callback:
            self.info_callback(msg)

        # Step 3: Extract reviews
        msg = "✓ 正在从评论中提取课程测评..."
        print(f"{AGENT_PREFIX}{msg}")
        if self.info_callback:
            self.info_callback(msg)
        course_reviews = self._extract_course_reviews_from_posts(posts, course_abbr, teacher)

        if not course_reviews:
            return {
                "answer": f"找到了 {len(posts)} 个帖子，但没有发现包含「{course_abbr}」的详细测评内容。",
                "course": course_abbr,
                "teacher": teacher,
                "sources": [{"pid": p.get("pid")} for p in posts[:5]],
            }

        msg = f"✓ 提取到 {len(course_reviews)} 条与课程相关的测评"
        print(f"{AGENT_PREFIX}{msg}")
        if self.info_callback:
            self.info_callback(msg)

        # Step 4: Display retrieved reviews
        print_separator("-")
        print(f"\n【找到 {len(course_reviews)} 条课程测评】\n")

        for i, review in enumerate(course_reviews[:10], 1):
            lz_mark = "[洞主]" if review.get("is_lz") else ""
            text_preview = review["text"][:80].replace("\n", " ")
            print(f"{i}. {lz_mark} {review['type']} #{review['pid']}: {text_preview}...")

        if len(course_reviews) > 10:
            print(f"... 还有 {len(course_reviews) - 10} 条评论")

        print_separator("-")

        # Step 5: Format reviews for LLM
        reviews_text = ""
        for i, review in enumerate(course_reviews, 1):
            lz_mark = "[洞主]" if review.get("is_lz") else ""
            reviews_text += f"\n--- 评论 {i} {lz_mark} (帖子#{review['pid']}) ---\n"
            reviews_text += review["text"] + "\n"

        # Step 6: Construct analysis prompt
        system_message = f"""你是一个专业的课程评价分析助手。你的任务是仔细分析北大树洞中关于「{course_abbr}」课程（{teacher_display}）的所有测评，综合多方观点，给出全面的分析。

分析要求：
1. **课程难度**: 综合评估课程的难度水平，包括作业量、考试难度等
2. **教学质量**: 分析老师的授课方式、讲课清晰度、课堂互动等
3. **课程内容**: 评价课程内容的实用性、前沿性、趣味性等
4. **考核方式**: 总结作业、项目、考试等考核方式及其特点
5. **选课建议**: 基于不同学生需求（兴趣/学分/能力等），给出针对性建议
6. **注意事项**: 提醒需要注意的先修知识、时间投入等

要点：
- 客观呈现不同观点，包括正面和负面评价
- 如果评价有分歧，要明确指出并分析原因
- 使用markdown格式时只能使用单级列表，不能出现多级列表
- 引用具体评论时要注明
"""

        user_message = f"""以下是从北大树洞收集到的关于「{course_abbr}」课程（{teacher_display}）的所有测评内容：

{reviews_text}

---

请仔细分析以上所有测评，从课程难度、教学质量、课程内容、考核方式、选课建议等多个维度，给出全面、客观的分析和建议。"""

        # Step 7: Call LLM with streaming
        print(f"\n【课程「{course_abbr}」({teacher_display}) 综合分析】\n")
        answer = self.call_deepseek(user_message, system_message, stream=True)

        return {
            "answer": answer,
            "course": course_abbr,
            "teacher": teacher,
            "sources": [{"pid": r["pid"], "text": r["text"][:100] + "..."} for r in course_reviews[:10]],
            "num_sources": len(course_reviews),
        }

    def mode_course_review_compare(self, course_abbr: str, teachers: List[str]) -> Dict[str, Any]:
        """
        Mode 3B: Compare reviews of the same course across multiple teachers.
        """
        teacher_list: List[str] = []
        seen = set()
        for teacher in teachers:
            t = teacher.strip()
            if t and t not in seen:
                seen.add(t)
                teacher_list.append(t)

        if not teacher_list:
            return self.mode_course_review(course_abbr, "")
        if len(teacher_list) == 1:
            return self.mode_course_review(course_abbr, teacher_list[0])

        print_header("模式 3B: 同课多老师横向对比")
        print(f"{AGENT_PREFIX}目标课程: {course_abbr}")
        print(f"{AGENT_PREFIX}待对比老师: {', '.join(teacher_list)}")

        teacher_results: List[Dict[str, Any]] = []

        for teacher in teacher_list:
            search_keyword = self._build_course_search_keyword(course_abbr, teacher)
            print(f"\n{AGENT_PREFIX}[{teacher}] 搜索关键词: {search_keyword}")

            posts = self.search_treehole(search_keyword, max_results=MAX_SEARCH_RESULTS)
            if not posts:
                teacher_results.append(
                    {
                        "teacher": teacher,
                        "search_keyword": search_keyword,
                        "posts": [],
                        "reviews": [],
                    }
                )
                print(f"{AGENT_PREFIX}[{teacher}] 未找到帖子")
                continue

            print(f"{AGENT_PREFIX}[{teacher}] 找到 {len(posts)} 个帖子，提取测评中...")
            reviews = self._extract_course_reviews_from_posts(posts, course_abbr, teacher)
            print(f"{AGENT_PREFIX}[{teacher}] 提取到 {len(reviews)} 条测评")

            teacher_results.append(
                {
                    "teacher": teacher,
                    "search_keyword": search_keyword,
                    "posts": posts,
                    "reviews": reviews,
                }
            )

        valid_results = [item for item in teacher_results if item["reviews"]]
        if not valid_results:
            summary = "；".join(
                f"{item['teacher']}: {len(item['posts'])}帖/0测评" for item in teacher_results
            )
            return {
                "answer": f"抱歉，未能提取到「{course_abbr}」不同老师的有效测评。检索情况：{summary}",
                "course": course_abbr,
                "teachers": teacher_list,
                "sources": [],
                "num_sources": 0,
            }

        print_separator("-")
        print("\n【各老师测评提取结果】\n")
        for item in teacher_results:
            print(f"- {item['teacher']}: 帖子 {len(item['posts'])} 个，测评 {len(item['reviews'])} 条")
        print_separator("-")

        # Build grouped review context (truncate per teacher to control context size)
        max_reviews_per_teacher = 30
        max_review_chars = 600
        grouped_reviews_text = ""
        total_used_reviews = 0

        for item in valid_results:
            teacher = item["teacher"]
            reviews = item["reviews"]
            use_reviews = reviews[:max_reviews_per_teacher]
            total_used_reviews += len(use_reviews)

            grouped_reviews_text += f"\n===== 老师：{teacher} =====\n"
            grouped_reviews_text += f"搜索关键词：{item['search_keyword']}\n"
            grouped_reviews_text += f"帖子数：{len(item['posts'])}，测评数：{len(reviews)}\n"

            for i, review in enumerate(use_reviews, 1):
                lz_mark = "[洞主]" if review.get("is_lz") else ""
                review_text = review.get("text", "")
                if len(review_text) > max_review_chars:
                    review_text = review_text[:max_review_chars] + "..."
                grouped_reviews_text += (
                    f"\n--- {teacher} 评论{i} {lz_mark} (帖子#{review['pid']}) ---\n{review_text}\n"
                )

            if len(reviews) > max_reviews_per_teacher:
                grouped_reviews_text += (
                    f"\n[注] {teacher} 还有 {len(reviews) - max_reviews_per_teacher} 条测评未展开\n"
                )

        missing_teachers = [item["teacher"] for item in teacher_results if not item["reviews"]]
        missing_info = "、".join(missing_teachers) if missing_teachers else "无"

        system_message = f"""你是一个专业的课程评价对比助手。你需要横向比较同一门课程「{course_abbr}」在不同老师下的差异。

输出要求：
1. 先给每位老师单独总结（课程难度、教学质量、考核方式、作业负担、给分体感）。
2. 再做横向对比，明确差异点与共识点。
3. 如果数据不均衡（某位老师测评少），要提示结论置信度。
4. 最后给出按学生偏好分类的选课建议（如：追求高分、重视学习收获、时间有限）。
5. 引用具体评论时注明老师和帖子编号。
6. 使用markdown格式时只能使用单级列表，不能出现多级列表。
"""

        user_message = f"""以下是北大树洞中同一门课程「{course_abbr}」不同老师的测评内容（已按老师分组）：

{grouped_reviews_text}

---

没有提取到有效测评的老师：{missing_info}

请基于以上内容，输出客观、可比较的横向测评结论。"""

        print(f"\n【课程「{course_abbr}」多老师横向对比分析】\n")
        answer = self.call_deepseek(user_message, system_message, stream=True)

        teacher_stats = [
            {
                "teacher": item["teacher"],
                "num_posts": len(item["posts"]),
                "num_reviews": len(item["reviews"]),
            }
            for item in teacher_results
        ]
        sources = []
        for item in valid_results:
            teacher = item["teacher"]
            for review in item["reviews"][:5]:
                sources.append(
                    {
                        "teacher": teacher,
                        "pid": review["pid"],
                        "text": review["text"][:100] + "...",
                    }
                )

        return {
            "answer": answer,
            "course": course_abbr,
            "teachers": teacher_list,
            "teacher_stats": teacher_stats,
            "sources": sources,
            "num_sources": total_used_reviews,
            "comparison_mode": True,
        }

    def interactive_mode(self):
        """
        Interactive mode for testing the agent.
        """
        print_header("PKU Treehole RAG Agent - Interactive Mode")
        
        while True:
            print("\n选择模式:")
            print("  1 - 手动输入关键词检索")
            print("  2 - LLM自动生成关键词检索")
            print("  3 - LLM自动课程测评分析")
            print("  q - 退出\n")
            mode = input("请选择模式 (1/2/3/q): ").strip()
            
            if mode == 'q':
                print(f"{AGENT_PREFIX}正在退出...")
                break
            
            if mode not in ['1', '2', '3']:
                print(f"{AGENT_PREFIX}无效选择，请重试")
                continue
            
            if mode == '3':
                # Course review mode
                course_abbr = input("\n请输入课程缩写（如：计网、操统）: ").strip()
                if not course_abbr:
                    print(f"{AGENT_PREFIX}课程缩写不能为空")
                    continue
                
                teacher_initials = input("请输入老师姓名首字母（支持多个，用逗号/空格分隔，如：zhx,yyx）: ").strip()
                if not teacher_initials:
                    print(f"{AGENT_PREFIX}老师姓名首字母不能为空")
                    continue
                
                result = self.mode_course_review(course_abbr, teacher_initials)
            else:
                # Original modes
                user_question = input("\n请输入你的问题: ").strip()
                
                if not user_question:
                    print(f"{AGENT_PREFIX}问题不能为空")
                    continue
                
                if mode == '1':
                    keyword = input("请输入搜索关键词: ").strip()
                    if not keyword:
                        print(f"{AGENT_PREFIX}关键词不能为空")
                        continue
                    result = self.mode_manual_search(keyword, user_question)
                else:
                    result = self.mode_auto_search(user_question)


def main():
    """Main entry point."""
    try:
        agent = TreeholeRAGAgent()
        agent.interactive_mode()
    except KeyboardInterrupt:
        print("\n\n[Agent] 程序被用户中断")
    except Exception as e:
        print(f"\n[Agent] 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
