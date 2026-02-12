# Metrics 查询参考

## 服务信息

- **VictoriaMetrics 地址**: http://prometheus.local:8428
- **API 端点**: http://prometheus.local:8428/api/v1
- **版本**: v1.111.0

## 基础 API 操作

### 健康检查
```bash
curl http://prometheus.local:8428/health
```

### 查询所有指标名称
```bash
curl "http://prometheus.local:8428/api/v1/label/__name__/values"
```

### 即时查询
```bash
curl "http://prometheus.local:8428/api/v1/query?query=<expression>"
```

### 范围查询
```bash
curl "http://prometheus.local:8428/api/v1/query_range?query=<expression>&start=<timestamp>&end=<timestamp>&step=<seconds>"
```

## 当前监控的 Targets

### 本地服务
- `127.0.0.1:8428` - VictoriaMetrics 自监控 (job=victoriametrics)
- `127.0.0.1:9100` - node_exporter (job=victoriametrics)
- `127.0.0.1:9428` - VictoriaLogs/VictoriaTraces (job=victoriatraces)
- `127.0.0.1:9901` - 局部 Envoy (job=local_envoy)

### 远程服务
- `142.171.205.19:443` - Production 服务器 (job=remote_server)
- `142.171.205.19:443` - Production Envoy (job=remote_server_envoy)
- `47.120.46.128:80` - Aliyun Envoy (job=aliyun_envoy)
- `192.168.31.58:9100` - 内网节点 (job=victoriametrics)

所有 targets 状态查看：
```bash
curl "http://prometheus.local:8428/api/v1/targets"
```

## 常用查询示例

### 服务健康
检查所有 targets 是否在线：
```promql
up
```

按 job 分组查看状态：
```promql
sum by (job) (up)
```

### Envoy 指标

#### 请求量
总请求：
```promql
sum(envoy_cluster_upstream_rq)
```

按集群分组请求：
```promql
sum by (envoy_cluster_name) (envoy_cluster_upstream_rq)
```

#### 错误率
5xx 错误率：
```promql
sum(rate(envoy_cluster_upstream_rq{envoy_response_code=~"5.."}[5m])) / sum(rate(envoy_cluster_upstream_rq[5m]))
```

#### 延迟
P99 延迟：
```promql
histogram_quantile(0.99, rate(envoy_cluster_upstream_rq_time_bucket[5m]))
```

平均延迟：
```promql
sum(rate(envoy_cluster_upstream_rq_time_sum[5m])) / sum(rate(envoy_cluster_upstream_rq_time_count[5m]))
```

### 系统指标

#### CPU 使用率
按实例：
```promql
rate(process_cpu_seconds_total[5m]) * 100
```

按实例平均值：
```promql
avg by (instance) (rate(process_cpu_seconds_total[5m]) * 100)
```

#### 内存使用
当前内存（MB）：
```promql
process_resident_memory_bytes / 1024 / 1024
```

内存使用率：
```promql
process_resident_memory_bytes / process_memory_limit_bytes * 100
```

#### 网络流量
接收速率：
```promql
rate(node_network_receive_bytes_total[5m])
```

传输速率：
```promql
rate(node_network_transmit_bytes_total[5m])
```

### Scrape 性能

#### 抓取延迟
平均抓取时长：
```promql
avg(scrape_duration_seconds)
```

按 target：
```promql
scrape_duration_seconds
```

#### 抓取错误
成功抓取率：
```promql
sum(rate(scrape_samples_scraped{success="1"}[5m])) / sum(rate(scrape_samples_scraped[5m]))
```

### HTTP/2 指标

连接超时：
```promql
rate(vm_http_conn_timeout_closed_conns_total[5m])
```

活跃连接：
```promql
vm_http_concurrent_requests
```

#### Envoy HTTP/2 相关
活跃流：
```promql
envoy_cluster_http2_streams_active
```

HTTP/2 连接数：
```promql
envoy_cluster_http2_connections_active
```

## 高级查询

### 时间范围过滤
最近 5 分钟的平均值：
```promql
avg_over_time(up[5m])
```

最近 1 小时的最大值：
```promql
max_over_time(rate(envoy_cluster_upstream_rq[5m])[1h:5m])
```

### 聚合函数
按多个标签分组：
```promql
sum by (job, instance) (rate(envoy_cluster_upstream_rq[5m]))
```

### 条件过滤
只查看 production 环境：
```promql
up{env="production"}
```

排除特定 instance：
```promql
up{instance!="127.0.0.1:8428"}
```

### 率计算
请求增长率：
```promql
rate(envoy_cluster_upstream_rq[1h])
```

错误增长：
```promql
rate(envoy_cluster_upstream_rq{envoy_response_code=~"5.."}[5m])
```

## 查询优化建议

1. **添加时间范围**: 使用 `rate()` 或 `irate()` 时指定范围
2. **使用 avg_over_time/max_over_time** 进行趋势分析
3. **避免查询无限范围**: 始终指定时间范围
4. **合理使用 `without` 或 `by`**: 减少标签维度提高查询性能

## Web UI

访问 VictoriaMetrics UI：
```
http://prometheus.local:8428/vmui
http://prometheus.local:8428/select/vmui
```

## 常见问题

### Q: 如何查看最近抓取的指标？
A: 查看 `scrape_duration_seconds` 和 `scrape_samples_scraped`

### Q: 如何查询特定的 envoy cluster？
A: 使用 `envoy_cluster_name` 标签过滤

### Q: 如何计算错误率？
A: `(sum(error_count) / sum(total_count)) * 100`
