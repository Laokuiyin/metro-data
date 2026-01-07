#!/bin/bash

# Ubuntu/Linux 系统卸载脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PATH="$SCRIPT_DIR/weibo.py"

echo "=========================================="
echo "卸载上海地铁数据抓取定时任务 (Ubuntu)"
echo "=========================================="

# 检查任务是否存在
if ! crontab -l 2>/dev/null | grep -q "$SCRIPT_PATH"; then
    echo "⚠️  未找到已安装的任务"
    exit 0
fi

# 删除定时任务
crontab -l 2>/dev/null | grep -v "$SCRIPT_PATH" | crontab -

echo "✅ 定时任务已卸载"

