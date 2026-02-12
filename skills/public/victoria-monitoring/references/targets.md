# Targets 参考

## 监控 Targets 概览

此文档列出了 VictoriaMetrics 监控的所有 targets 及其详细信息。

### 获取当前 targets
```bash
curl "http://prometheus.local:8428/api/v1/targets"
```

## 本地 Targets

### 1. VictoriaMetrics (自监控)
- **地址**: 127.0.0.1:8428
- **Job**: victoriametrics
- **路径**: /metrics
- **抓取间隔**: 1m
- **状态**: up
- **指标数量**: ~1600

**监控内容**:
- 自身进程指标 (CPU、内存)
- Scrape 性能指标
- HTTP 请求指标
- PromQL 函数性能

**常用查询**:
```promql
# 查看进程状态
up{job="victoriametrics", instance="127.0.0.1:8428"}

# CPU 使用率
rate(process_cpu_seconds_total{job="victoriametrics", instance="127.0.0.1:8428"}[5m])

# 内存使用
process_resident_memory_bytes{job="victoriametrics", instance="127.0.0.1:8428"}
```

### 2. Node Exporter (本地)
- **地址**: 127.0.0.1:9100
- **Job**: victoriametrics
- **路径**: /metrics
- **抓取间隔**: 1m
- **状态**: up

**监控内容**:
- CPU、内存、磁盘
- 网络流量
- 系统负载
- 文件系统使用

**常用查询**:
```promql
# 系统负载
node_load1{instance="127.0.0.1:9100"}

# CPU 使用率
100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle", instance="127.0.0.1:9100"}[5m])) * 100)

# 内存使用率
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

# 磁盘使用率
(1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100
```

### 3. VictoriaLogs/VictoriaTraces
- **地址**: 127.0.0.1:9428
- **Job**: victoriatraces
- **路径**: /metrics
- **抓取间隔**: 1m
- **状态**: up

**监控内容**:
- 日志处理性能
- 存储性能
- HTTP/2 连接
- 内存使用

**常用查询**:
```promql
# 服务状态
up{job="victoriatraces", instance="127.0.0.1:9428"}

# CPU 使用率
rate(process_cpu_seconds_total{job="victoriatraces", instance="127.0.0.1:9428"}[5m])

# 日志合并性能
vl_merge_duration_seconds{quantile="0.99"}

# 缓存性能
(vm_cache_requests_total{type="promql/parse"} - vm_cache_misses_total{type="promql/parse"}) / vm_cache_requests_total{type="promql/parse"}
```

### 4. Local Envoy
- **地址**: 127.0.0.1:9901
- **Job**: local_envoy
- **路径**: /stats/prometheus
- **抓取间隔**: 1m
- **状态**: up

**监控内容**:
- Envoy 集群状态
- HTTP/2 流量
- 连接状态
- 请求/响应指标

**常用查询**:
```promql
# 集群状态
envoy_cluster_upstream_rq

# 错误率
sum(envoy_cluster_upstream_rq{job="local_envoy", envoy_response_code=~"5.."}) / sum(envoy_cluster_upstream_rq{job="local_envoy"})

# 活跃连接
envoy_listener_downstream_cx_active{job="local_envoy"}
```

## 远程 Targets

### 1. Production Server
- **地址**: 142.171.205.19:443
- **Job**: remote_server
- **环境**: production
- **服务器标签**: remote
- **状态**: up

**监控内容**:
- 应用性能指标
- 端到端指标
- 自定义业务指标

**常用查询**:
```promql
# 服务健康
up{job="remote_server", server="remote"}

# 抓取延迟
scrape_duration_seconds{job="remote_server", server="remote"}

# 抓取样本数
scrape_samples_scraped{job="remote_server", server="remote"}
```

### 2. Production Envoy
- **地址**: 142.171.205.19:443
- **Job**: remote_server_envoy
- **环境**: production
- **服务器标签**: remote
- **状态**: up

**监控内容**:
- 网关流量
- 后端服务可观测性
- 连接池状态
- 断路器状态

**常用查询**:
```promql
# 流量
sum(envoy_cluster_upstream_rq{job="remote_server_envoy", server="remote"})

# 错误率
sum(envoy_cluster_upstream_rq{job="remote_server_envoy", env="production", envoy_response_code=~"5.."}) / sum(envoy_cluster_upstream_rq{job="remote_server_envoy", env="production"})

# 断路器状态
envoy_cluster_circuit_breakers_default_rq_open{job="remote_server_envoy", server="remote"}
```

### 3. Aliyun Envoy
- **地址**: 47.120.46.128:80
- **Job**: aliyun_envoy
- **状态**: up

**监控内容**:
- Aliyun 网关流量
- 客户端接入可观测性
- 地理位置分布

