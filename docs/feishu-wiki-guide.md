# Feishu Wiki 文档操作完整指南

_更新时间: 2026-02-12_
_成功案例: https://qcnxu5ciwz8e.feishu.cn/wiki/H1BywLXG8iziObksbfQc4hPNnNb_

---

## 概述

本文档详细说明了如何在 Feishu 知识库中创建和管理文档，包括常见的错误和解决方案。

---

## 快速开始

### 1. 创建 Wiki 节点

```json
{
  "action": "create",
  "space_id": "7606015010138590169",
  "title": "文档标题",
  "obj_type": "docx"
}
```

**返回结果**:
```json
{
  "node_token": "H1BywLXG8iziObksbfQc4hPNnNb",
  "obj_token": "Oy65dkPROoE9pGxTTiNcFSUbnUe",
  "obj_type": "docx",
  "title": "文档标题"
}
```

**重要**:
- ✅ 在知识库根创建节点
- ❌ 不要指定 `parent_node_token`（会导致 400 错误）

### 2. 写入 Markdown 内容

```json
{
  "action": "append",
  "doc_token": "Oy65dkPROoE9pGxTTiNcFSUbnUe",
  "content": "# 标题\n\n## 副标题\n\n- 列表项\n\n**粗体** 和 *斜体*"
}
```

**返回结果**:
```json
{
  "success": true,
  "blocks_added": 5,
  "block_ids": ["doxcn...", ...]
}
```

**重要**:
- ✅ 使用 `append` 而不是 `write`（Wiki 文档限制）
- ✅ 使用 `append` 而不是 `update_block`（需要 Markdown 渲染）
- ✅ 支持标题、列表、链接、粗体、斜体等

### 3. 验证结果

```json
{
  "action": "list_blocks",
  "doc_token": "Oy65dkPROoE9pGxTTiNcFSUbnUe"
}
```

---

## 操作对比

| 操作 | Wiki 文档 | 普通文档 | 用途 | 推荐度 |
|------|-----------|-----------|------|--------|
| `feishu_wiki create` | ✅ | - | 创建知识库节点 | ⭐⭐⭐⭐⭐ |
| `feishu_doc append` | ✅ | ✅ | 追加内容，自动转换 Markdown | ⭐⭐⭐⭐⭐ |
| `feishu_doc write` | ❌ (400) | ✅ | 替换全部内容 | ⭐⭐⭐ |
| `feishu_doc update_block` | ⚠️ | ⚠️ | 更新单个块，纯文本 | ⭐ |
| `feishu_doc list_blocks` | ✅ | ✅ | 查看 block 结构 | ⭐⭐⭐⭐⭐ |
| `feishu_doc read` | ✅ | ✅ | 读取纯文本 | ⭐⭐⭐⭐ |

---

## Markdown 渲染原理

### 关键发现

`write` 和 `append` 内部使用 `convertMarkdown()` 函数，调用 Feishu 的 `docx.document.convert` API。

### 源代码

从 `/usr/local/src/openclaw/extensions/feishu/src/docx.ts`:

```typescript
async function convertMarkdown(client: Lark.Client, markdown: string) {
  const res = await client.docx.document.convert({
    data: { content_type: "markdown", content: markdown },
  });
  return {
    blocks: res.data?.blocks ?? [],
    firstLevelBlockIds: res.data?.first_level_block_ids ?? [],
  };
}

async function appendDoc(client: Lark.Client, docToken: string, markdown: string) {
  const { blocks } = await convertMarkdown(client, markdown);
  // ... 插入 blocks
}
```

### Block 类型映射

| block_type | 名称 | Markdown 语法 |
|------------|------|---------------|
| 1 | Page | - |
| 2 | Text | 普通文本 |
| 3 | Heading1 | `# 标题` |
| 4 | Heading2 | `## 标题` |
| 5 | Heading3 | `### 标题` |
| 12 | Bullet | `- 列表` |
| 13 | Ordered | `1. 列表` |
| 14 | Code | `` `代码` `` |
| 15 | Quote | `> 引用` |
| 27 | Image | `![alt](url)` |

---

## 常见错误和解决方案

### 错误 1: Markdown 渲染成"高亮"文本

**症状**: 所有 Markdown 符号（`#`、`**`、`-` 等）都作为普通文本显示

**原因**: 使用了 `update_block` 而不是 `append`

