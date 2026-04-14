import json
import os
from datetime import datetime, timedelta

from blisummary.config import SUMMARY_FOLDER, stats_json_path, summary_markdown_path
from blisummary.models import LoadedDayStats, StoredDayStats



def _parse_frontmatter_fields(text):
    """简单解析 YAML frontmatter 中的数值字段（无外部依赖）"""
    result = {}
    stack = [result]
    indent_stack = [-1]

    for line in text.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()

        while len(indent_stack) > 1 and indent <= indent_stack[-1]:
            stack.pop()
            indent_stack.pop()

        if ":" not in stripped:
            continue

        key, _, val = stripped.partition(":")
        key = key.strip()
        val = val.strip()

        if val == "" or val is None:
            new_dict = {}
            stack[-1][key] = new_dict
            stack.append(new_dict)
            indent_stack.append(indent)
        else:
            try:
                stack[-1][key] = int(val)
            except ValueError:
                try:
                    stack[-1][key] = float(val)
                except ValueError:
                    stack[-1][key] = val.strip('"').strip("'")

    return result



def extract_stats_from_summary_file(target_date):
    """从已生成的总结 MD 文件中提取统计数据（.stats JSON 不存在时的备用方案）"""
    date_str = target_date.strftime("%Y-%m-%d")
    md_file = summary_markdown_path(target_date)

    if not os.path.exists(md_file):
        return None

    try:
        with open(md_file, "r", encoding="utf-8") as file:
            content = file.read()

        if not content.startswith("---"):
            return None
        end = content.find("\n---", 3)
        if end == -1:
            return None

        frontmatter_text = content[3:end]
        frontmatter = _parse_frontmatter_fields(frontmatter_text)
        if not frontmatter:
            return None

        behavior_metrics = frontmatter.get("behavior_metrics") or {}
        video_stats = frontmatter.get("video_stats") or {}
        short_video = video_stats.get("short_video") or {}

        return {
            "total_videos": frontmatter.get("video_count"),
            "total_watch_time": frontmatter.get("total_time"),
            "deep_watch_count": frontmatter.get("deep_watch"),
            "avg_completion": behavior_metrics.get("avg_completion"),
            "quality_time_ratio": behavior_metrics.get("quality_time_ratio"),
            "fragment_count": short_video.get("fragment_count"),
            "score": frontmatter.get("score"),
        }
    except Exception:
        return None



def load_stats_by_date(target_date) -> StoredDayStats | None:
    """加载指定日期的统计数据，优先读取 JSON，不存在时从 MD 文件恢复"""
    os.makedirs(SUMMARY_FOLDER, exist_ok=True)
    date_str = target_date.strftime("%Y-%m-%d")
    stats_file = stats_json_path(target_date)

    if os.path.exists(stats_file):
        with open(stats_file, "r", encoding="utf-8") as file:
            return json.load(file)

    fallback = extract_stats_from_summary_file(target_date)
    if fallback:
        print(f"   ℹ️ .stats JSON 不存在，已从 {date_str}-B站总结.md 恢复统计数据")
    return fallback



def load_yesterday_stats() -> StoredDayStats | None:
    yesterday = (datetime.now() - timedelta(days=1)).date()
    return load_stats_by_date(yesterday)



def save_stats_by_date(target_date, stats, video_stats, behavior_metrics, score, video_positions=None):
    os.makedirs(SUMMARY_FOLDER, exist_ok=True)
    stats_file = stats_json_path(target_date)

    save_data = {
        "total_videos": stats["total_videos"],
        "total_watch_time": stats["total_watch_time"],
        "deep_watch_count": stats["deep_watch_count"],
        "avg_completion": behavior_metrics["avg_completion"],
        "quality_time_ratio": behavior_metrics["quality_time_ratio"],
        "fragment_count": video_stats["short_video"]["fragment_count"],
        "score": score,
        "video_positions": video_positions or {},
    }

    with open(stats_file, "w", encoding="utf-8") as file:
        json.dump(save_data, file)



def load_day_stats(target_date) -> LoadedDayStats | None:
    data = load_stats_by_date(target_date)
    if not data:
        return None

    result = dict(data)
    result["date"] = target_date
    return result



def load_week_stats(monday, sunday) -> list[LoadedDayStats]:
    result = []
    current = monday
    while current <= sunday:
        stats = load_day_stats(current)
        if stats:
            result.append(stats)
        current += timedelta(days=1)
    return result
