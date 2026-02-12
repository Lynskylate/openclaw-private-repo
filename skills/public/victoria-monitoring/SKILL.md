---
name: victoria-monitoring
description: Query and analyze metrics, logs, and traces from VictoriaMetrics and VictoriaLogs monitoring stack. Use when querying system observability data, checking service health, investigating errors, analyzing performance, or exploring the 8 monitored targets (local VictoriaMetrics, node_exporter, VictoriaLogs, Envoy; plus remote servers and Aliyun).
---

# Victoria Monitoring

## Overview

Query and analyze observability data from the VictoriaMetrics stack deployed locally:
- **VictoriaMetrics** (prometheus.local:8428) - Time-series metrics collection and storage
- **VictoriaLogs** (loki.local:9428) - Log aggregation and querying (LogSQL)

**Monitored targets:** 8 services (4 local + 4 remote) including VictoriaMetrics self-monitoring, node_exporter, VictoriaLogs/VictoriaTraces, Envoy, remote servers, and Aliyun Envoy.

## Quick Start

### Health Check
```bash
curl http://prometheus.local:8428/health    # VictoriaMetrics
curl http://loki.local:9428/health           # VictoriaLogs
```

### Query Metrics
```bash
# Check all targets
curl "http://prometheus.local:8428/api/v1/query?query=up"

# Get error rate
curl "http://prometheus.local:8428/api/v1/query?query=rate(envoy_cluster_upstream_rq{envoy_response_code=~\"5..\"}[5m])"
```

### Query Logs
```bash
# Search recent errors
curl -X POST "http://loki.local:9428/select/logsql/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "level=\"error\"", "limit": 10}'

# Search by job
curl -X POST "http://loki.local:9428/select/logsql/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "job=\"victoriametrics\" AND level=\"error\""}'
```

## Query Types

### 1. Metrics Queries (VictoriaMetrics)

**Use when:** Checking service health, analyzing performance, monitoring resource usage, or creating alerts.

**Common patterns:**
- Service uptime: `up`
- Error rates: `sum(rate(envoy_cluster_upstream_rq{envoy_response_code=~"5.."}[5m])) / sum(rate(envoy_cluster_upstream_rq[5m]))`
- Latency P99: `histogram_quantile(0.99, rate(envoy_cluster_upstream_rq_time_bucket[5m]))`
- CPU usage: `rate(process_cpu_seconds_total[5m]) * 100`
- Memory usage: `process_resident_memory_bytes / 1024 / 1024`

**Need more details?** See [metrics-reference.md](references/metrics-reference.md) for complete query patterns and examples.

### 2. Logs Queries (VictoriaLogs - LogSQL)

**Use when:** Searching for errors, debugging issues, finding specific events, or correlating logs with metrics.

**LogSQL patterns:**
- Simple search: `error`, `warning`, `"connection refused"`
- Field filters: `job="victoriametrics"`, `level="error"`, `stream="stdout"`
- Time range: `_time >= now() - 1h`
- Combos: `job="victoriametrics" AND level="error" AND _time >= now() - 1h`
- Regex: `msg =~ "error.*[0-9]+"`

**Need more details?** See [logs-reference.md](references/logs-reference.md) for comprehensive LogSQL syntax and examples.

### 3. Targets Information

**Use when:** Checking monitored services, understanding monitoring coverage, or investigating scrape issues.

**Current targets:**
- Local: VictoriaMetrics (8428), node_exporter (9100), VictoriaLogs (9428), local Envoy (9901)
- Remote: production server (142.171.205.19:443), production Envoy (142.171.205.19:443), Aliyun Envoy (47.120.46.128:80), internal node (192.168.31.58:9100)

Check target status:
```bash
curl "http://prometheus.local:8428/api/v1/targets"
```

**Need more details?** See [targets.md](references/targets.md) for complete target information and troubleshooting.

### 4. Traces (VictoriaTraces)

**Use when:** Tracing request flows, finding root causes of errors, or analyzing distributed system performance.

**Status:** ✅ Fully operational at http://prometheus.local:9428 with Jaeger API support.

**Current services being traced:**
- envoy-gtr (operations: ingress, router grafana_service egress, router logs_service egress, router openclaw_gateway egress, router victoriametrics_service egress)
- envoy-iZf8z8qpzl0oqrzqf1y9t1Z
- otel-smoke
- test-service

