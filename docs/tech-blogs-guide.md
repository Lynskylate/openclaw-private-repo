# AI 公司博客获取指南

## 概述

本文档记录了如何获取 OpenAI、Anthropic、LangChain 和 Manus 四家 AI 公司的官方博客内容。

## 博客列表

### 1. OpenAI Blog

**主博客**: https://openai.com/blog
**开发者博客**: https://developers.openai.com/blog/
**新闻页**: https://openai.com/news/

**RSS 订阅**:
- 历史地址: `https://openai.com/blog/rss.xml` (网站改版后可能失效)
- 社区反馈: https://community.openai.com/t/openai-website-rss-feed-inquiry/733747

**内容类型**:
- 产品发布 (GPT模型更新)
- 研究论文
- AI安全与政策
- 技术教程

**获取方式**:
```bash
# 使用 Tavily 搜索最新文章
python3 /opt/openclaw/.openclaw/workspace/skills/tavily/scripts/tavily_search.py \
  "site:openai.com/blog OR site:openai.com/news" \
  --topic news \
  --max-results 10

# 使用 web_fetch 提取文章内容
web_fetch https://openai.com/blog/article-name
```

---

### 2. Anthropic Blog

**主博客**: https://www.anthropic.com/blog
**新闻页**: https://www.anthropic.com/news

**内容分类**:
- Research (研究论文)
- News (公司新闻)
- Product Updates (产品更新)
- AI Safety (AI安全)

**特色专栏**:
- Claude's Constitution: https://www.anthropic.com/constitution
- Transparency: https://www.anthropic.com/transparency

**获取方式**:
```bash
# 使用 Tavily 搜索最新文章
python3 /opt/openclaw/.openclaw/workspace/skills/tavily/scripts/tavily_search.py \
  "site:anthropic.com/blog OR site:anthropic.com/news" \
  --topic news \
  --max-results 10

# 使用 web_fetch 提取文章内容
web_fetch https://www.anthropic.com/news/article-name
```

---

### 3. LangChain Blog

**主博客**: https://blog.langchain.com/
**GitHub**: https://github.com/langchain-ai

**内容类型**:
- LangChain/LangGraph 更新
- 多智能体架构
- 技术教程
- 产品发布
- Newsletter (月刊)

**获取方式**:
```bash
# 使用 Tavily 搜索最新文章
python3 /opt/openclaw/.openclaw/workspace/skills/tavily/scripts/tavily_search.py \
  "site:blog.langchain.com" \
  --topic news \
  --max-results 10

# 使用 web_fetch 提取文章内容
web_fetch https://blog.langchain.com/article-name
```

**作者页面**: https://www.blog.langchain.com/author/langchain/

---

### 4. Manus Blog (Meta)

**主博客**: https://www.manus.ai/blog
**主页**: https://manus.ai/

**背景**:
- Manus 已被 Meta 收购
- 定位: "Hands On AI" - 任务执行引擎
- Reddit社区: https://www.reddit.com/r/ManusOfficial/

**内容类型**:
- 产品发布 (Manus 1.5等)
- 任务自动化
- AI工具链

**获取方式**:
```bash
# 使用 Tavily 搜索最新文章
python3 /opt/openclaw/.openclaw/workspace/skills/tavily/scripts/tavily_search.py \
  "site:manus.ai/blog OR site:manus.im/blog" \
  --topic news \
  --max-results 10

# 使用 web_fetch 提取文章内容
web_fetch https://www.manus.ai/blog/article-name
```

---

## 通用获取策略

### 方案 1: 使用 Tavily 搜索 (推荐)

**优势**:
- ✅ 快速获取最新文章
- ✅ 支持时间过滤 (最近7天)
- ✅ AI生成摘要
- ✅ 多域名搜索

**示例脚本**:
```bash
#!/bin/bash

# 搜索所有四家公司的最新博客文章
python3 /opt/openclaw/.openclaw/workspace/skills/tavily/scripts/tavily_search.py \
  "(site:openai.com/blog OR site:anthropic.com/blog OR site:blog.langchain.com OR site:manus.ai/blog) AND (AI OR research OR product)" \
  --topic news \
  --depth advanced \
  --max-results 20 \
  --json > /tmp/ai-blogs.json

# 提取 URLs
cat /tmp/ai-blogs.json | jq -r '.results[].url'
```

