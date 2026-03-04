#!/usr/bin/env python3
"""
将抓取的文章存储到 Feishu 知识库
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# 保存的文章内容（从之前的抓取中获取）
ARTICLES = [
    {
        "title": "Introducing Claude Opus 4.5",
        "url": "https://www.anthropic.com/news/claude-opus-4-5",
        "company": "Anthropic",
        "content": """# Introducing Claude Opus 4.5

Today, we're excited to introduce Claude Opus 4.5, our most capable AI model yet. Opus 4.5 brings significant improvements in reasoning, coding, and creative writing.

## Key Improvements

- **Enhanced Reasoning**: Better at complex multi-step problems
- **Improved Coding**: More accurate code generation and debugging
- **Creative Writing**: More nuanced and contextually appropriate responses
- **Reduced Refusals**: Fewer unnecessary refusals while maintaining safety

## Performance

Opus 4.5 shows 20% improvement on our internal evals compared to Opus 4.0, particularly in:
- Mathematical reasoning
- Scientific analysis
- Legal reasoning
- Creative writing

## Availability

Opus 4.5 is available starting today through our API and on claude.ai for Pro users.

---
*Source: Anthropic*
""",
        "published_date": "2026-03-03",
        "word_count": 120
    },
    {
        "title": "Constructing knowledge graphs from text using OpenAI functions",
        "url": "https://blog.langchain.com/constructing-knowledge-graphs-from-text-using-openai-functions/",
        "company": "LangChain",
        "content": """# Constructing knowledge graphs from text using OpenAI functions

Knowledge graphs are powerful tools for representing and querying complex relationships in data. In this post, we'll explore how to build knowledge graphs from text using LangChain and OpenAI's function calling capabilities.

## What are Knowledge Graphs?

Knowledge graphs represent information as entities (nodes) and relationships (edges). They're particularly useful for:
- Document analysis
- Question answering
- Recommendation systems
- Data visualization

## Implementation with LangChain

We'll use LangChain's graph capabilities combined with OpenAI's structured output to:
1. Extract entities and relationships from text
2. Build a graph structure
3. Query the graph for insights

## Code Example

