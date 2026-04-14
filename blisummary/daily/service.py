import os
from datetime import datetime, timedelta

from blisummary.bilibili.client import enrich_multipart_history, get_bilibili_cookies, get_bilibili_history
from blisummary.common.ai import run_claude_prompt
from blisummary.config import SUMMARY_FOLDER, stats_json_path, summary_markdown_path
from blisummary.daily.metrics import (
    calculate_advanced_score,
    calculate_behavior_metrics,
    calculate_content_quality_score,
    calculate_quality_scores,
    calculate_statistics,
    calculate_video_stats,
    classify_videos,
    filter_history_by_date,
)
from blisummary.daily.render import (
    format_history_top10,
    format_statistics,
    generate_comparison,
    generate_content_types,
    generate_dataview_queries,
    generate_goal_tracking,
    generate_quality_rating,
    generate_reflection_template,
    generate_tags,
    generate_time_heatmap,
    generate_up_recommendations,
    generate_video_classification_stats,
)
from blisummary.storage.stats_store import load_stats_by_date, load_yesterday_stats, save_stats_by_date



def generate_summary_with_claude(stats_text: str, classification_text: str, quality_text: str) -> str:
    """调用 Claude Code 生成总结"""
    prompt = f"""请根据以下B站观看数据，生成简洁的每日总结：

{stats_text}

{classification_text}

{quality_text}

请生成总结，包含：
1. 今日观看习惯分析（分析长/中/短视频分布）
2. 内容质量评价（基于质量评分数据）
3. 具体改进建议（针对碎片化、时间管理等问题）
4. 一句话总结

请简洁明了，重点突出问题和建议。
"""
    result = run_claude_prompt(prompt)
    return result.stdout



def get_yesterday_summary_file_path():
    """获取昨天总结文件路径"""
    yesterday = (datetime.now() - timedelta(days=1)).date()
    return summary_markdown_path(yesterday)



def should_regenerate_yesterday_summary() -> bool:
    """判断是否需要重新生成昨天的总结。"""
    yesterday = (datetime.now() - timedelta(days=1)).date()

    md_path = get_yesterday_summary_file_path()
    stats_path = stats_json_path(yesterday)

    md_exists = os.path.exists(md_path)
    stats_exists = os.path.exists(stats_path)

    if not md_exists and not stats_exists:
        return True
    if datetime.now().weekday() == 0:
        return False

    ref_path = md_path if md_exists else stats_path
    file_mtime = datetime.fromtimestamp(os.path.getmtime(ref_path))
    cutoff_time = datetime.combine(yesterday, datetime.strptime("23:30", "%H:%M").time())
    return file_mtime < cutoff_time



