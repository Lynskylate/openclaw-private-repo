# Logs 查询参考

## 服务信息

- **VictoriaLogs 地址**: http://loki.local:9428
- **API 端点**: http://loki.local:9428/select/logsql/query
- **版本**: v0.7.1 (victoria-traces)
- **查询语言**: LogSQL

## 基础 API 操作

### 健康检查
```bash
curl http://loki.local:9428/health
```

### 基础查询
```bash
# 查询所有日志
curl -X POST "http://loki.local:9428/select/logsql/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "*"}'

# 限制返回数量
curl -X POST "http://loki.local:9428/select/logsql/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "*", "limit": 10}'
```

### 时间范围查询
```bash
# 最近 1 小时
curl -X POST "http://loki.local:9428/select/logsql/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "*", "start": "-1h"}'

# 特定时间范围
curl -X POST "http://loki.local:9428/select/logsql/query" \
  -H "Content-Type: application/json" \
  -d '"{\"query\": "*", \"start\": \"2026-02-11T00:00:00Z\", \"end\": \"2026-02-11T23:59:59Z\"}"'
```

## LogSQL 语法

### 文本搜索

#### 简单搜索
```sql
error
warning
"connection refused"
```

#### OR 逻辑
```sql
error OR warning
error OR warning OR critical
```

#### AND 逻辑
```sql
error AND timeout
error AND timeout AND retry
```

#### NOT 逻辑
```sql
error NOT "temp"
error NOT "temporal"
```

### 字段过滤

#### 基础字段过滤
```sql
job="victoriametrics"
level="error"
stream="stdout"
env="production"
instance="127.0.0.1:9428"
```

#### 数值比较
```sql
status_code>=400
status_code=500
duration_seconds>5
count>=10
```

#### 字符串匹配
```sql
msg="error"
method="GET"
path="/api/v1/query"
```

### 复合查询

#### 组合查询
```sql
job="victoriametrics" AND level="error"
level="error" AND job="victoriametrics" OR job="victoriatraces"
( error OR warning ) AND status_code>=500
```

#### 括号分组
```sql
( level="error" OR level="warning" ) AND job="victoriametrics"
```

### 正则表达式

#### 简单正则
```sql
msg =~ "error.*[0-9]+"
job =~ "remote.*"
method =~ "(GET|POST)"
```

#### 负向正则
```sql
msg !~ "temporal"
job !~ "test.*"
```

### 时间过滤

#### 相对时间
```sql
_time >= now() - 1h
_time >= now() - 24h
_time >= now() - 7d
```

#### 绝对时间
```sql
_time >= "2026-02-11T00:00:00Z"
_time >= "2026-02-11T00:00:00Z" AND _time < "2026-02-12T00:00:00Z"
```

#### 时间范围
```sql
_time >= "2026-02-11T10:00:00Z" AND _time <= "2026-02-11T18:00:00Z"
```

## 常见日志字段

### 字段说明

| 字段 | 说明 |
|------|------|
| `_stream` | 日志流 (stdout/stderr) |
| `_time` | 时间戳 |
| `job` | 任务名称 |
| `level` | 日志级别 (info/warn/error/debug) |
| `instance` | 实例地址 |
| `env` | 环境标签 |
| `msg` | 日志消息 |
| `method` | HTTP 方法 |
| `path` | HTTP 路径 |
| `status_code` | HTTP 状态码 |
| `duration_seconds` | 请求时长 |

### 查询常用字段

查看日志级别：
```sql
level="info"
level="warning"
level="error"
level="debug"
```

查看特定任务：
```sql
job="victoriametrics"
job="victoriatraces"
job="local_envoy"
```

查看日志流：
```sql
_stream:stdout
_stream:stderr
```

## 常见查询场景

### 错误日志排除
排除特定错误类型：
```sql
level="error" AND msg!~ "temporal"
```

### 服务日志
VictoriaLogs/VictoriaTraces 错误：
```sql
job="victoriatraces" AND level="error"
```

特定服务的 INFO 日志：
```sql
job="victoriametrics" AND level="info"
```