**Jaeger API patterns:**
```bash
# List all services
curl "http://prometheus.local:9428/select/jaeger/api/services"

# Query traces for a service
curl "http://prometheus.local:9428/select/jaeger/api/traces?service=envoy-gtr&limit=10"

# Get operations for a service
curl "http://prometheus.local:9428/select/jaeger/api/services/envoy-gtr/operations"

# Query by trace ID
curl "http://prometheus.local:9428/select/jaeger/api/traces?traceID=abc123"

# Service dependencies
curl "http://prometheus.local:9428/select/jaeger/api/dependencies"
```

**Ingestion metrics:**
- Data received: ~6.8MB traces
- Protocols: OTLP gRPC (:9429), OTLP HTTP, Jaeger (if configured)

**Need more details?** See [traces-reference.md](references/traces-reference.md) for full API reference and integration patterns.

## Common Workflows

### Checking Service Health

```bash
# 1. Check all targets are up
curl "http://prometheus.local:8428/api/v1/query?query=up"

# 2. Check for scrape errors
curl "http://prometheus.local:8428/metrics" | grep scrape_error

# 3. Check logs for issues
curl -X POST "http://loki.local:9428/select/logsql/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "level=\"error\"", "limit": 20}'
```

### Investigating High Error Rate

```bash
# 1. Identify error spike
curl "http://prometheus.local:8428/api/v1/query?query=rate(envoy_cluster_upstream_rq{envoy_response_code=~\"5..\"}[5m])"

# 2. Find time range
curl "http://prometheus.local:8428/api/v1/query_range?query=rate(envoy_cluster_upstream_rq{envoy_response_code=~\"5..\"}[5m])&start=$(date -d '1h ago' +%s)&end=$(date +%s)&step=60"

# 3. Search logs for that time
curl -X POST "http://loki.local:9428/select/logsql/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "status_code >= 500", "start": "-1h", "limit": 50}'
```

### Analyzing Performance

```bash
# 1. Measure latency
curl "http://prometheus.local:8428/api/v1/query?query=histogram_quantile(0.99, rate(envoy_cluster_upstream_rq_time_bucket[5m]))"

# 2. Find slow requests
curl -X POST "http://loki.local:9428/select/logsql/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "duration_seconds > 5", "limit": 20}'

# 3. Correlate with errors
curl -X POST "http://loki.local:9428/select/logsql/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "(duration_seconds > 5 OR status_code >= 500)", "limit": 20}'
```

### Monitoring Resource Usage

```bash
# 1. CPU usage
curl "http://prometheus.local:8428/api/v1/query?query=rate(process_cpu_seconds_total[5m]) * 100"

# 2. Memory usage
curl "http://prometheus.local:8428/api/v1/query?query=process_resident_memory_bytes / 1024 / 1024"

# 3. Check all services
curl "http://prometheus.local:8428/api/v1/query?query=process_resident_memory_bytes"
```

## Service Architecture

| Service | Address | Purpose |
|---------|---------|---------|
| VictoriaMetrics | prometheus.local:8428 | Metrics storage and querying |
| VictoriaLogs | loki.local:9428 | Log storage and querying |
| VictoriaTraces | prometheus.local:9428 | Distributed tracing (Jaeger API + OTLP) |

## Web UI

- **VictoriaMetrics**: http://prometheus.local:8428/vmui
- **VictoriaLogs**: http://loki.local:9428/select/logsql
- **VictoriaTraces**: http://prometheus.local:9428/select/vmui

## Reference Files

When you need more detail:

- **[metrics-reference.md](references/metrics-reference.md)** - Complete PromQL query guide, metric patterns, and examples
- **[logs-reference.md](references/logs-reference.md)** - LogSQL syntax, query patterns, and common scenarios
- **[targets.md](references/targets.md)** - All monitored targets, their health status, and troubleshooting
- **[traces-reference.md](references/traces-reference.md)** - Tracing patterns, correlation with metrics/logs, and best practices

## Constraints and Notes

- Traces API availability needs verification (VictoriaTraces integrated with VictoriaLogs)
- Default scrape interval: 1 minute
- Logs retention depends on disk space (not currently documented)
- Time zones: All timestamps in UTC (ISO 8601 format)
