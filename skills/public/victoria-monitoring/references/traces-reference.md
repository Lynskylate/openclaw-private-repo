# Traces 查询参考

## 服务信息

- **服务名称**: VictoriaTraces
- **地址**: http://prometheus.local:9428
- **与 VictoriaLogs**: 独立部署（不同端口）
- **版本**: victoria-traces v0.7.1
- **支持的协议**: OpenTelemetry (OTLP gRPC/HTTP), Jaeger API

## Tracing 概念

### Trace 结构
- **Trace**: 一次请求的完整追踪，由多个 span 组成
- **Span**: trace 中的一个操作单元，包含时间和元数据
- **Span ID**: 单个 span 的唯一标识
- **Trace ID**: 整个 trace 的唯一标识

### Span 属性
- **trace_id**: trace 的唯一 ID
- **span_id**: span 的唯一 ID
- **parent_id**: 父 span 的 ID（如果有）
- **operation_name**: 操作名称
- **service_name**: 服务名称
- **start_time**: 开始时间
- **duration**: 持续时间
- **tags**: 键值对标签
- **logs**: 结构化日志

## Traces 相关 Metrics

### 在 VictoriaMetrics 中的 OpenTelemetry/Tracing 指标

查看与 traces 相关的指标（如存在）：

```bash
# 查找 tracing 相关的指标
curl "http://prometheus.local:8428/api/v1/label/__name__/values" | \
  jq -r '.data[] | select(test("trace|span|tracing|jaeger"; "i"))'
```

### 可能的指标类型（需验证）
- `service_calls_total` - 服务调用总数
- `span_duration_seconds` - span 时长
- `trace_error_count` - 错误 trace 数量
- `tracing_sample_rate` - 采样率

## 通过 Logs 关联 Traces

VictoriaLogs 可能包含 trace ID 信息，用于关联 traces 和 logs。

### 查找包含 trace ID 的日志
```sql
msg:"trace_id"
msg:"span_id"
trace_id:"abc123"
```

### 查找特定服务的 trace
```sql
service_name:"my_service" AND msg:"trace"
```

### 查找慢请求的 trace
```sql
duration_seconds > 5 AND msg:"trace"
```

## Traces 查询建议

## Traces API 实际可用端点

### 健康检查
```bash
curl http://prometheus.local:9428/
```

### Jaeger API (完全支持)

#### 查询所有服务
```bash
curl "http://prometheus.local:9428/select/jaeger/api/services"
```
**当前服务:**
- envoy-gtr
- envoy-iZf8z8qpzl0oqrzqf1y9t1Z
- otel-smoke
- test-service

#### 查询服务的操作
```bash
curl "http://prometheus.local:9428/select/jaeger/api/services/{service_name}/operations"
```

示例:
```bash
# 查看 envoy-gtr 的操作
curl "http://prometheus.local:9428/select/jaeger/api/services/envoy-gtr/operations"

# 返回: ["ingress", "router grafana_service egress", "router logs_service egress", ...]
```

#### 查询 Traces
```bash
curl "http://prometheus.local:9428/select/jaeger/api/traces?service={service_name}&limit=10"
```

参数:
- `service`: 服务名称
- `operation`: 操作名称（可选）
- `tags`: 标签过滤（可选，格式: `key=value`）
- `limit`: 返回 trace 数量（可选，默认足够）
- `startMin`: 开始时间（可选，纳秒时间戳）
- `endMax`: 结束时间（可选，纳秒时间戳）

示例:
```bash
# 查询 envoy-gtr 的 traces
curl "http://prometheus.local:9428/select/jaeger/api/traces?service=envoy-gtr&limit=5"

# 查询特定操作的 traces
curl "http://prometheus.local:9428/select/jaeger/api/traces?service=envoy-gtr&operation=ingress&limit=10"

# 按 trace ID 查询
curl "http://prometheus.local:9428/select/jaeger/api/traces?traceID=<trace_id>"
```

#### 服务依赖
```bash
curl "http://prometheus.local:9428/select/jaeger/api/dependencies"
```

### Web UI 访问
```
http://prometheus.local:9428/select/vmui
```

### 数据采集端点
VictoriaTraces 接收以下格式:
- **OTLP gRPC**: http://prometheus.local:9429 (默认)
- **OTLP HTTP POST**: `/insert/opentelemetry/v1/traces`
- **Jaeger Thrift**: 需确认是否启用

