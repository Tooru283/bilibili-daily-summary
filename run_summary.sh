#!/bin/bash

# 切换到脚本目录
cd /Users/moca/Work/Python/Blisummary

# 激活虚拟环境
source .venv/bin/activate

# 设置PATH，确保能找到homebrew命令（claude等）
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

# 运行Python脚本
python daily_summary.py >> /tmp/bilisummary.log 2>&1

# 记录执行时间
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Daily summary completed" >> /tmp/bilisummary.log