**解决方案**:
```json
// ❌ 错误
{
  "action": "update_block",
  "doc_token": "...",
  "block_id": "...",
  "content": "# 标题\n\n- 列表"  // 不会被解析
}

// ✅ 正确
{
  "action": "append",
  "doc_token": "...",
  "content": "# 标题\n\n- 列表"  // 会被正确转换
}
```

**原因分析**:
- `update_block` 只接受纯文本，不解析 Markdown
- `append` 内部调用 `convertMarkdown()`，将 Markdown 转换为 Feishu blocks

### 错误 2: write 操作返回 400 错误

**症状**:
```json
{
  "error": "Request failed with status code 400"
}
```

**原因**: Wiki 文档不支持 `write` 操作

**解决方案**: 使用 `append` 代替 `write`

### 错误 3: 创建子节点时指定 parent_node_token

**症状**: 创建 Wiki 节点时返回 400 错误

**原因**: 指定 `parent_node_token` 会导致验证失败

**解决方案**:
```json
// ❌ 错误
{
  "action": "create",
  "space_id": "7606015010138590169",
  "parent_node_token": "OU1qw1jX3iWgYVkoK71cBymgnJg",  // 会导致 400
  "title": "子文档"
}

// ✅ 正确
{
  "action": "create",
  "space_id": "7606015010138590169",
  // 不指定 parent_node_token
  "title": "子文档"
}
```

**注意**: 创建后可以在 Feishu UI 中手动移动节点到父节点下

---

## Markdown 格式支持

### 支持的格式

- ✅ 标题（`#`, `##`, `###`）
- ✅ 无序列表（`-` 或 `*`）
- ✅ 有序列表（`1.`）
- ✅ 链接（`[text](url)` 或 `<url>`）
- ✅ 粗体（`**text**`）
- ✅ 斜体（`*text*`）
- ✅ 代码块（`` ``` ``)
- ✅ 行内代码（`` `code` ``）
- ✅ 引用（`>`）
- ✅ 分隔线（`---`）

### 不支持的格式

- ❌ Markdown 表格（`| 列1 | 列2 |`）
- ❌ 任务列表（`- [ ]`）
- ❌ 复杂的嵌套结构

---

## 最佳实践

### 1. 创建文档流程

```
1. feishu_wiki create (不指定 parent_node_token)
   ↓
2. 获取 obj_token
   ↓
3. feishu_doc append (传入完整 Markdown)
   ↓
4. feishu_doc list_blocks (验证渲染)
```

### 2. 内容组织

- 使用标题层级组织内容（`#` → `##` → `###`）
- 使用列表提高可读性
- 使用链接引用外部资源
- 避免使用表格

### 3. 错误处理

- 如果 `append` 返回 400 错误，尝试分批追加
- 使用 `list_blocks` 验证 block 结构是否正确
- 如果内容太长，考虑分成多个文档

### 4. 验证和调试

```json
// 查看文档结构
{
  "action": "list_blocks",
  "doc_token": "..."
}

// 查看纯文本
{
  "action": "read",
  "doc_token": "..."
}
```

---

## 示例代码

### 完整示例：创建 GitHub 热点文档

```javascript
// 1. 创建 Wiki 节点
const wiki = await feishu_wiki({
  action: "create",
  space_id: "7606015010138590169",
  title: "每日github热点",
  obj_type: "docx"
});

// 2. 追加内容
const result = await feishu_doc({
  action: "append",
  doc_token: wiki.obj_token,
  content: `# 2026-02-12 GitHub 热点分析

## 数据来源
GitHub Trending - Today

## 热门项目

### 1. google/langextract
- 语言: Python
- Stars: 31,104 (今日 +1,201)
- 链接: <https://github.com/google/langextract>

### 2. unslothai/unsloth
- 语言: Python
- Stars: 51,981 (今日 +100)
- 链接: <https://github.com/unslothai/unsloth>

... 更多内容 ...
`
});

// 3. 验证
const blocks = await feishu_doc({
  action: "list_blocks",
  doc_token: wiki.obj_token
});
```

---

## 参考资源

- **知识库**: https://qcnxu5ciwz8e.feishu.cn/wiki/OU1qw1jX3iWgYVkoK71cBymgnJg
- **成功案例**: https://qcnxu5ciwz8e.feishu.cn/wiki/H1BywLXG8iziObksbfQc4hPNnNb
- **源代码**: `/usr/local/src/openclaw/extensions/feishu/src/docx.ts`
- **Skill 文档**: `/usr/local/src/openclaw/extensions/feishu/skills/feishu-doc/SKILL.md`

---

_文档维护: 小龙虾 🦞_