def generate_summary_for_date(history_list, target_date, prev_day_stats=None, cookies=None):
    """为指定日期生成总结"""
    date_str = target_date.strftime("%Y-%m-%d")
    week_number = target_date.isocalendar()[1]

    day_history = filter_history_by_date(history_list, target_date)
    if not day_history:
        print(f"📅 {date_str} 没有观看记录")
        return None

    print(f"📅 正在生成 {date_str} 的总结（{len(day_history)}条记录）...")

    if cookies:
        prev_video_positions = (prev_day_stats or {}).get("video_positions", {})
        day_history = enrich_multipart_history(day_history, prev_video_positions, cookies)

    video_positions = {}
    for item in day_history:
        bvid = item.get("bvid", "")
        page_num = (item.get("page") or {}).get("page") or 1
        if bvid:
            video_positions[bvid] = max(video_positions.get(bvid, 0), page_num)

    stats = calculate_statistics(day_history)
    classified = classify_videos(day_history)
    video_stats = calculate_video_stats(classified)
    quality_scores = calculate_quality_scores(classified, video_stats)
    behavior_metrics = calculate_behavior_metrics(day_history, video_stats)
    content_score = calculate_content_quality_score(video_stats, quality_scores)
    advanced_score = calculate_advanced_score(video_stats, behavior_metrics, classified)

    stats_text = format_statistics(stats)
    classification_text = generate_video_classification_stats(video_stats, quality_scores)
    goal_text, total_score = generate_goal_tracking(stats, video_stats, content_score, advanced_score)
    quality_text = generate_quality_rating(day_history, classified)
    heatmap_text = generate_time_heatmap(stats["hour_stats"])
    history_text = format_history_top10(day_history)
    up_text = generate_up_recommendations(stats)
    reflection_text = generate_reflection_template(stats, video_stats, classified)
    dataview_text = generate_dataview_queries()
    comparison_text = generate_comparison(stats, behavior_metrics, prev_day_stats)

    save_stats_by_date(target_date, stats, video_stats, behavior_metrics, total_score, video_positions)

    tags = generate_tags(stats, video_stats, behavior_metrics)
    content_types = generate_content_types(stats)

    print("   🤖 生成 AI 总结...")
    summary = generate_summary_with_claude(stats_text, classification_text, quality_text)

    hours = round(stats["total_watch_time"] / 3600, 1)
    tags_yaml = "\n  - ".join(tags)
    content_types_yaml = "\n  - ".join(content_types) if content_types else "未分类"

    content = f"""---
date: {date_str}
tags:
  - {tags_yaml}
week_number: {week_number}
total_time: {stats['total_watch_time']}
video_count: {stats['total_videos']}
deep_watch: {stats['deep_watch_count']}
score: {total_score}
video_stats:
  long_video:
    count: {video_stats['long_video']['count']}
    quality_count: {video_stats['long_video']['quality_count']}
    total_time: {video_stats['long_video']['total_time']}
  medium_video:
    count: {video_stats['medium_video']['count']}
    quality_count: {video_stats['medium_video']['quality_count']}
    total_time: {video_stats['medium_video']['total_time']}
  short_video:
    count: {video_stats['short_video']['count']}
    quality_count: {video_stats['short_video']['quality_count']}
    fragment_count: {video_stats['short_video']['fragment_count']}
    total_time: {video_stats['short_video']['total_time']}
quality_scores:
  long_video:
    knowledge_gain: {quality_scores['long_video']['knowledge_gain']}
    thinking_depth: {quality_scores['long_video']['thinking_depth']}
    production_quality: {quality_scores['long_video']['production_quality']}
  short_video:
    info_density: {quality_scores['short_video']['info_density']}
    practical_value: {quality_scores['short_video']['practical_value']}
    emotional_value: {quality_scores['short_video']['emotional_value']}
behavior_metrics:
  avg_completion: {behavior_metrics['avg_completion']}
  peak_hour: "{behavior_metrics['peak_hour']}"
  quality_time_ratio: {behavior_metrics['quality_time_ratio']}
content_types:
  - {content_types_yaml}
---

# B站每日总结 - {date_str}

> 📅 周次：第{week_number}周 | ⏰ 时长：{hours}小时 | 🎯 得分：{total_score}/100

### 快捷操作
- [🔗 B站历史记录](https://www.bilibili.com/account/history)
- [🔗 返回周总结](../周总结/2026-W{week_number:02d}.md)

---

{goal_text}

{comparison_text}

{stats_text}

{classification_text}

{heatmap_text}

{quality_text}

{up_text}

## 📝 今日TOP10（按观看时长排序）

{history_text}

> 📋 [查看完整{stats['total_videos']}条记录](https://www.bilibili.com/account/history)

## 🤖 AI 总结

{summary}

{reflection_text}

---

{dataview_text}
"""

    os.makedirs(SUMMARY_FOLDER, exist_ok=True)
    file_path = summary_markdown_path(target_date)
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)

    print(f"   ✅ 已保存到: {file_path}")
    return {
        "stats": stats,
        "video_stats": video_stats,
        "behavior_metrics": behavior_metrics,
        "score": total_score,
    }



def run_daily_summary(date_arg=None):
    cookies = get_bilibili_cookies()

    if date_arg:
        try:
            target_date = datetime.strptime(date_arg, "%Y-%m-%d").date()
        except ValueError:
            print("❌ 日期格式错误，请使用 YYYY-MM-DD，例如：--date 2026-03-10")
            return

        days_ago = max(0, (datetime.now().date() - target_date).days)
        max_pages = max(50, days_ago + 10)
        print(f"📥 获取B站历史记录（最多 {max_pages} 页，直到覆盖目标日期）...")
        history = get_bilibili_history(cookies, max_pages=max_pages, until_date=target_date)

        if not history:
            print("❌ 获取历史记录失败")
            return

        print(f"   获取到 {len(history)} 条记录")
        print(f"\n📊 生成 {date_arg} 的总结...")
        prev_stats = load_stats_by_date(target_date - timedelta(days=1))
        result = generate_summary_for_date(history, target_date, prev_stats, cookies)

        if result:
            print(f"\n🎉 完成！得分：{result['score']}/100")
        else:
            print(f"\n📭 {date_arg} 没有观看记录")
        return

    print("📥 获取B站历史记录...")
    history = get_bilibili_history(cookies, pages=20)
    if not history:
        print("❌ 获取历史记录失败")
        return

    print(f"   获取到 {len(history)} 条记录")
    print("\n🔄 检查昨日总结...")
    if should_regenerate_yesterday_summary():
        yesterday = (datetime.now() - timedelta(days=1)).date()
        day_before_yesterday = yesterday - timedelta(days=1)
        prev_stats = load_stats_by_date(day_before_yesterday)

        print("   ⚠️ 昨日总结需要重新生成...")
        generate_summary_for_date(history, yesterday, prev_stats, cookies)
    else:
        print("   ✅ 昨日总结已是最新，跳过")

    print("\n📊 生成今日总结...")
    today = datetime.now().date()
    yesterday_stats = load_yesterday_stats()
    result = generate_summary_for_date(history, today, yesterday_stats, cookies)

    if result:
        print(f"\n🎉 完成！今日得分：{result['score']}/100")
    else:
        print("\n📭 今天没有观看记录")
