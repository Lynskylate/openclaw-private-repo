# Self-Troubleshooting Guide

_Last updated: 2026-02-12 by 小龙虾 🦞_

## Overview

This guide documents how I (小龙虾) can troubleshoot myself using the VictoriaMetrics monitoring stack deployed locally. It covers metrics, logs, and traces for OpenClaw Gateway and related services.

---

## Monitoring Stack Architecture

### Components

| Component | Address | Purpose | Status |
|-----------|---------|---------|--------|
| **VictoriaMetrics** | prometheus.local:8428 | Time-series metrics storage and querying | ✅ Operational |
| **VictoriaLogs** | localhost:8429 | Log aggregation and querying (LogSQL) | ✅ Operational |
| **VictoriaTraces** | prometheus.local:9428 | Distributed tracing (Jaeger API compatible) | ✅ Operational |
| **Gateway Logs** | /var/log/openclaw/gateway.log | Local log file | ✅ Accessible |

### Monitored Targets

**Total: 8 targets** (4 local + 4 remote)

**Local:**
- VictoriaMetrics (127.0.0.1:8428)
- node_exporter (127.0.0.1:9100)
- VictoriaTraces (127.0.0.1:9428)
- Envoy (127.0.0.1:9901)

**Remote:**
- Production server (142.171.205.19:443)
- Production Envoy (142.171.205.19:443)
- Aliyun Envoy (47.120.46.128:80)
- Internal node (192.168.31.58:9100)

---

## Query Patterns

### 1. Health Checks

```bash
# Check all services
curl http://prometheus.local:8428/health    # VictoriaMetrics
curl http://localhost:8429/health           # VictoriaLogs
curl http://prometheus.local:9428/health    # VictoriaTraces

# Check monitored targets
curl "http://prometheus.local:8428/api/v1/query?query=up"
```

### 2. Metrics Queries (VictoriaMetrics)

#### OpenClaw Gateway Traffic

```bash
# Total requests by status code
curl -s "http://prometheus.local:8428/api/v1/query?query=envoy_cluster_upstream_rq" | \
  jq '.data.result[] | select(.metric.envoy_cluster_name=="openclaw_gateway")'

# Current request rate (requests per second)
curl -s "http://prometheus.local:8428/api/v1/query?query=rate(envoy_cluster_upstream_rq{envoy_cluster_name=\"openclaw_gateway\"}[5m])"

# Error rate (5xx errors)
curl -s "http://prometheus.local:8428/api/v1/query?query=rate(envoy_cluster_upstream_rq{envoy_cluster_name=\"openclaw_gateway\",envoy_response_code=~\"5..\"}[5m])"
```

#### Service Health

```bash
# All target status
curl -s "http://prometheus.local:8428/api/v1/targets" | jq '.data.activeTargets[] | {job: .labels.job, health: .health, lastError: .lastError}'

# Scrape errors
curl -s "http://prometheus.local:8428/metrics" | grep scrape_error
```

#### Performance Metrics

```bash
# P99 Latency
curl -s "http://prometheus.local:8428/api/v1/query?query=histogram_quantile(0.99, rate(envoy_cluster_upstream_rq_time_bucket[5m]))"

# CPU usage
curl -s "http://prometheus.local:8428/api/v1/query?query=rate(process_cpu_seconds_total[5m]) * 100"

# Memory usage
curl -s "http://prometheus.local:8428/api/v1/query?query=process_resident_memory_bytes / 1024 / 1024"
```

### 3. Logs Queries (VictoriaLogs)

#### ⚠️ IMPORTANT: Correct API Usage

**VictoriaLogs runs on port 8429, NOT 9428!**

```bash
# CORRECT: Query with URL encoding
curl -G "http://localhost:8429/select/logsql/query" \
  --data-urlencode 'query={container_name="openclaw-gateway"}' \
  --data-urlencode 'limit=10'

# WRONG (will fail): Using loki.local:9428
curl -X POST "http://loki.local:9428/select/logsql/query"  # ❌ Wrong port
```

#### Common Log Queries

```bash
# OpenClaw Gateway logs (all)
curl -G "http://localhost:8429/select/logsql/query" \
  --data-urlencode 'query={container_name="openclaw-gateway"}' \
  --data-urlencode 'limit=20'

# Recent errors (last 5 minutes)
curl -G "http://localhost:8429/select/logsql/query" \
  --data-urlencode 'query={container_name="openclaw-gateway"} AND _time:5m' \
  --data-urlencode 'limit=50'

# Tool failures
curl -G "http://localhost:8429/select/logsql/query" \
  --data-urlencode 'query={container_name="openclaw-gateway"} AND "exec failed"' \
  --data-urlencode 'limit=10'

# Feishu message logs
curl -G "http://localhost:8429/select/logsql/query" \
  --data-urlencode 'query={container_name="openclaw-gateway"} AND "feishu"' \
  --data-urlencode 'limit=20'

# Time range query (last hour)
curl -G "http://localhost:8429/select/logsql/query" \
  --data-urlencode 'query={container_name="openclaw-gateway"} AND _time >= now() - 1h' \
  --data-urlencode 'limit=100'
```

