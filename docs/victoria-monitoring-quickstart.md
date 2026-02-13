# 系统监控服务使用指南

## 服务概览

### 1. VictoriaMetrics (prometheus.local:8428)
**版本:** v1.111.0
**用途:** 时序数据采集和存储
**状态:** ✅ 运行中 (运行时间: 21.2小时)

### 2. VictoriaLogs (loki.local:9428)
**版本:** v0.7.1 (victoria-traces)
**用途:** 日志聚合和查询
**状态:** ✅ 运行中 (运行时间: 21.2小时)

---

## VictoriaMetrics 使用方法

### 健康检查
```bash
curl http://prometheus.local:8428/health
# 返回: OK
```

### 查询所有指标名称
```bash
curl "http://prometheus.local:8428/api/v1/label/__name__/values" | jq
```

### 基础查询 API
```bash
# 即时查询示例
curl "http://prometheus.local:8428/api/v1/query?query=up"

# 范围查询示例
curl "http://prometheus.local:8428/api/v1/query_range?query=up&start=$(date -d '1h ago' +%s)&end=$(date +%s)&step=60"
```

### 常用查询示例

1. **检查所有 target 状态**
   ```bash
   curl "http://prometheus.local:8428/api/v1/query?query=up" | jq
   ```

2. **查看抓取时长**
   ```bash
   curl "http://prometheus.local:8428/api/v1/query?query=scrape_duration_seconds" | jq
   ```

3. **查看 CPU 使用率**
   ```bash
   curl "http://prometheus.local:8428/api/v1/query?query=rate(process_cpu_seconds_total[5m])" | jq
   ```

4. **查看内存使用**
   ```bash
   curl "http://prometheus.local:8428/api/v1/query?query=process_resident_memory_bytes" | jq
   ```

### 查看所有 Targets
```bash
# 格式化输出
curl "http://prometheus.local:8428/api/v1/targets" | jq '.data.activeTargets[] | {job: .labels.job, instance: .labels.instance, health: .health, lastScrape: .lastScrape, lastSamples: .lastSamplesScraped}'
```

**当前监控目标:**
- `127.0.0.1:8428` (victoriametrics) - 自监控 ✅
- `127.0.0.1:9100` (victoriametrics) - node_exporter ✅
- `192.168.31.58:9100` (victoriametrics) - 远程节点 exporter ✅
- `142.171.205.19:443` (remote_server) - Production 服务器 ✅
- `142.171.205.19:443` (remote_server_envoy) - Production Envoy ✅
- `127.0.0.1:9901` (local_envoy) - 本地 Envoy ✅
- `47.120.46.128:80` (aliyun_envoy) - Aliyun Envoy ✅
- `127.0.0.1:9428` (victoriatraces) - VictoriaLogs ✅

### 指标查询示例

#### Envoy 指标
```bash
# 查看集群请求量
curl "http://prometheus.local:8428/api/v1/query?query=sum(envoy_cluster_upstream_rq)"

# 查看成功率
curl "http://prometheus.local:8428/api/v1/query?query=sum(envoy_cluster_upstream_rq{envoy_response_code!~'5..'}) / sum(envoy_cluster_upstream_rq)"
```

#### 系统指标
```bash
# CPU 使用率
curl "http://prometheus.local:8428/api/v1/query?query=rate(process_cpu_seconds_total[5m]) * 100"

# 内存使用 (MB)
curl "http://prometheus.local:8428/api/v1/query?query=process_resident_memory_bytes / 1024 / 1024"
```

---

## VictoriaLogs 使用方法

### 健康检查
```bash
curl http://loki.local:9428/health
# 返回: OK
```

### LogSQL 查询 API
VictoriaLogs 支持 LogSQL 查询语法进行日志查询。

**基础查询:**
```bash
# 查询所有日志
curl -X POST "http://loki.local:9428/select/logsql/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "*"}'

# 查询最近日志
curl -X POST "http://loki.local:9428/select/logsql/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "*", "limit": 10}'

# 按时间过滤
curl -X POST "http://loki.local:9428/select/logsql/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "*",
    "start": "-1h",
    "limit": 20
  }'
```

### LogSQL 查询语法示例

1. **简单文本搜索**
   ```
   error
   WARNING
   "connection refused"
   ```

2. **字段过滤**
   ```
   job="victoriametrics"
   level="error"
   stream="stdout"
   ```

3. **组合查询**
   ```
   level="error" AND job="victoriametrics"
   (error OR warning) AND status_code>=500
   ```

4. **时间过滤**
   ```
   _time >= now() - 1h
   _time >= "2026-02-11T00:00:00Z"
   ```

5. **正则表达式**
   ```
   msg =~ "error.*[0-9]+"
   job =~ "remote.*"
   ```

