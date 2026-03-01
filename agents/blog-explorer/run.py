#!/usr/bin/env python3
"""
Blog Explorer - 抓取和存储 AI 公司博客内容
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# 添加 workspace 路径
workspace_path = Path("/opt/openclaw/.openclaw/workspace")
sys.path.insert(0, str(workspace_path / "skills" / "tavily" / "scripts"))

from tavily_search import search as tavily_search

# Blog 配置
BLOGS = {
    "openai": {
        "name": "OpenAI",
        "url": "https://openai.com/blog",
        "search_query": "site:openai.com/blog",
        "wiki_space": "7606015010138590169",
        "wiki_parent": "AI公司博客"
    },
    "anthropic": {
        "name": "Anthropic",
        "url": "https://www.anthropic.com/blog",
        "search_query": "site:anthropic.com/blog OR site:anthropic.com/news",
        "wiki_space": "7606015010138590169",
        "wiki_parent": "AI公司博客"
    },
    "langchain": {
        "name": "LangChain",
        "url": "https://blog.langchain.com",
        "search_query": "site:blog.langchain.com",
        "wiki_space": "7606015010138590169",
        "wiki_parent": "AI公司博客"
    },
    "manus": {
        "name": "Manus",
        "url": "https://www.manus.ai/blog",
        "search_query": "site:manus.ai/blog OR site:manus.im/blog",
        "wiki_space": "7606015010138590169",
        "wiki_parent": "AI公司博客"
    }
}

PROXY_URL = "http://localhost:7890"


def search_recent_posts(blog_key, hours=24):
    """搜索最近发布的文章"""
    config = BLOGS[blog_key]
    
    query = f"{config['search_query']} after:{hours}h"
    
    print(f"🔍 搜索 {config['name']} 的最新文章...")
    
    result = tavily_search(
        query=query,
        search_depth="basic",
        max_results=10,
        api_key=os.getenv("TAVILY_API_KEY")
    )
    
    if not result.get("success"):
        print(f"❌ 搜索失败: {result.get('error', 'Unknown error')}")
        return []
    
    posts = []
    for item in result.get("results", []):
        posts.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "snippet": item.get("content", ""),
            "published_date": item.get("publishedDate", ""),
            "score": item.get("score", 0)
        })
    
    print(f"✅ 找到 {len(posts)} 篇文章")
    return posts


def fetch_article_content(url, use_proxy=True):
    """获取文章的完整内容（通过代理）"""
    import subprocess
    try:
        from readability import Document
        has_readability = True
    except ImportError:
        has_readability = False
    
    print(f"📥 抓取文章: {url}")
    
    # 使用 curl 获取 HTML (通过代理)
    proxy_arg = f"-x {PROXY_URL}" if use_proxy else ""
    
    try:
        # 使用 curl 获取页面内容
        curl_cmd = ["curl", "-s", "-L", "-A", "Mozilla/5.0"]
        if use_proxy:
            curl_cmd.extend(["-x", PROXY_URL])
        curl_cmd.append(url)
        
        result = subprocess.run(
            curl_cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            html_content = result.stdout
            
            # 如果有 readability，提取主要内容
            if has_readability:
                doc = Document(html_content)
                content = doc.summary()
                # 简单的 HTML 转 Markdown
                import re
                # 移除 script 和 style
                content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
                content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
                # 转换一些基本标签
                content = re.sub(r'<h([1-6])[^>]*>(.*?)</h\1>', r'\n\#\# \2\n', content, flags=re.DOTALL)
                content = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', content, flags=re.DOTALL)
                content = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', content, flags=re.DOTALL)
                content = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', content, flags=re.DOTALL)
                content = re.sub(r'<br\s*/?>', '\n', content)
                content = re.sub(r'<[^>]+>', '', content)  # 移除剩余标签
                content = content.strip()
            else:
                # 简单提取：移除 HTML 标签
                import re
                content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
                content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
                content = re.sub(r'<[^>]+>', '\n', content)
                content = re.sub(r'\n\s*\n', '\n\n', content)
                content = content.strip()
            
            print(f"✅ 成功抓取，长度: {len(content)} 字符")
            return content
        else:
            print(f"❌ curl 失败: {result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        print(f"⏱️ 抓取超时")
        return None
    except Exception as e:
        print(f"❌ 抓取异常: {e}")
        return None


def parse_article_content(content, title, url):
    """解析文章内容，提取关键信息"""
    lines = content.split('\n')
    
    # 提取关键信息
    metadata = {
        "title": title,
        "url": url,
        "fetched_at": datetime.now().isoformat(),
        "word_count": len(content.split()),
        "char_count": len(content)
    }
    
    # 尝试提取摘要（前500字符）
    metadata["summary"] = content[:500] + "..." if len(content) > 500 else content
    
    return metadata


def create_feishu_document(blog_key, title, url, content, metadata):
    """在 Feishu 知识库创建文档"""
    from datetime import datetime
    
    company_name = BLOGS[blog_key]["name"]
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 格式化文档标题
    doc_title = f"{today}-{title[:50]}"  # 限制标题长度
    folder_name = company_name
    
    # 构建 Markdown 内容
    markdown_content = f"""# {title}