## 常见 Trace 查询模式

### 查找完整请求链
通过日志中的 trace ID 追踪完整请求：

```sql
# 在日志中查找 trace ID
msg:"trace_id:abc123def"

# 查看包含 trace 的所有日志
msg:"trace" AND service_name="api_gateway"
```

### 查找错误 Traces
```sql
msg:"trace" AND ( "error" OR "exception" OR "failed" )
```

### 查找慢操作 Traces
```sql
duration_seconds > 10 AND msg:"trace"
```

### 查找特定服务的 Traces
```sql
service_name="victoriametrics" AND msg:"trace"
job="victoriametrics" AND msg:"trace_id"
```

## Tracing 性能指标

### Ingestion Metrics (数据接收)

#### 数据接收量
```promql
# 总接收字节数
sum(vt_bytes_ingested_total)

# 按类型分组接收量
vt_bytes_ingested_total

# OTLP gRPC 接收速率
rate(vt_bytes_ingested_total{type="opentelemetry_traces_otlpgrpc"}[5m])

# OTLP HTTP 接收速率
rate(vt_bytes_ingested_total{type="opentelemetry_traces_otlphttp"}[5m])
```

#### HTTP 错误
```promql
# 总错误数
sum(vt_http_errors_total)

# 按端点和格式分组错误
vt_http_errors_total

# 错误率
sum(rate(vt_http_errors_total[5m]))
```

### Request Latency (请求延迟)

#### Ingestion 延迟 (P99)
```promql
# OTLP gRPC ingestion P99
vt_http_request_duration_seconds{path="/opentelemetry.proto.collector.trace.v1.TraceService/Export",format="protobuf",quantile="0.99"}

# Jaeger 查询延迟
vt_http_request_duration_seconds{path=~"/select/jaeger/.*"}
```

#### 平均延迟
```bash
# 查看 ingestion 延迟统计
curl "http://prometheus.local:9428/metrics" | grep vt_http_request_duration_seconds
```

### System Metrics (系统指标)

#### 查询并发
```promql
# 当前查询数
vt_concurrent_select_current

# 查询队列容量
vt_concurrent_select_capacity

# 限流次数
vt_concurrent_select_limit_reached_total
rate(vt_concurrent_select_limit_reached_total[5m])
```

#### 存储合并
```promql
# 强制合并操作
vt_active_force_merges
```

### 实时监控示例

```bash
# 1. 查看接收速率
curl "http://prometheus.local:9428/api/v1/query?query=rate(vt_bytes_ingested_total[5m])"

# 2. 查看错误率
curl "http://prometheus.local:9428/api/v1/query?query=rate(vt_http_errors_total[5m])"

# 3. 查看查询延迟 P99
curl "http://prometheus.local:9428/api/v1/query?query=vt_http_request_duration_seconds{quantile=\"0.99\"}"
```

### Span 示例分析
从 trace 数据可以提取：
- Duration: `spans[].duration` (纳秒)
- Operation: `spans[].operationName`
- Service: `processes[].serviceName`
- Tags: `spans[].tags[]`

## 与 Metrics 和 Logs 的协同

### 三大信号关联

1. **Metrics**: 告诉你"何时"出问题
2. **Logs**: 告诉你"什么"出问题
3. **Traces**: 告诉你"哪里"出问题和"为什么"

### 典型故障排查流程

1. **Metrics 触发告警**: 查询 error rate ↑
2. **Logs 定位错误**: 查找包含 trace_id 的错误日志
3. **Traces 追踪根因**: 使用 trace_id 查看完整调用链

### 关联查询示例

#### 查找高延迟的完整路径
```bash
# 1. 找到高延迟的 timestamps
curl "http://prometheus.local:8428/api/v1/query?query=histogram_quantile(0.99, rate(envoy_cluster_upstream_rq_time_bucket{job=\"aliyun_envoy\"}[5m]))"

# 2. 在 logs 中查找该时段的 trace ID
curl -X POST "http://loki.local:9428/select/logsql/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "duration_seconds > 5 AND msg:\"trace_id\"",
    "start": "2026-02-11T10:00:00Z",
    "end": "2026-02-11T10:05:00Z"
  }'

# 3. 使用 trace_id 查询完整 trace（如果 API 可用）
curl "http://loki.local:9428/api/traces/{trace_id}"
```

