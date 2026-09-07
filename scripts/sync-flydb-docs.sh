#!/usr/bin/env sh
set -eu

# 用法：./scripts/sync-flydb-docs.sh [--check] [Flydb 仓库路径]
# Python 标准库实现，兼容 macOS/Linux；默认使用相邻的 Flydb checkout。
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$SCRIPT_DIR/sync_flydb_docs.py" "$@"