### API 日志
HTTP 5xx 错误：
```sql
status_code>=500
```

特定路径的错误：
```sql
path="/api/v1/query" AND status_code>=400
```

慢请求（>5秒）：
```sql
duration_seconds > 5
path="/api/v1/query_range" AND duration_seconds > 10
```

### 环境过滤
Production 环境错误：
```sql
env="production" AND level="error"
```

### 时间范围+条件
最近 1 小时的错误日志：
```sql
_time >= now() - 1h AND level="error"
```

今天的 job="victoriametrics" 日志：
```sql
job="victoriametrics" AND _time >= "2026-02-11T00:00:00Z"
```

## 实用查询示例

### 1. 搜索所有错误日志
```sql
level="error" OR msg:"ERROR"
```

### 2. 查找特定服务错误
```sql
job="victoriametrics" AND (level="error" OR msg:"WARN")
```

### 3. 超时和连接错误
```sql
msg:"timeout" OR "connection" AND "error"
```

### 4. 认证失败
```sql
msg:"authentication" AND "failed" OR "unauthorized"
```

### 5. 查看特定时间段
```sql
_time >= "2026-02-11T10:00:00Z" AND _time <= "2026-02-11T12:00:00Z"
```

### 6. HTTP 错误
```sql
status_code >= 400
status_code = 500
```

### 7. 组合多个条件
```sql
job="victoriametrics" AND (level="error" OR level="warning") AND _time >= now() - 1h
```

### 8. 排除内容
```sql
level="error" AND msg!~ "test"
msg:"error" AND NOT "debug"
```

### 9. 正则匹配
```sql
msg =~ "error.*[0-9]{3}"
job =~ "remote.*"
```

### 10. 时间+状态
```sql
_time >= now() - 24h AND status_code >= 400
```

## API 参数

### POST 请求参数

```json
{
  "query": "LogSQL 查询语句",
  "limit": 100,          // 返回结果数量，默认100
  "start": "-1h",        // 开始时间，相对时间或 ISO 时间
  "end": "now",          // 结束时间，默认 now
  "nocache": false       // 是否禁用缓存
}
```

### 相对时间格式
- `n` - 现在时间
- `-5m` - 5 分钟前
- `-1h` - 1 小时前
- `-24h` - 24 小时前
- `-7d` - 7 天前

###绝对时间格式 (ISO 8601)
```
2026-02-11T10:00:00Z
2026-02-11T10:00:00.000Z
```

## Web UI

访问 VictoriaLogs UI：
```
http://loki.local:9428/select/logsql
```

## 性能优化建议

1. **始终添加时间范围**: 减少搜索的数据量
2. **字段过滤优先**: 先用 job/level 等字段缩小范围
3. **限制返回结果**: 使用 `limit` 控制返回的文档数量
4. **避免宽泛查询**: 避免长时间范围 + 简单的 `*`
5. **使用索引字段**: 充分利用 job/stream 等索引字段

## 调试技巧

### 查看索引字段
查看哪些字段有索引可以加速查询：
```sql
job="victoriametrics" AND level="error"
```

### 测试查询范围
先用更小的范围测试，然后再扩展：
```sql
_time >= now() - 5m AND job="victoriametrics"
```

### 使用 limit 预览
先用少量数据预览结果：
```sql
job="victoriametrics" AND limit=10
```

## 与 Metrics 关联

### 查找 HTTP 错误的详细日志
```sql
status_code >= 500
```

### 查询慢请求
```sql
duration_seconds > 5
```

### 查找 scrape 失败
```sql
msg:"scrape" AND "error"
```

## 常见问题

### Q: 如何搜索多个字符串？
A: 使用 OR: `"error OR warning"`

### Q: 如何排除特定内容？
A: 使用 NOT: `level="error" AND msg!~ "temporal"`

### Q: 为什么有些字段显示为 _field？
A: 未被显式索引的字段会显示为 _field，可以直接按字段名查询

### Q: 如何区分 stdout 和 stderr？
A: 使用 `_stream:stdout` 或 `_stream:stderr`
