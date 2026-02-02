"""
示例：如何使用 TreeholeRAGAgent 进行编程调用

这个脚本展示了如何在你的代码中使用Agent，而不是交互式模式。
"""

from agent import TreeholeRAGAgent


def example_manual_search():
    """示例1：手动关键词检索"""
    print("\n" + "=" * 60)
    print("示例 1: 手动关键词检索")
    print("=" * 60)
    
    # 初始化Agent
    agent = TreeholeRAGAgent()
    
    # 使用手动关键词模式
    result = agent.mode_manual_search(
        keyword="计算机图形学",
        user_question="计算机图形学这门课怎么样？难度如何？"
    )
    
    # 打印结果
    print("\n【问题】计算机图形学这门课怎么样？难度如何？")
    print(f"\n【搜索关键词】{result['keyword']}")
    print(f"\n【回答】\n{result['answer']}")
    print(f"\n【参考来源】共 {result['num_sources']} 个帖子")
    for i, source in enumerate(result['sources'][:3], 1):
        print(f"  {i}. #{source['pid']}: {source['text']}")


def example_auto_search():
    """示例2：自动关键词提取"""
    print("\n" + "=" * 60)
    print("示例 2: 自动关键词提取")
    print("=" * 60)
    
    # 初始化Agent
    agent = TreeholeRAGAgent()
    
    # 使用自动提取模式
    result = agent.mode_auto_search(
        user_question="我想选一些AI和机器学习相关的课程，有什么推荐吗？"
    )
    
    # 打印结果
    print("\n【问题】我想选一些AI和机器学习相关的课程，有什么推荐吗？")
    print(f"\n【提取的关键词】{', '.join(result['keywords'])}")
    print(f"\n【回答】\n{result['answer']}")
    print(f"\n【参考来源】共 {result['num_sources']} 个帖子")


def example_batch_questions():
    """示例3：批量处理问题"""
    print("\n" + "=" * 60)
    print("示例 3: 批量处理多个问题")
    print("=" * 60)
    
    # 初始化Agent
    agent = TreeholeRAGAgent()
    
    # 准备问题列表
    questions = [
        ("人工智能", "人工智能导论这门课适合零基础的同学吗？"),
        ("数据结构", "数据结构与算法难不难？需要什么基础？"),
        ("操作系统", "操作系统课程的大作业工作量大吗？"),
    ]
    
    # 批量处理
    results = []
    for keyword, question in questions:
        print(f"\n处理问题: {question}")
        result = agent.mode_manual_search(keyword, question)
        results.append(result)
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("批量处理完成！")
    print("=" * 60)
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['keyword']}")
        print(f"   来源: {result['num_sources']} 个帖子")
        print(f"   回答预览: {result['answer'][:100]}...")


def example_custom_parameters():
    """示例4：自定义参数"""
    print("\n" + "=" * 60)
    print("示例 4: 使用自定义参数")
    print("=" * 60)
    
    # 初始化Agent
    agent = TreeholeRAGAgent()
    
    # 自定义搜索参数
    posts = agent.search_treehole(
        keyword="转专业",
        max_results=50,  # 获取更多结果
        use_cache=True   # 使用缓存
    )
    
    print(f"找到 {len(posts)} 个相关帖子")
    
    # 可以对这些帖子进行自定义处理
    # 例如：过滤、排序、分析等
    
    # 然后手动构造上下文并调用LLM
    from utils import format_posts_batch
    
    context = format_posts_batch(posts[:5])
    
    response = agent.call_deepseek(
        user_message=f"基于以下内容，总结一下转专业的难点：\n\n{context}",
        system_message="你是一个北大树洞分析助手",
        temperature=0.5  # 更加聚焦
    )
    
    print(f"\n【分析结果】\n{response}")


def example_search_only():
    """示例5：仅搜索，不调用LLM"""
    print("\n" + "=" * 60)
    print("示例 5: 仅搜索树洞内容")
    print("=" * 60)
    
    # 初始化Agent
    agent = TreeholeRAGAgent()
    
    # 搜索帖子
    posts = agent.search_treehole("选课攻略", max_results=20)
    
    print(f"找到 {len(posts)} 个帖子\n")
    
    # 直接处理原始数据
    for post in posts[:5]:
        print(f"帖子 #{post.get('pid')}")
        print(f"  内容: {post.get('text', '')[:80]}...")
        print(f"  点赞: {post.get('likenum', 0)} | 回复: {post.get('reply', 0)}")
        print()


def main():
    """运行所有示例"""
    print("PKU Treehole RAG Agent - 编程调用示例")
    print("=" * 60)
    print("\n⚠️  注意：运行这些示例前，请确保：")
    print("  1. 已配置 config_private.py")
    print("  2. 已实现 client.py 中的 search_posts() 函数")
    print("  3. 网络连接正常")
    print("\n选择要运行的示例：")
    print("  1 - 手动关键词检索")
    print("  2 - 自动关键词提取")
    print("  3 - 批量处理问题")
    print("  4 - 自定义参数")
    print("  5 - 仅搜索不调用LLM")
    print("  a - 运行所有示例")
    print("  q - 退出")
    
    choice = input("\n请选择 (1-5/a/q): ").strip().lower()
    
    if choice == 'q':
        return
    elif choice == '1':
        example_manual_search()
    elif choice == '2':
        example_auto_search()
    elif choice == '3':
        example_batch_questions()
    elif choice == '4':
        example_custom_parameters()
    elif choice == '5':
        example_search_only()
    elif choice == 'a':
        example_manual_search()
        example_auto_search()
        example_batch_questions()
        example_custom_parameters()
        example_search_only()
    else:
        print("无效选择")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