### 方案 2: 使用 web_fetch 批量抓取

**优势**:
- ✅ 完整文章内容
- ✅ 自动转换为 Markdown
- ✅ 支持图片提取

**示例**:
```bash
# 抓取单篇文章
web_fetch https://openai.com/blog/chatgpt

# 批量抓取 (需要循环)
for url in $(cat blog-urls.txt); do
  web_fetch "$url" >> blog-articles.md
done
```

### 方案 3: RSS 订阅 (如果可用)

**检查 RSS 可用性**:
```bash
# OpenAI (可能失效)
curl -I https://openai.com/blog/rss.xml

# LangChain
curl -I https://blog.langchain.com/rss.xml

# Anthropic
curl -I https://www.anthropic.com/blog/rss.xml

# Manus
curl -I https://www.manus.ai/blog/rss.xml
```

**RSS 阅读器**:
- Feedly
- Inoreader
- FreshRSS (自托管)

---

## 自动化方案

### 定时任务: 每日博客抓取

使用 OpenClaw cron 功能创建定时任务：

```bash
# 创建每日博客汇总任务
cron action=add job='{
  "name": "Daily AI Blogs Summary",
  "schedule": {
    "kind": "cron",
    "expr": "0 9 * * *",
    "tz": "Asia/Shanghai"
  },
  "payload": {
    "kind": "agentTurn",
    "message": "请抓取 OpenAI、Anthropic、LangChain、Manus 的最新博客文章 (最近24小时)，并生成简报发送到飞书"
  },
  "sessionTarget": "isolated",
  "enabled": true
}'
```

### 处理流程

1. **搜索阶段**: 使用 Tavily 搜索最新文章
2. **过滤阶段**: 按时间、相关性筛选
3. **抓取阶段**: 使用 web_fetch 获取完整内容
4. **分析阶段**: 提取关键信息、摘要
5. **输出阶段**: 发送到 Feishu 或存档

---

## 内容分析策略

### 关键信息提取

每篇文章提取：
- 标题
- 发布时间
- 作者/来源
- 核心观点 (3-5条)
- 技术要点
- 相关链接

### 分类标签

- 📢 产品发布
- 🔬 研究论文
- 🛠️ 技术教程
- 📈 行业趋势
- 🤖 AI安全
- 💡 最佳实践

### 存储方案

**方案 1: Feishu 知识库**
- 创建 "AI公司博客" 空间
- 按公司分类节点
- 每篇文章一个子文档

**方案 2: Workspace 本地存储**
```
workspace/
├── ai-blogs/
│   ├── openai/
│   │   ├── 2026-02-13-gpt5-release.md
│   │   └── ...
│   ├── anthropic/
│   ├── langchain/
│   └── manus/
└── ai-blogs-summary.md
```

---

## 快速参考

### 搜索命令模板

```bash
# OpenAI 最近文章
python3 /opt/openclaw/.openclaw/workspace/skills/tavily/scripts/tavily_search.py \
  "site:openai.com/blog OR site:openai.com/news" --topic news --max-results 10

# Anthropic 最近文章
python3 /opt/openclaw/.openclaw/workspace/skills/tavily/scripts/tavily_search.py \
  "site:anthropic.com/blog OR site:anthropic.com/news" --topic news --max-results 10

# LangChain 最近文章
python3 /opt/openclaw/.openclaw/workspace/skills/tavily/scripts/tavily_search.py \
  "site:blog.langchain.com" --topic news --max-results 10

# Manus 最近文章
python3 /opt/openclaw/.openclaw/workspace/skills/tavily/scripts/tavily_search.py \
  "site:manus.ai/blog OR site:manus.im/blog" --topic news --max-results 10

# 全部搜索
python3 /opt/openclaw/.openclaw/workspace/skills/tavily/scripts/tavily_search.py \
  "(site:openai.com/blog OR site:anthropic.com/blog OR site:blog.langchain.com OR site:manus.ai/blog)" --topic news --max-results 20
```

---

## 注意事项

1. **网站结构变化**: 这些公司可能会改版网站，定期验证 URL
2. **RSS 可靠性**: OpenAI 的 RSS 历史上出现过失效
3. **频率限制**: 不要频繁抓取，避免被封禁
4. **内容版权**: 抓取的内容仅用于个人学习，不要公开发布

---

_创建时间: 2026-02-13_  
_作者: 小龙虾 🦞_