### 使用 curl 查询示例

```bash
# 查询特定 job 的日志
curl -X POST "http://loki.local:9428/select/logsql/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "job=\"victoriametrics\" AND level=\"error\"",
    "limit": 100
  }'

# 查询包含特定错误消息的日志
curl -X POST "http://loki.local:9428/select/logsql/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "_stream:stdout \"WARN\" OR \"ERROR\"",
    "limit": 50
  }'
```

### Metrics API
VictoriaLogs 也提供标准的 metrics 端点:

```bash
# 获取内部指标
curl "http://loki.local:9428/metrics"

# 监控日志处理
curl "http://loki.local:9428/metrics" | grep -E "vl_|vm_"
```

**关键指标:**
- `vl_merge_bytes` - 日志合并数据量
- `vl_merge_duration_seconds` - 合并延迟
- `vm_cache_*` - 缓存性能
- `process_*` - 进程资源使用

---

## Web 界面访问

### VictoriaMetrics
```
http://prometheus.local:8428/vmui
http://prometheus.local:8428/select/vmui
```

### VictoriaLogs
```
http://loki.local:9428/select/logsql
```

---

## 常用查询模板

### VictoriaMetrics 查询模板

1. **服务健康检查**
   ```promql
   up
   ```

2. **API 延迟 P99**
   ```promql
   histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))
   ```

3. **错误率**
   ```promql
   sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))
   ```

4. **磁盘使用率**
   ```promql
   1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)
   ```

5. **网络流量**
   ```promql
   rate(node_network_receive_bytes_total[5m])
   rate(node_network_transmit_bytes_total[5m])
   ```

### VictoriaLogs 查询模板

1. **错误日志**
   ```
   level="error" OR msg:"ERROR"
   ```

2. **特定服务日志**
   ```
   job="victoriametrics" AND _time >= now() - 1h
   ```

3. **慢请求日志**
   ```
   duration_seconds > 5
   ```

4. **认证失败**
   ```
   msg:"authentication" AND msg:"failed"
   ```

---

## 数据采集配置

### Metrics 采集点
- 本地节点: `127.0.0.1:9100` (node_exporter)
- 本地 VictoriaMetrics: `127.0.0.1:8428`
- 本地 VictoriaLogs: `127.0.0.1:9428`
- 本地 Envoy: `127.0.0.1:9901`
- 远程服务器: `142.171.205.19:443`
- Aliyun Envoy: `47.120.46.128:80`
- 远程节点: `192.168.31.58:9100`

### 日志采集
日志采集到 VictoriaLogs 的方式需要确认当前配置，可能包括：
- 本地应用日志
- Envoy access logs
- 远程服务器日志

---

## 快速诊断命令

### 服务状态检查
```bash
# 检查所有服务健康
echo "=== VictoriaMetrics ==="
curl -s http://prometheus.local:8428/health

echo -e "\n=== VictoriaLogs ==="
curl -s http://loki.local:9428/health
```

### 监控目标检查
```bash
curl -s "http://prometheus.local:8428/api/v1/query?query=up" | \
  jq -r '.data.result[] | "\(.metric.job): \(.metric.instance) -> \(.value[1])"'
```

### 资源使用检查
```bash
echo "=== VictoriaMetrics ==="
curl -s "http://prometheus.local:8428/metrics" | grep -E "process_resident_memory_bytes|process_cpu_seconds_total"

echo -e "\n=== VictoriaLogs ==="
curl -s "http://loki.local:9428/metrics" | grep -E "process_resident_memory_bytes|process_cpu_seconds_total"
```

---

## 性能优化建议

### VictoriaMetrics
- 使用 `rollup` 函数减少查询数据量
- 添加适当的 `recording rules` 预计算常用指标
- 配置数据保留策略

### VictoriaLogs
- 使用时间范围限制查询
- 添加索引字段到查询条件
- 使用 `limit` 控制返回结果

---

## 故障排查

### Prometheus/VictoriaMetrics 无法抓取
```bash
# 检查 target 状态
curl "http://prometheus.local:8428/api/v1/targets" | jq '.data.activeTargets[] | select(.health != "up")'

# 查看最近的错误
curl "http://prometheus.local:8428/metrics" | grep scrape_errors
```

### 日志查询过慢
```bash
# 检查缓存命中率
curl "http://loki.local:9428/metrics" | grep vm_cache_misses_total

# 检查合并延迟
curl "http://loki.local:9428/metrics" | grep vl_merge_duration_seconds
```

---

## 联系人和支持

- 配置文件位置: 需要确认
- 日志位置: 需要确认
- 文档: https://victoriametrics.com/

---

*最后更新: 2026-02-11*
