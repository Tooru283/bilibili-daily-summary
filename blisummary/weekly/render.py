import os
import shutil
from datetime import date, datetime, timedelta

from blisummary.config import SUMMARY_FOLDER, WEEKLY_FOLDER, summary_markdown_path, weekly_archive_folder
from blisummary.weekly.analytics import HEALTH



def day_status(day: dict) -> str:
    total_watch_time = day["total_watch_time"]
    fragment_ratio = day["fragment_count"] / max(day["total_videos"], 1)
    if total_watch_time > HEALTH["daily_severe_sec"] or fragment_ratio > 0.8:
        return "🔴 严重超标"
    if total_watch_time > HEALTH["daily_warn_sec"] or fragment_ratio > 0.6:
        return "⚠️ 偏超标"
    if day["score"] >= 65:
        return "✅ 良好"
    return "📊 中等"



def build_markdown(week_number: int, monday: date, sunday: date, day_stats: list[dict], agg: dict, problems: list[dict], suggestions: dict, ai_summary: str) -> str:
    week_str = f"{monday.month}.{monday.day}-{sunday.month}.{sunday.day}"
    title_date = f"{monday.year}.{week_str}"

    lines = [
        "---",
        f"week_number: {week_number}",
        f"week_start: {monday}",
        f"week_end: {sunday}",
        "tags:",
        "  - 周总结",
        "  - bilibili",
        "  - 数据分析",
        "---",
        "",
        f"# 📊 B站观看周总结 — 第{week_number}周（{title_date}）",
        "",
        "---",
        "",
    ]

    avg_h = agg["avg_daily_time"] / 3600
    time_eval = "⚠️ 长时间浏览" if agg["avg_daily_time"] > HEALTH["daily_time_sec"] else "✅ 达标"
    video_eval = "🔴 严重碎片化" if agg["avg_daily_videos"] > 50 else ("⚠️ 偏多" if agg["avg_daily_videos"] > HEALTH["daily_videos"] else "✅ 达标")
    score_eval = "📊 中等水平" if agg["avg_score"] < HEALTH["weekly_score"] else "✅ 良好"

    lines += [
        "## 📈 本周总体数据",
        "",
        "| 指标 | 数值 | 评价 |",
        "|------|------|------|",
        f"| **总观看时长** | {agg['total_time']:,} 秒（{agg['total_time']/3600:.1f} 小时） | {time_eval} |",
        f"| **总视频数** | {agg['total_videos']} 个 | {video_eval} |",
        f"| **平均每日时长** | {avg_h:.2f} 小时 | {'❌ 过长' if avg_h > HEALTH['daily_severe_sec']/3600 else ('⚠️ 略长' if avg_h > HEALTH['daily_warn_sec']/3600 else '✅')} |",
        f"| **深度观看** | {agg['total_deep']} 个（占比 {agg['deep_ratio']*100:.1f}%） | {'✅' if agg['deep_ratio'] >= HEALTH['deep_watch_ratio'] else '⚠️ 偏低'} |",
        f"| **周平均评分** | {agg['avg_score']}/100 | {score_eval} |",
        f"| **平均完成度** | {agg['avg_completion']}% | {'✅' if agg['avg_completion'] >= HEALTH['avg_completion'] else '⚠️ 偏低'} |",
        "",
        "---",
        "",
    ]

    lines += [
        "## 📅 日均对比",
        "",
        "| 日期 | 视频数 | 时长 | 深度观看 | 评分 | 状态 |",
        "|------|--------|------|---------|------|------|",
    ]
    for day in day_stats:
        lines.append(
            f"| {day['date']} | {day['total_videos']} | {day['total_watch_time']/3600:.1f}h | {day['deep_watch_count']} | {day['score']} | {day_status(day)} |"
        )
    lines += ["", "---", ""]

    fragment_pct = agg["fragment_ratio"] * 100
    deep_pct = agg["deep_ratio"] * 100
    score_gap = agg["avg_score"] - HEALTH["weekly_score"]

    time_cell = ("✅" if agg["avg_daily_time"] <= HEALTH["daily_time_sec"] else "⚠️ 略超基线" if agg["avg_daily_time"] <= HEALTH["daily_warn_sec"] else f"❌ 超警告线{(agg['avg_daily_time'] - HEALTH['daily_warn_sec'])/3600:.1f}h")
    frag_limit = HEALTH["fragment_ratio"] * 100
    frag_cell = "✅" if fragment_pct <= frag_limit else f"❌ 超{fragment_pct - frag_limit:.1f}%"
    deep_target = HEALTH["deep_watch_ratio"] * 100
    deep_cell = "✅" if deep_pct >= deep_target else f"❌ 差{deep_target - deep_pct:.1f}%"
    score_cell = "✅" if score_gap >= 0 else f"❌ 差{-score_gap:.1f}分"

    lines += [
        "## 📊 数据对标",
        "",
        "| 指标 | 本周 | 健康标准 | 差距 |",
        "|------|------|----------|------|",
        f"| 每日时长 | {avg_h:.2f}h | 基线{HEALTH['daily_time_sec']/3600:.1f}h / 警告{HEALTH['daily_warn_sec']/3600:.1f}h | {time_cell} |",
        f"| 碎片视频占比 | {fragment_pct:.1f}% | ≤{frag_limit:.0f}% | {frag_cell} |",
        f"| 深度观看占比 | {deep_pct:.1f}% | ≥{deep_target:.0f}% | {deep_cell} |",
        f"| 周评分 | {agg['avg_score']}/100 | ≥{HEALTH['weekly_score']}/100 | {score_cell} |",
        "",
        "---",
        "",
    ]

    if ai_summary:
        lines += ["## 🤖 AI 总结", "", ai_summary.strip(), "", "---", ""]

    if problems:
        lines += ["## 🎯 本周问题分析", ""]
        for index, problem in enumerate(problems, 1):
            lines.append(f"### {index}️⃣ {problem['level']} {problem['title']}")
            for detail in problem["details"]:
                lines.append(f"- {detail}")
            lines.append("")
        lines += ["---", ""]

    lines += ["## 💡 改进建议", ""]
    if suggestions["urgent"]:
        lines += ["### 🔴 紧急行动", ""]
        for index, suggestion in enumerate(suggestions["urgent"], 1):
            lines.append(f"{index}. {suggestion}")
        lines.append("")
    if suggestions["mid"]:
        lines += ["### 🟡 中期优化", ""]
        for suggestion in suggestions["mid"]:
            lines.append(f"- {suggestion}")
        lines.append("")
    if suggestions["long"]:
        lines += ["### 🟢 长期目标", ""]
        for suggestion in suggestions["long"]:
            lines.append(f"- {suggestion}")
        lines.append("")
    lines += ["---", ""]

    next_wn = week_number + 1
    lines += [
        "## 📝 下周目标",
        "",
        f"### 🎯 Week {next_wn} 行动计划",
        "",
        "1. **时间目标**",
        "   - 每日观看时长控制在 1.5-2 小时",
        "2. **质量目标**",
        f"   - 深度观看 ≥{max(agg['total_deep'], int(agg['total_videos'] * HEALTH['deep_watch_ratio']))} 个",
        f"   - 周评分目标 ≥{HEALTH['weekly_score']}/100",
        "3. **习惯目标**",
        "   - _（填写具体计划）_",
        "",
        "---",
        "",
    ]

    lines += ["## 🔗 相关日报", ""]
    for day in day_stats:
        lines.append(f"- [[{day['date']}-B站总结]]")
    lines += [
        "",
        "---",
        "",
        f"> **周总结时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')} 生成",
        f"> **数据源**：{len(day_stats)} 天观看历史",
        f"> **下次周总结**：{sunday + timedelta(days=8)}",
        "",
    ]

    return "\n".join(lines)



def archive_week(week_number: int, monday: date, sunday: date, day_stats: list[dict]) -> str:
    """将日报 .md 文件移动到周文件夹，返回目标文件夹路径。"""
    if sunday >= date.today():
        print("   ⏭ 本周未结束，跳过归档")
        return SUMMARY_FOLDER

    dest = weekly_archive_folder(week_number, monday, sunday)
    os.makedirs(dest, exist_ok=True)

    moved = 0
    for day in day_stats:
        src = summary_markdown_path(day["date"])
        if os.path.exists(src):
            shutil.move(src, os.path.join(dest, os.path.basename(src)))
            moved += 1

    print(f"   📁 已归档 {moved} 个日报到 {os.path.basename(dest)}/")
    return dest

