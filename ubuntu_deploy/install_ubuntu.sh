#!/bin/bash

# Ubuntu/Linux 系统安装脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_CMD="python3"

echo "=========================================="
echo "安装上海地铁数据抓取定时任务 (Ubuntu)"
echo "=========================================="

# 检查 Python3
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3，请先安装 Python3"
    exit 1
fi

# 检查 pip3
if ! command -v pip3 &> /dev/null; then
    echo "警告: 未找到 pip3，尝试安装..."
    # 尝试安装 pip3
    if command -v apt-get &> /dev/null; then
        echo "使用 apt-get 安装 pip3..."
        sudo apt-get update && sudo apt-get install -y python3-pip
    elif command -v yum &> /dev/null; then
        echo "使用 yum 安装 pip3..."
        sudo yum install -y python3-pip
    else
        echo "错误: 未找到 pip3，且无法自动安装。请手动安装："
        echo "  Ubuntu/Debian: sudo apt-get install python3-pip"
        echo "  CentOS/RHEL: sudo yum install python3-pip"
        exit 1
    fi
fi

# 创建日志目录
mkdir -p "$SCRIPT_DIR/logs"

# 创建虚拟环境（如果不存在）
VENV_DIR="$SCRIPT_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "创建 Python 虚拟环境..."
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "错误: 无法创建虚拟环境，尝试安装 python3-venv..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y python3-venv
        elif command -v yum &> /dev/null; then
            sudo yum install -y python3-venv
        else
            echo "错误: 无法自动安装 python3-venv，请手动安装后重试"
            exit 1
        fi
        python3 -m venv "$VENV_DIR"
    fi
fi

# 安装 Python 依赖
echo "安装 Python 依赖包..."
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"

# 获取虚拟环境中的 Python 和脚本的绝对路径
PYTHON_PATH="$VENV_DIR/bin/python"
SCRIPT_PATH="$SCRIPT_DIR/weibo.py"

# 创建 cron 任务
# 时间格式：分钟 小时 日期 月份 星期
# 示例：0 11 * * * 表示每天 11:00
# 示例：30 9 * * * 表示每天 09:30
# 示例：0 14 * * * 表示每天 14:00
CRON_TIME="10 11 * * *"  # 每天 11:30 执行
CRON_JOB="$CRON_TIME $PYTHON_PATH $SCRIPT_PATH >> $SCRIPT_DIR/logs/cron.log 2>&1"

# 检查是否已存在相同的任务
if crontab -l 2>/dev/null | grep -q "$SCRIPT_PATH"; then
    echo "检测到已存在的定时任务，先删除..."
    crontab -l 2>/dev/null | grep -v "$SCRIPT_PATH" | crontab -
fi

# 添加新的定时任务
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo ""
echo "✅ 定时任务安装成功！"
echo ""
echo "任务信息："
# 解析并显示执行时间
CRON_HOUR=$(echo $CRON_TIME | awk '{print $2}')
CRON_MIN=$(echo $CRON_TIME | awk '{print $1}')
echo "  - 执行时间: 每天 ${CRON_HOUR}:${CRON_MIN} (系统时区)"
echo "  - Python 路径: $PYTHON_PATH (虚拟环境)"
echo "  - 虚拟环境: $VENV_DIR"
echo "  - 脚本路径: $SCRIPT_PATH"
echo "  - 日志文件: $SCRIPT_DIR/logs/cron.log"
echo ""
echo "常用命令："
echo "  查看定时任务: crontab -l"
echo "  编辑定时任务: crontab -e"
echo "  查看日志: tail -f $SCRIPT_DIR/logs/cron.log"
echo "  测试运行: $PYTHON_PATH $SCRIPT_PATH"
echo "  卸载任务: ./uninstall_ubuntu.sh"
echo ""
echo "注意：依赖包已安装到虚拟环境中，cron 任务会自动使用虚拟环境的 Python"
echo ""

