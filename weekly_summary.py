#!/usr/bin/env python3
"""
B站观看周总结生成器
用法:
    python weekly_summary.py
    python weekly_summary.py -1
    python weekly_summary.py 0
    python weekly_summary.py 2026-W10
"""

import sys

from blisummary.weekly.analytics import parse_week_arg
from blisummary.weekly.service import ensure_weekly_folder, generate_weekly_summary



def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "-1"
    try:
        week_number, monday, sunday = parse_week_arg(arg)
    except ValueError as exc:
        print(f"参数错误: {exc}")
        print("用法: python weekly_summary.py [-1|0|'2026-W10']")
        sys.exit(1)

    ensure_weekly_folder()
    generate_weekly_summary(week_number, monday, sunday)


if __name__ == "__main__":
    main()
