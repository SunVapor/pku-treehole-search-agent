"""
Utility functions for PKU Treehole RAG Agent.
"""

import json
import os
import time
from datetime import datetime
from typing import List, Dict, Any


def format_post_to_text(post: Dict[str, Any], include_comments: bool = True) -> str:
    """
    Convert a post JSON to readable text format.
    
    Args:
        post (dict): Post data from Treehole API.
        include_comments (bool): Whether to include comments.
        
    Returns:
        str: Formatted text representation of the post.
    """
    lines = []
    
    # Post header
    pid = post.get("pid", "unknown")
    timestamp = post.get("timestamp", 0)
    time_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S") if timestamp else "unknown"
    
    lines.append(f"=== 帖子 #{pid} ===")
    lines.append(f"时间: {time_str}")
    
    # Post content
    text = post.get("text", "")
    lines.append(f"\n内容:\n{text}")
    
    # Post metadata
    likenum = post.get("likenum", 0)
    reply_count = post.get("reply", 0)
    lines.append(f"\n点赞: {likenum} | 回复: {reply_count}")
    
    # Tags if available
    if "tag" in post:
        lines.append(f"标签: {post['tag']}")
    
    # Comments
    if include_comments:
        # Support both 'comments' and 'comment_list' fields
        comments = post.get("comments") or post.get("comment_list") or []
        if comments:
            lines.append("\n--- 评论 ---")
            for i, comment in enumerate(comments[:5], 1):  # Limit to 5 comments
                comment_text = comment.get("text", "")
                comment_name = comment.get("name_tag", "Anonymous")
                lines.append(f"{i}. [{comment_name}] {comment_text}")
    
    lines.append("=" * 50)
    lines.append("")
    
    return "\n".join(lines)


def format_posts_batch(posts: List[Dict[str, Any]], include_comments: bool = False) -> str:
    """
    Convert multiple posts to text format.
    
    Args:
        posts (list): List of post dictionaries.
        include_comments (bool): Whether to include comments.
        
    Returns:
        str: Formatted text of all posts.
    """
    formatted_posts = []
    for post in posts:
        formatted_posts.append(format_post_to_text(post, include_comments))
    
    return "\n".join(formatted_posts)


def extract_keywords(text: str) -> List[str]:
    """
    Extract potential keywords from text.
    Simple implementation - can be enhanced with NLP.
    
    Args:
        text (str): Input text.
        
    Returns:
        list: List of keywords.
    """
    # Simple keyword extraction - split by common separators
    import re
    
    # Remove punctuation and split
    words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text)
    
    # Filter short words
    keywords = [w for w in words if len(w) >= 2]
    
    return keywords


def save_json(data: Any, filepath: str) -> None:
    """
    Save data to JSON file.
    
    Args:
        data: Data to save.
        filepath (str): Path to save file.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_json(filepath: str) -> Any:
    """
    Load data from JSON file.
    
    Args:
        filepath (str): Path to JSON file.
        
    Returns:
        Loaded data or None if file doesn't exist.
    """
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def get_cache_key(keyword: str, page: int = 1) -> str:
    """
    Generate cache key for search results.
    
    Args:
        keyword (str): Search keyword.
        page (int): Page number.
        
    Returns:
        str: Cache key.
    """
    import hashlib
    key_str = f"{keyword}_{page}"
    return hashlib.md5(key_str.encode()).hexdigest()


def is_cache_valid(cache_file: str, expiration: int) -> bool:
    """
    Check if cache file is still valid.
    
    Args:
        cache_file (str): Path to cache file.
        expiration (int): Expiration time in seconds.
        
    Returns:
        bool: True if cache is valid, False otherwise.
    """
    if not os.path.exists(cache_file):
        return False
    
    file_time = os.path.getmtime(cache_file)
    current_time = time.time()
    
    return (current_time - file_time) < expiration


def truncate_text(text: str, max_length: int = 1000) -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text (str): Input text.
        max_length (int): Maximum length.
        
    Returns:
        str: Truncated text.
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length] + "..."


def count_tokens_estimate(text: str) -> int:
    """
    Estimate token count (rough estimation).
    For Chinese: ~1.5 chars per token
    For English: ~4 chars per token
    
    Args:
        text (str): Input text.
        
    Returns:
        int: Estimated token count.
    """
    chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
    other_chars = len(text) - chinese_chars
    
    return int(chinese_chars / 1.5 + other_chars / 4)


def smart_truncate_posts(posts: List[Dict[str, Any]], max_tokens: int = 4000) -> List[Dict[str, Any]]:
    """
    Intelligently truncate posts to fit within token limit.
    
    Args:
        posts (list): List of posts.
        max_tokens (int): Maximum token limit.
        
    Returns:
        list: Truncated list of posts.
    """
    selected_posts = []
    total_tokens = 0
    
    for post in posts:
        post_text = format_post_to_text(post, include_comments=False)
        post_tokens = count_tokens_estimate(post_text)
        
        if total_tokens + post_tokens <= max_tokens:
            selected_posts.append(post)
            total_tokens += post_tokens
        else:
            break
    
    return selected_posts


def print_separator(char="=", length=80):
    """Print a separator line."""
    print(char * length)


def print_header(text: str):
    """Print a formatted header."""
    print_separator()
    print(f"  {text}")
    print_separator()
