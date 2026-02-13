# Blog Explorer Agent

**Purpose**: 专门负责抓取、解析和存储 AI 公司博客内容

**职责**:
1. 监控 OpenAI、Anthropic、LangChain、Manus 的博客更新
2. 抓取最新文章的完整内容
3. 解析并提取关键信息（标题、发布时间、摘要、标签）
4. 存储到 Feishu 知识库
5. 生成每日简报

**目标博客**:
- OpenAI: https://openai.com/blog
- Anthropic: https://www.anthropic.com/blog
- LangChain: https://blog.langchain.com
- Manus: https://www.manus.ai/blog

**工具**:
- `tavily`: 搜索最新文章
- `web_fetch`: 抓取完整内容（通过代理 localhost:7890）
- `feishu_doc`: 写入到知识库
- `feishu_wiki`: 创建知识库节点

**工作流程**:
1. 使用 Tavily 搜索最近24小时的文章
2. 对每篇新文章，使用 web_fetch 获取完整内容
3. 解析 Markdown，提取关键信息
4. 在 Feishu 知识库创建/更新文档
5. 生成每日简报

**存储结构**:
```
知识库空间: 7606015010138590169
├── AI公司博客/
│   ├── OpenAI/
│   │   └── YYYY-MM-DD-文章标题.md
│   ├── Anthropic/
│   │   └── YYYY-MM-DD-文章标题.md
│   ├── LangChain/
│   │   └── YYYY-MM-DD-文章标题.md
│   └── Manus/
│       └── YYYY-MM-DD-文章标题.md
└── 每日简报/
    └── YYYY-MM-DD.md
```

**定时任务**:
- 每天 08:00 (Asia/Shanghai) 执行
- Job ID: 待创建
- Cron: `"0 8 * * *"` (每天早上8点)