**常用查询**:
```promql
# 请求量
sum(envoy_cluster_upstream_rq{job="aliyun_envoy"})

# 响应时间 P99
histogram_quantile(0.99, rate(envoy_cluster_upstream_rq_time_bucket{job="aliyun_envoy"}[5m]))
```

### 4. 内网节点
- **地址**: 192.168.31.58:9100
- **Job**: victoriametrics
- **状态**: up

**监控内容**:
- 内网节点资源使用
- 磁盘 IO
- 网络连通性

**常用查询**:
```promql
# CPU 使用率
rate(process_cpu_seconds_total{instance="192.168.31.58:9100"}[5m])

# 内存使用
process_resident_memory_bytes{instance="192.168.31.58:9100"}
```

## Targets 健康检查

### 检查所有 targets 状态
```bash
curl -s "http://prometheus.local:8428/api/v1/targets" | \
  jq -r '.data.activeTargets[] | "\(.labels.job): \(.labels.instance) - \(.health) - Last: \(.lastScrape)"'
```

### 查看失败的 targets
```bash
curl -s "http://prometheus.local:8428/api/v1/targets" | \
  jq -r '.data.activeTargets[] | select(.health != "up")'
```

### 通过 PromQL 查询
```bash
# 所有 up targets
curl "http://prometheus.local:8428/api/v1/query?query=up"

# 只看 down 的 targets
curl "http://prometheus.local:8428/api/v1/query?query=up==0"
```

## Target 配置

### 抓取配置
```yaml
# 默认抓取间隔
scrape_interval: 1m
scrape_timeout: 10s
```

### 指标统计
每个 target 每次抓取的指标数量：
```bash
curl "http://prometheus.local:8428/api/v1/query?query=scrape_samples_scraped"
```

## Target 故障排查

### 检查抓取错误
```bash
curl "http://prometheus.local:8428/metrics" | grep -E "scrape_error|promscrape"
```

查看 scrape 错误：
```bash
# Promscrape 配置重载错误
vm_promscrape_config_reloads_errors_total

# Prometheus client 错误
scrape_samples_scraped{success="0"}
```

### 常见问题

1. **Target 状态为 down**:
   - 检查 target 是否可达
   - 检查 metrics 端点是否正常
   - 查看 lastError 信息

2. **抓取指标为 0**:
   - 检查 exporter 是否正常提供指标
   - 查看抓取日志是否有错误

3. **抓取延迟过高**:
   - 查看 scrape_duration_seconds 指标
   - 检查 target 网络延迟
   - 考虑调整 scrape_interval

## Envoy Cluster 信息

### 集群名称
通过查询 envoy_cluster 相关指标获取集群列表：
```bash
curl "http://prometheus.local:8428/api/v1/query?query=envoy_cluster_upstream_rq" | \
  jq -r '.data.result[].metric.envoy_cluster_name' | sort -u
```

### 常见的集群监控指标
- `envoy_cluster_upstream_rq` - 上游请求总数
- `envoy_cluster_upstream_rq_time` - 请求时长
- `envoy_cluster_upstream_rq_completed` - 完成的请求数
- `envoy_cluster_upstream_rq_xx` - HTTP 状态码统计
- `envoy_cluster_circuit_breakers_*` - 断路器状态
- `envoy_cluster_external_upstream_rq` - 外部上游请求

### 查询特定集群
```promql
# 集群流量
envoy_cluster_upstream_rq{envoy_cluster_name="my_service"}

# 集群错误率
sum(envoy_cluster_upstream_rq{envoy_cluster_name="my_service", envoy_response_code=~"5.."}) / sum(envoy_cluster_upstream_rq{envoy_cluster_name="my_service"})
```

## 环境

### 环境标签
- `env="production"` - 生产环境
- `env="test"` - 测试环境（如有）
- 无标签 - 默认环境

### 查询特定环境
```promql
# 生产环境所有 targets
up{env="production"}

# 生产环境错误率
sum(rate(envoy_cluster_upstream_rq{env="production", envoy_response_code=~"5.."}[5m])) / sum(rate(envoy_cluster_upstream_rq{env="production"}[5m]))
```

## 与 Logs 关联

### 从日志查找 scrape 问题
```sql
job="victoriametrics" AND msg:"scrape" AND "error"
```

### 查找 target 连接问题
```sql
msg:"connection" AND "error" AND "timeout"
```

## 总结

当前监控架构：
- **本地实例**: 4 个 (VictoriaMetrics x2, Node Exporter, Envoy)
- **远程实例**: 4 个 (Production x2, Aliyun, 内网)
- **总 Target 数**: 8 个
- **全部状态**: ✅ up

所有 targets 的健康状态和指标历史都可以通过 VictoriaMetrics API 查询。