#### 追踪端到端请求
```sql
# 在日志中查找所有包含相同 trace_id 的记录
trace_id="abc123"

# 查看请求的完整生命周期
trace_id="abc123" AND (service_name="api_gateway" OR service_name="backend_service" OR service_name="database")
```

## 实用场景

### 1. 慢请求分析
当 API 延迟过高时：
```bash
# 查询慢请求 trace
curl -X POST "http://loki.local:9428/select/logsql/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "duration_seconds > 10 AND msg:\"trace_id\"", "limit": 20}'
```

### 2. 错误追踪
追踪错误的根本原因：
```sql
msg:"exception" OR "error" AND msg:"trace_id"
```

### 3. 服务依赖分析
分析服务之间的调用关系：
```sql
msg:"call" AND "trace" AND service_name="gateway"
```

### 4. 分布式事务追踪
追踪跨服务的完整事务：
```sql
transaction_id="txn_123" AND msg:"trace"
```

## 采样策略

### 默认采样
VictoriaTraces 默认可能使用 1% 采样率，降低存储成本。

### 调整采样（需配置）
- 开发环境: 100% 采样（all traces）
- 测试环境: 50% 采样
- 生产环境: 1-5% 采样

### 采样率查询
```promql
# 查看采样率（如果指标存在）
tracing_sample_rate
```

## Tracing 最佳实践

### 1. 选择性追踪
- 优先追踪高价值流量（用户访问、支付等）
- 避免追踪健康检查和内部流量
- 使用适当的标签（不追踪 PII）

### 2. Tags 规范
统一使用标准化的标签：
- `service_name`: 服务名称
- `operation_name`: 操作名称
- `http.method`: HTTP 方法
- `http.route`: HTTP 路径
- `http.status_code`: HTTP 状态码
- `error.type`: 错误类型（如果有）

### 3. Span 层级
保持合理的 span 嵌套深度，避免过深的调用链。

## 限制和注意事项

### 当前环境限制
- VictoriaTraces API 具体可用性需要验证
- Traces 可能主要作为 VictoriaLogs 的扩展功能
- 需要通过 Logs API 查询 trace 相关信息

### 性能考虑
- 高采样率会增加存储和处理开销
- 追踪所有请求可能影响性能
- 合理设置采样率和 TTL

### 存储策略
- Traces 数据通常比 Logs 和 Metrics 更大
- 需要定期清理旧 traces（例如 7-30 天保留）

## 与其他工具集成

### Grafana
如果在 Grafana 中配置了 traces 数据源：
- 可以创建 trace 查询面板
- 支持 LogQL + Tracing 联合查询
- 支持从 Metrics 跳转到 Traces

### Alerting
结合 Metrics 和 Logs 创建告警：
- Metrics 检测延迟/错误率升高
- Logs 查找对应的 trace_id
- 自动关联到 trace 详情

## 诊断和调试

### 查找 tracing 相关错误
```sql
msg:"trace" AND ("error" OR "exception" OR "failed")
```

### 查看采样统计
在 VictoriaMetrics 中查找 trace 相关指标（如果存在）：
```bash
curl "http://prometheus.local:8428/api/v1/label/__name__/values" | \
  jq -r '.data[] | select(test("trace|span"; "i"))'
```

### 验证 trace 采集
```sql
msg:"trace_id" | count()
```

## 常见问题

### Q: 如何查询 traces？
A: 目前主要通过 Logs API 查询包含 trace_id 的日志；VictoriaTraces API 具体可用性需验证。

### Q: 是否支持 Jaeger 兼容 API？
A: 需要查看 VictoriaTraces 文档（可能支持 `vm/api/traces` 端点）。

### Q: 如何调整采样率？
A: 需要在 VictoriaTraces 配置文件中设置 `-tracingSampleRate` 参数。

### Q: Traces 数据保留多久？
A: 需要在配置中设置 `-search.maxTimeseries` 或相关保留策略。

### Q: 能否与 Grafana 集成？
A: 可以，通过添加 VictoriaTraces 作为数据源。

## 下一步

要完全启用和验证 Tracing 功能，建议：
1. 检查 VictoriaTraces 配置
2. 验证 API 端点可用性
3. 配置采样策略
4. 测试 trace 查询流程
5. 与 Grafana 集成
