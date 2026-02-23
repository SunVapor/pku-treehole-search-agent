#!/usr/bin/env python3
"""
邮件机器人测试脚本

测试邮件解析和查询功能（不实际发送邮件）
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot_email import EmailBot

def test_parse_prompt():
    """测试 prompt 解析功能"""
    bot = EmailBot()
    
    print("=" * 60)
    print("测试 Prompt 解析功能")
    print("=" * 60)
    
    # 测试模式 1
    print("\n1. 测试模式 1 (手动关键词):")
    result = bot.parse_prompt("树洞 手动检索", "计网\n这门课怎么样？")
    print(f"   解析结果: {result}")
    assert result["mode"] == 1
    assert result["keyword"] == "计网"
    assert "这门课怎么样" in result["question"]
    print("   ✓ 通过")
    
    # 测试模式 2
    print("\n2. 测试模式 2 (自动提取):")
    result = bot.parse_prompt("树洞 自动检索", "我想了解计算机图形学")
    print(f"   解析结果: {result}")
    assert result["mode"] == 2
    assert "我想了解计算机图形学" in result["question"]
    print("   ✓ 通过")
    
    # 测试模式 3
    print("\n3. 测试模式 3 (课程测评):")
    result = bot.parse_prompt("树洞 课程测评", "计网\nhq")
    print(f"   解析结果: {result}")
    assert result["mode"] == 3
    assert result["course"] == "计网"
    assert result["teacher"] == "hq"
    print("   ✓ 通过")
    
    print("\n" + "=" * 60)
    print("所有测试通过！")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_parse_prompt()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
