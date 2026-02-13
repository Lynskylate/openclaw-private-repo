# Memory

## Important Markers

- **embed-smoke-1770918775** - User marker (added 2026-02-13)

## Key Technical Learnings

### Feishu Doc Operations (from 2026-02-12)
- **400 Error Pattern**: `write` and `append` operations frequently return 400 errors
- **Solution**: Use `update_block` for reliable updates
- **Wiki Documents**: Always create in space_id=7606015010138590169 (openclaw 知识库)
- **Format**: Avoid Markdown tables - convert to lists

### VictoriaMonitoring Stack
- **Metrics**: prometheus.local:8428 (VictoriaMetrics)
- **Logs**: loki.local:9428 (VictoriaLogs) - check if online before querying
- **Traces**: prometheus.local:9428 (VictoriaTraces, Jaeger API compatible)
- **Gateway**: openclaw-gateway service with tracing enabled
- **Monitoring**: 8 targets (4 local + 4 remote including Aliyun and production servers)

### Active Skills (2026-02-13)
- **Feishu Suite**: feishu-doc, feishu-drive, feishu-wiki (documents, storage, knowledge base)
- **Development**: github, mcporter, tmux, playwright-cli
- **Monitoring**: victoria-monitoring, healthcheck, session-logs
- **Web & Data**: tavily, web_fetch
- **Utilities**: weather, skill-creator, canvas, tts, message

### Self-Improvement System (2026-02-13)

**Daily Personal Reports**:
- **Schedule**: Every day at 23:00 (Asia/Shanghai)
- **Job ID**: 2db82cb3-ef06-4766-8c37-92f5e529a490
- **Location**: Feishu 知识库 / 首页/日报/YYYY-MM-DD
- **Content**: Task summary, self-reflection, improvements, metrics, tomorrow's plan

**Key Learnings**:
- VictoriaLogs runs on localhost:8429 (NOT 9428 - that's VictoriaTraces)
- Correct query format: `curl -G "http://localhost:8429/select/logsql/query" --data-urlencode 'query=...'`
- Feishu Wiki API: `write` works for simple content, but read operations often return 400
- Self-troubleshooting guide created at `docs/self-troubleshooting.md` (11.9 KB)