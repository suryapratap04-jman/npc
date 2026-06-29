# Cache Monitoring Metrics

This report displays the live cache statistics, hit ratios, memory usage, and namespace stats.

## 1. System Caching Stats

- **Cache Enabled**: True
- **Total Cache Keys**: 6
- **Cache Hits Count**: 3
- **Cache Misses Count**: 7
- **Hit Ratio**: 30.0%
- **Memory Usage**: 150KB (Mock Fallback)
- **Connected Clients**: 1

## 2. Active Namespaces

| Namespace | TTL | Description |
| :--- | :--- | :--- |
| `recommendation` | 15 minutes | Resource rankings and LLM explanations |
| `dashboard` | 5 minutes | Health cards and KPI summaries |
| `forecast` | 30 minutes | Rolling capacity and demand projections |
| `health` | 10 minutes | Risk metrics and project billing audits |
| `embedding` | 24 hours | Search query string vector representations |
| `search` | 30 minutes | Semantic search results list |
| `employee` | 24 hours | Full relational profile summaries |
| `project` | 24 hours | Relational project configurations |
| `copilot` | 60 minutes | Session histories and fit context summaries |