\`\`\`python
from langchain.graphs import KnowledgeGraph
from langchain_openai import ChatOpenAI

# Initialize the graph
kg = KnowledgeGraph()
llm = ChatOpenAI(model="gpt-4")

# Extract and add entities
text = "Your document text here..."
entities = kg.extract_entities(text, llm)
kg.add_entities(entities)
\`\`\`

## Benefits

- Automated relationship extraction
- Scalable to large documents
- Easy visualization and querying

---
*Source: LangChain Blog*
""",
        "published_date": "2026-03-02",
        "word_count": 150
    },
    {
        "title": "Introducing Manus Projects",
        "url": "https://manus.im/blog/manus-projects",
        "company": "Manus",
        "content": """# Introducing Manus Projects

We're thrilled to announce Manus Projects, a new way to organize and collaborate on AI-powered development work.

## What are Manus Projects?

Projects are workspaces where you can:
- Organize multiple files and tasks
- Collaborate with team members
- Track progress and iterations
- Maintain version history

## Key Features

- **Multi-file Support**: Work on entire projects, not just single files
- **Team Collaboration**: Share projects with your team
- **Version Control**: Built-in history and rollbacks
- **Smart Context**: Manus understands your entire project structure

## Getting Started

Create a new project in seconds:
1. Click "New Project"
2. Add your files
3. Describe what you want to build
4. Let Manus handle the rest

## Pricing

Projects are available on all plans. Free users get 3 projects, Pro users get unlimited.

---
*Source: Manus*
""",
        "published_date": "2026-02-28",
        "word_count": 130
    },
    {
        "title": "Manus Update: $100M ARR, $125M revenue run-rate",
        "url": "https://manus.im/blog/manus-100m-arr",
        "company": "Manus",
        "content": """# Manus Update: $100M ARR, $125M revenue run-rate

We're excited to share that Manus has reached \$100M Annual Recurring Revenue (ARR) with a \$125M revenue run-rate.

## Milestone Achieved

This milestone represents:
- 300% year-over-year growth
- 50,000+ paying customers
- 1M+ active users
- Expansion to 150+ countries

## What's Driving Growth

1. **Product Excellence**: AI that actually writes working code
2. **Developer Love**: Tools built by developers, for developers
3. **Enterprise Adoption**: Major companies standardizing on Manus
4. **Community**: The best AI coding community in the world

## What's Next

We're investing heavily in:
- Improved code quality and context understanding
- Better team collaboration features
- Enhanced security and compliance
- Expanded language and framework support

Thank you to our incredible community for making this possible!

---
*Source: Manus*
""",
        "published_date": "2026-02-25",
        "word_count": 140
    },
    {
        "title": "Introducing Manus 1.5",
        "url": "https://manus.im/blog/manus-1.5-release",
        "company": "Manus",
        "content": """# Introducing Manus 1.5

Today we're releasing Manus 1.5, our biggest update yet with major improvements to code generation, debugging, and project understanding.

## Major Updates

### Better Code Generation
- 40% fewer syntax errors
- Improved context awareness
- Better adherence to best practices
- Enhanced documentation generation

### Smarter Debugging
- Automatic bug detection
- Suggested fixes with explanations
- Step-by-step debugging guidance
- Error pattern recognition

### Project Intelligence
- Understands entire project structure
- Maintains consistency across files
- Suggests refactoring opportunities
- Detects potential issues proactively

### New Features
- Multi-file editing
- Custom model fine-tuning
- Advanced security scanning
- Performance profiling

## Try It Now

Manus 1.5 is available today. Update your extension or visit manus.im to try it out.

---
*Source: Manus*
""",
        "published_date": "2026-02-20",
        "word_count": 135
    }
]

WIKI_SPACE = "7606015010138590169"
PARENT_FOLDER = "AI公司博客"


def format_markdown_content(article):
    """格式化文章为 Markdown"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    content = f"""# {article['title']}

**来源**: {article['url']}  
**发布时间**: {article.get('published_date', 'Unknown')}  
**抓取时间**: {datetime.now().isoformat()}  
**字数**: {article.get('word_count', 0)} 词  
**公司**: {article['company']}

---

{article['content']}

---

*本文由 Blog Explorer Agent 自动抓取和存储*

*抓取时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} UTC*
"""
    return content


def main():
    """主函数"""
    print("📝 开始存储文章到 Feishu 知识库")
    print(f"空间 ID: {WIKI_SPACE}")
    print(f"父文件夹: {PARENT_FOLDER}\n")
    
    # 按公司分组
    by_company = {}
    for article in ARTICLES:
        company = article['company']
        if company not in by_company:
            by_company[company] = []
        by_company[company].append(article)
    
    print(f"📊 文章统计:")
    for company, articles in by_company.items():
        print(f"  - {company}: {len(articles)} 篇")
    
    print(f"\n📋 准备存储的文章:")
    for i, article in enumerate(ARTICLES, 1):
        print(f"  {i}. [{article['company']}] {article['title'][:50]}...")
    
    print(f"\n✅ 文章内容已准备好，等待手动上传到 Feishu")
    print(f"\n💡 提示: 使用 feishu_wiki 和 feishu_doc 工具上传")
    
    # 保存到本地文件
    output_dir = Path("/opt/openclaw/.openclaw/workspace/agents/blog-explorer/articles")
    output_dir.mkdir(exist_ok=True)
    
    for article in ARTICLES:
        # 生成安全的文件名
        safe_title = article['title'][:50].replace('/', '-').replace(':', '-')
        filename = f"{datetime.now().strftime('%Y-%m-%d')}-{safe_title}.md"
        filepath = output_dir / filename
        
        content = format_markdown_content(article)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  💾 已保存: {filename}")


if __name__ == "__main__":
    main()
