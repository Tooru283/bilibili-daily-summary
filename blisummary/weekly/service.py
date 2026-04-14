import os

from blisummary.common.ai import run_claude_prompt
from blisummary.config import WEEKLY_FOLDER, weekly_summary_path
from blisummary.storage.stats_store import load_week_stats
from blisummary.weekly.analytics import analyze_problems, calc_week_aggregates, generate_suggestions
from blisummary.weekly.render import archive_week, build_markdown



def generate_ai_summary(agg: dict, problems: list[dict], day_stats: list[dict]) -> str:
    problem_text = "\n".join(
        f"- {problem['level']} {problem['title']}：" + "；".join(problem["details"])
        for problem in problems
    )
    day_text = "\n".join(
        f"  {day['date']}：{day['total_videos']}个视频，{day['total_watch_time']/3600:.1f}h，评分{day['score']}"
        for day in day_stats
    )
    prompt = f"""根据以下B站本周观看数据，生成简洁的周总结分析（200字以内）：

周汇总：总视频{agg['total_videos']}个，总时长{agg['total_time']/3600:.1f}h，
平均每日{agg['avg_daily_time']/3600:.1f}h，深度观看{agg['total_deep']}个（{agg['deep_ratio']*100:.0f}%），
周均分{agg['avg_score']}分。

每日数据：
{day_text}

检测到的问题：
{problem_text if problem_text else '无明显问题'}

请分析：1. 本周整体趋势  2. 最值得改进的一点  3. 一句话总结。
"""
    result = run_claude_prompt(prompt)
    return result.stdout if result.returncode == 0 else ""



def generate_weekly_summary(week_number, monday, sunday):
    print(f"\n📅 第{week_number}周（{monday} ~ {sunday}）")

    day_stats = load_week_stats(monday, sunday)
    if not day_stats:
        print("❌ 未找到本周任何日报数据")
        return

    print(f"   读取到 {len(day_stats)} 天数据")

    agg = calc_week_aggregates(day_stats)
    problems = analyze_problems(agg, day_stats)
    suggestions = generate_suggestions(agg, problems)

    print("   🤖 生成 AI 总结...")
    ai_summary = generate_ai_summary(agg, problems, day_stats)
    content = build_markdown(week_number, monday, sunday, day_stats, agg, problems, suggestions, ai_summary)

    dest_folder = archive_week(week_number, monday, sunday, day_stats)
    out_path = weekly_summary_path(dest_folder, week_number, monday)
    with open(out_path, "w", encoding="utf-8") as file:
        file.write(content)

    print(f"   ✅ 已保存: {out_path}")
    print(f"   📊 周均分: {agg['avg_score']}/100  |  问题数: {len(problems)}")



def ensure_weekly_folder():
    os.makedirs(WEEKLY_FOLDER, exist_ok=True)