#### LogSQL Patterns

- **Simple search**: `error`, `warning`, `"connection refused"`
- **Field filters**: `{container_name="openclaw-gateway"}`, `{level="error"}`
- **Time range**: `_time:5m` (last 5 min), `_time >= now() - 1h` (last hour)
- **Combos**: `{container_name="openclaw-gateway"} AND error AND _time:5m`
- **Regex**: `msg =~ "error.*[0-9]+"`

#### Available Log Streams

From VictoriaLogs discovery (2026-02-12):
- `openclaw-gateway` (47 entries)
- `mihomo` (146 entries)
- `network-monitor` (125 entries)
- `envoy` (10 entries)
- **Total**: 458 log entries

### 4. Traces Queries (VictoriaTraces)

#### List Services

```bash
curl -s "http://prometheus.local:9428/select/jaeger/api/services" | jq -r '.data[]'
```

**Current traced services:**
- `openclaw-gateway`
- `envoy-gtr`
- `envoy-iZf8z8qpzl0oqrzqf1y9t1Z`
- `otel-smoke`
- `test-service`

#### Query Traces for OpenClaw Gateway

```bash
# Recent traces
curl -s "http://prometheus.local:9428/select/jaeger/api/traces?service=openclaw-gateway&limit=10"

# Specific trace by ID
curl -s "http://prometheus.local:9428/select/jaeger/api/traces?traceID=402b74de776a1961c75591e088846671"

# Operations for a service
curl -s "http://prometheus.local:9428/select/jaeger/api/services/openclaw-gateway/operations"

# Service dependencies
curl -s "http://prometheus.local:9428/select/jaeger/api/dependencies"
```

### 5. Local Log Files

```bash
# Real-time Gateway logs
tail -f /var/log/openclaw/gateway.log

# Recent errors
grep -i error /var/log/openclaw/gateway.log | tail -50

# Tool call failures
grep "exec failed" /var/log/openclaw/gateway.log | tail -20

# Feishu messages
grep "feishu" /var/log/openclaw/gateway.log | tail -30
```

---

## Common Troubleshooting Workflows

### Workflow 1: Investigating Tool Failures

**Symptom**: Tools (read, write, exec) are failing

**Steps:**

1. **Check recent errors in logs**
   ```bash
   curl -G "http://localhost:8429/select/logsql/query" \
     --data-urlencode 'query={container_name="openclaw-gateway"} AND "exec failed"' \
     --data-urlencode 'limit=10'
   ```

2. **Check metrics for anomalies**
   ```bash
   # High error rate?
   curl -s "http://prometheus.local:8428/api/v1/query?query=rate(envoy_cluster_upstream_rq{envoy_response_code=~\"5..\"}[5m])"
   ```

3. **Review local logs**
   ```bash
   tail -100 /var/log/openclaw/gateway.log | grep -A 5 -B 5 "exec failed"
   ```

4. **Check traces for failed requests**
   ```bash
   curl -s "http://prometheus.local:9428/select/jaeger/api/traces?service=openclaw-gateway&limit=20" | \
     jq '.data[] | select(.spans[].tags[]?.value | tostring | test("error|5[0-9]{2}"; "i"))'
   ```

---

### Workflow 2: High Error Rate Investigation

**Symptom**: Spike in 5xx errors

**Steps:**

1. **Identify error spike time**
   ```bash
   curl -s "http://prometheus.local:8428/api/v1/query_range?query=rate(envoy_cluster_upstream_rq{envoy_response_code=~\"5..\"}[5m])&start=$(date -d '1h ago' +%s)&end=$(date +%s)&step=60"
   ```

2. **Search logs for that time**
   ```bash
   curl -G "http://localhost:8429/select/logsql/query" \
     --data-urlencode 'query={container_name="openclaw-gateway"} AND _time >= now() - 1h' \
     --data-urlencode 'limit=100'
   ```

3. **Check downstream service health**
   ```bash
   curl -s "http://prometheus.local:8428/api/v1/query?query=up" | \
     jq '.data.result[] | select(.value[1] == "0")'
   ```

---

### Workflow 3: Performance Issues

**Symptom**: Slow response times

**Steps:**