**来源**: {url}  
**发布时间**: {metadata.get('published_date', 'Unknown')}  
**抓取时间**: {metadata.get('fetched_at', '')}  
**字数**: {metadata.get('word_count', 0)} 词  

---

{content}

---

*本文由 Blog Explorer Agent 自动抓取和存储*
"""
    
    return markdown_content, doc_title, folder_name


def generate_daily_summary(all_posts):
    """生成每日简报"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    summary = f"""# AI 公司博客每日简报 - {today}

## 📊 今日统计

"""
    
    # 按公司分组
    by_company = {}
    for post in all_posts:
        company = post.get("company", "Unknown")
        if company not in by_company:
            by_company[company] = []
        by_company[company].append(post)
    
    # 统计
    for company, posts in by_company.items():
        summary += f"\n### {company}\n"
        summary += f"- 新文章数: **{len(posts)}** 篇\n"
        
        for post in posts[:5]:  # 只列出前5篇
            title = post.get("title", "Untitled")
            url = post.get("url", "")
            summary += f"  - [{title}]({url})\n"
    
    summary += f"\n## 🔗 所有文章链接\n\n"
    for post in all_posts:
        summary += f"- [{post.get('title', '')}]({post.get('url', '')}) - {post.get('company', '')}\n"
    
    return summary


def main():
    """主函数"""
    print("🦞 Blog Explorer Agent 启动")
    print(f"⏰ 开始时间: {datetime.now().isoformat()}")
    
    # 1. 搜索所有博客的最新文章
    all_recent_posts = []
    
    for blog_key in BLOGS.keys():
        print(f"\n{'='*60}")
        print(f"处理 {BLOGS[blog_key]['name']} 博客")
        print(f"{'='*60}")
        
        posts = search_recent_posts(blog_key, hours=24)
        
        # 添加公司信息
        for post in posts:
            post["company"] = BLOGS[blog_key]["name"]
            post["blog_key"] = blog_key
        
        all_recent_posts.extend(posts)
    
    print(f"\n{'='*60}")
    print(f"📊 总计找到 {len(all_recent_posts)} 篇新文章")
    print(f"{'='*60}\n")
    
    if not all_recent_posts:
        print("❌ 没有找到新文章")
        return
    
    # 2. 只处理今天的新文章（避免重复）
    # 这里简化处理：全部处理
    articles_to_process = all_recent_posts[:10]  # 限制处理数量
    
    print(f"📝 将处理 {len(articles_to_process)} 篇文章\n")
    
    # 3. 抓取和存储文章
    processed_articles = []
    
    for i, post in enumerate(articles_to_process, 1):
        print(f"\n[{i}/{len(articles_to_process)}] {post['title']}")
        print(f"URL: {post['url']}")
        print(f"发布时间: {post.get('published_date', 'Unknown')}")
        
        # 抓取内容
        content = fetch_article_content(post['url'], use_proxy=True)
        
        if content:
            metadata = parse_article_content(content, post['title'], post['url'])
            
            article_info = {
                "title": post['title'],
                "url": post['url'],
                "company": post['company'],
                "blog_key": post['blog_key'],
                "metadata": metadata,
                "content": content
            }
            
            processed_articles.append(article_info)
            print(f"✅ 文章处理完成\n")
        else:
            print(f"⏭️ 跳过此文章\n")
    
    # 4. 生成简报
    print(f"\n{'='*60}")
    print("📋 生成每日简报")
    print(f"{'='*60}\n")
    
    summary = generate_daily_summary([{
        "title": a["title"],
        "url": a["url"],
        "company": a["company"]
    } for a in processed_articles])
    
    # 保存简报到本地
    summary_path = workspace_path / "blog-daily-summary.md"
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary)
    
    print(f"✅ 简报已保存: {summary_path}")
    print(f"\n⏰ 完成时间: {datetime.now().isoformat()}")
    print("🦞 Blog Explorer Agent 完成")


if __name__ == "__main__":
    main()
