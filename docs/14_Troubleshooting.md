# 14. Troubleshooting

Common errors and solutions for local developer environments.

## 1. Database Connection Failures
- **Issue**: `ConnectionRefusedError: [WinError 10061]` when connecting to Qdrant or Postgres.
- **Solution**: Stop local services binding to ports `5432` or `6333` before starting Docker containers.

## 2. WSL Memory Bottlenecks
- **Issue**: Docker containers restart with `Exit Code 137` (OOM).
- **Solution**: Set a RAM ceiling in your Windows host `.wslconfig` file.
