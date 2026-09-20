#!/usr/bin/env bash
set -e

# Jev System One WebUI 一键启动脚本
cd "$(dirname "$0")"

echo "=== 启动 Jev Playground ==="
echo "基于 uv 环境管理，服务监听于 http://0.0.0.0:8000"

uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
