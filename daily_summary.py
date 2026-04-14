#!/usr/bin/env python3
"""
B站观看日报生成器
用法:
    python daily_summary.py
    python daily_summary.py --date 2026-03-10
"""

import argparse

from blisummary.daily.service import run_daily_summary



def main():
    parser = argparse.ArgumentParser(description="生成B站每日观看总结")
    parser.add_argument(
        "--date",
        "-d",
        metavar="YYYY-MM-DD",
        help="生成指定日期的总结（默认生成今日+检查昨日）",
    )
    args = parser.parse_args()
    run_daily_summary(args.date)


if __name__ == "__main__":
    main()