1. **Measure latency**
   ```bash
   curl -s "http://prometheus.local:8428/api/v1/query?query=histogram_quantile(0.99, rate(envoy_cluster_upstream_rq_time_bucket[5m]))"
   ```

2. **Find slow requests in logs**
   ```bash
   curl -G "http://localhost:8429/select/logsql/query" \
     --data-urlencode 'query={container_name="openclaw-gateway"} AND duration_seconds > 5' \
     --data-urlencode 'limit=20'
   ```

3. **Trace slow requests**
   ```bash
   # Get trace IDs from logs, then query
   curl -s "http://prometheus.local:9428/select/jaeger/api/traces?traceID=<trace_id>"
   ```

---

### Workflow 4: File System Issues

**Symptom**: "Read-only file system" errors

**Discovery (2026-02-12):**
- Error: `EROFS: read-only file system, write '<path>'`
- Cause: Skills directory is mounted read-only
- Solution: Write to workspace (`/opt/openclaw/.openclaw/workspace`) instead

**Check logs:**
```bash
grep -i "read-only\|EROFS" /var/log/openclaw/gateway.log | tail -20
```

---

## Known Issues and Solutions

### Issue 1: VictoriaLogs API "missing query" Error

**Problem:**
```bash
curl -X POST "http://localhost:8429/select/logsql/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "..."}'
# Error: cannot parse query []: missing query
```

**Solution:**
Use GET request with URL encoding instead:
```bash
curl -G "http://localhost:8429/select/logsql/query" \
  --data-urlencode 'query=...'
```

---

### Issue 2: Wrong VictoriaLogs Port

**Problem:**
Old documentation showed `loki.local:9428`, but:
- Port 9428 is VictoriaTraces, not VictoriaLogs
- VictoriaLogs is on port 8429

**Solution:**
Always use `localhost:8429` for VictoriaLogs queries.

---

### Issue 3: VictoriaLogs Query Returns Empty

**Problem:**
```bash
curl "http://localhost:8429/select/logsql/streams" --data-raw 'query=1=1'
# Response: {"values":[]}
```

**Cause:**
Query needs to be sent via GET with URL encoding, not POST raw data.

**Solution:**
```bash
curl -G "http://localhost:8429/select/logsql/streams" \
  --data-urlencode 'query=1=1'
```

---

## Web UI Access

For visual exploration and query building:

- **VictoriaLogs UI**: http://localhost:8429/select/vmui
- **VictoriaMetrics UI**: http://prometheus.local:8428/vmui
- **VictoriaTraces UI**: http://prometheus.local:9428/select/vmui

Use `npx playwright-cli open` and navigate to these URLs for interactive exploration.

---

## Quick Reference Card

```bash
# Health check
curl http://prometheus.local:8428/health && curl http://localhost:8429/health && curl http://prometheus.local:9428/health

# OpenClaw Gateway traffic
curl -s "http://prometheus.local:8428/api/v1/query?query=envoy_cluster_upstream_rq{envoy_cluster_name=\"openclaw_gateway\"}" | \
  jq '.data.result[] | "\(.metric.envoy_response_code): \(.value[1])"'

# Gateway errors (last 5 min)
curl -G "http://localhost:8429/select/logsql/query" \
  --data-urlencode 'query={container_name="openclaw-gateway"} AND error AND _time:5m' \
  --data-urlencode 'limit=20'

# Recent traces
curl -s "http://prometheus.local:9428/select/jaeger/api/traces?service=openclaw-gateway&limit=5" | \
  jq '.data[] | {traceID: .traceID, spanCount: (.spans | length)}'

# Local logs
tail -50 /var/log/openclaw/gateway.log
```

---

## Metrics Reference

### OpenClaw Gateway Status (2026-02-12)

From metrics query:
- ✅ HTTP 200: 510 requests
- 🔌 HTTP 101: 67 requests (WebSocket upgrades)
- ❌ HTTP 404: 2 requests (not found)
- ⚠️ HTTP 503: 95 requests (service unavailable)

**Interpretation:**
- High success rate (510/674 = 75.7%)
- Some WebSocket activity (normal for real-time features)
- 95 service unavailable errors need investigation (possible downstream issues)

---

## Related Documentation

- **VictoriaMonitoring Skill**: `/opt/openclaw/.openclaw/workspace/skills/public/victoria-monitoring/SKILL.md`
- **AGENTS.md**: `/opt/openclaw/.openclaw/workspace/AGENTS.md` (references this guide)
- **VictoriaMetrics Docs**: https://docs.victoriametrics.com/
- **VictoriaLogs Docs**: https://docs.victoriametrics.com/victorialogs/
- **VictoriaTraces Docs**: https://docs.victoriametrics.com/victoriatraces/

---

_Last updated: 2026-02-12 by 小龙虾 🦞_
