#!/usr/bin/env python3
"""
B站观看周总结生成器
自动识别周边界、计算统计、生成问题分析和建议、归档日报文件
用法:
    python weekly_summary.py          # 生成上周总结（默认）
    python weekly_summary.py -1       # 同上
    python weekly_summary.py 0        # 生成本周（当前不完整）总结
    python weekly_summary.py 2026-W10 # 生成指定周
"""

import os
import re
import json
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, date
from pathlib import Path

# ─── 配置 ─────────────────────────────────────────────────────────────────────

SUMMARY_FOLDER = "编辑路径"
WEEKLY_FOLDER  = os.path.join(SUMMARY_FOLDER, "周总结")

# 健康标准基准
HEALTH = {
    "daily_time_sec":      2 * 3600,   # 每日时长上限
    "daily_videos":        30,          # 每日视频数上限
    "deep_watch_ratio":    0.30,        # 深度观看占比目标
    "fragment_ratio":      0.50,        # 碎片视频占比上限
    "weekly_score":        70,          # 周评分目标
    "avg_completion":      40.0,        # 平均完成度目标 %
}

# ─── 周边界计算 ────────────────────────────────────────────────────────────────

def get_week_bounds(offset: int = -1) -> tuple[int, date, date]:
    """返回 (week_number, monday, sunday)，offset=-1 为上周，0 为本周"""
    today = date.today()
    monday = today - timedelta(days=today.weekday())  # 本周一
    monday += timedelta(weeks=offset)
    sunday = monday + timedelta(days=4)               # 工作周到周五，或改为 +6 完整周
    # 用自然周（Mon–Sun）
    sunday = monday + timedelta(days=6)
    week_number = monday.isocalendar()[1]
    return week_number, monday, sunday


def parse_week_arg(arg: str) -> tuple[int, date, date]:
    """解析命令行参数，支持 -1/0 或 '2026-W10'"""
    if re.fullmatch(r"-?\d+", arg):
        return get_week_bounds(int(arg))
    m = re.fullmatch(r"(\d{4})-W(\d{1,2})", arg)
    if m:
        year, wn = int(m.group(1)), int(m.group(2))
        # ISO week 1 的周一
        jan4 = date(year, 1, 4)
        week1_monday = jan4 - timedelta(days=jan4.weekday())
        monday = week1_monday + timedelta(weeks=wn - 1)
        sunday = monday + timedelta(days=6)
        return wn, monday, sunday
    raise ValueError(f"无法解析参数: {arg}")


# ─── 数据加载 ──────────────────────────────────────────────────────────────────

def load_day_stats(target_date: date) -> dict | None:
    """加载指定日期的 .stats_*.json，不存在返回 None"""
    path = os.path.join(SUMMARY_FOLDER, f".stats_{target_date}.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    data["date"] = target_date
    return data


def load_week_stats(monday: date, sunday: date) -> list[dict]:
    """加载一整周的每日统计，跳过不存在的日期"""
    result = []
    d = monday
    while d <= sunday:
        s = load_day_stats(d)
        if s:
            result.append(s)
        d += timedelta(days=1)
    return result


# ─── 统计计算 ──────────────────────────────────────────────────────────────────

def calc_week_aggregates(day_stats: list[dict]) -> dict:
    """计算周汇总指标"""
    if not day_stats:
        return {}

    total_videos    = sum(d["total_videos"]    for d in day_stats)
    total_time      = sum(d["total_watch_time"] for d in day_stats)
    total_deep      = sum(d["deep_watch_count"] for d in day_stats)
    total_fragments = sum(d["fragment_count"]   for d in day_stats)
    avg_score       = round(sum(d["score"] for d in day_stats) / len(day_stats), 1)
    avg_completion  = round(sum(d["avg_completion"] for d in day_stats) / len(day_stats), 1)

    days = len(day_stats)
    return {
        "days":              days,
        "total_videos":      total_videos,
        "total_time":        total_time,
        "total_deep":        total_deep,
        "total_fragments":   total_fragments,
        "avg_daily_time":    total_time / days,
        "avg_daily_videos":  total_videos / days,
        "avg_score":         avg_score,
        "avg_completion":    avg_completion,
        "deep_ratio":        round(total_deep / total_videos, 3) if total_videos else 0,
        "fragment_ratio":    round(total_fragments / total_videos, 3) if total_videos else 0,
        "best_day":          max(day_stats, key=lambda d: d["score"]),
        "worst_day":         min(day_stats, key=lambda d: d["score"]),
    }


# ─── 问题分析（自动生成）──────────────────────────────────────────────────────

def analyze_problems(agg: dict, day_stats: list[dict]) -> list[dict]:
    """
    根据数据自动检测问题，返回问题列表
    每个问题: {"title": str, "level": "🔴"/"🟡"/"🟢", "details": [str]}
    """
    problems = []

    # 1. 时间管理
    over_days = [d for d in day_stats if d["total_watch_time"] > HEALTH["daily_time_sec"]]
    severe_days = [d for d in over_days if d["total_watch_time"] > 3 * 3600]
    if severe_days:
        details = [
            f"{d['date']} 观看 {d['total_watch_time']/3600:.1f}h（超标 "
            f"{(d['total_watch_time'] - HEALTH['daily_time_sec'])/3600:.1f}h）"
            for d in severe_days
        ]
        worst = max(severe_days, key=lambda d: d["total_watch_time"])
        details.append(
            f"峰值日 {worst['date']}：{worst['total_videos']}个视频，"
            f"平均每视频仅 {worst['total_watch_time']/max(worst['total_videos'],1)/60:.1f} 分钟"
        )
        problems.append({"title": "严重的时间管理问题", "level": "🔴", "details": details})
    elif over_days:
        details = [
            f"{d['date']} 观看 {d['total_watch_time']/3600:.1f}h，超过每日 2h 上限"
            for d in over_days
        ]
        problems.append({"title": "时间管理偏超标", "level": "🟡", "details": details})

    # 2. 碎片化
    if agg["fragment_ratio"] > HEALTH["fragment_ratio"]:
        avg_min = agg["total_time"] / max(agg["total_videos"], 1) / 60
        problems.append({
            "title": "碎片化浏览成常态",
            "level": "🔴" if agg["fragment_ratio"] > 0.7 else "🟡",
            "details": [
                f"本周 {agg['total_videos']} 个视频 ÷ {agg['total_time']/3600:.1f}h = "
                f"平均每个视频仅 {avg_min:.1f} 分钟",
                f"深度观看仅 {agg['total_deep']} 个，占比 {agg['deep_ratio']*100:.1f}%"
                f"（目标 ≥{HEALTH['deep_watch_ratio']*100:.0f}%）",
                f"碎片视频 {agg['total_fragments']} 个，占比 {agg['fragment_ratio']*100:.1f}%",
            ],
        })

    # 3. 内容质量
    if agg["avg_score"] < HEALTH["weekly_score"]:
        gap = HEALTH["weekly_score"] - agg["avg_score"]
        level = "🔴" if gap > 20 else "🟡"
        problems.append({
            "title": "内容质量有待提升",
            "level": level,
            "details": [
                f"周平均评分 {agg['avg_score']}/100（目标 {HEALTH['weekly_score']}，差 {gap:.1f}分）",
                f"平均完成度 {agg['avg_completion']}%（目标 ≥{HEALTH['avg_completion']}%）",
            ],
        })

    # 4. 评分趋势（连续下降）
    scores = [d["score"] for d in day_stats]
    if len(scores) >= 3 and all(scores[i] >= scores[i+1] for i in range(len(scores)-1)):
        problems.append({
            "title": "评分持续下滑",
            "level": "🟡",
            "details": [f"本周评分走势：{' → '.join(map(str, scores))}，呈连续下降趋势"],
        })

    return problems


def generate_suggestions(agg: dict, problems: list[dict]) -> dict:
    """根据问题自动生成分层建议"""
    urgent, mid, long_ = [], [], []
    problem_titles = {p["title"] for p in problems}

    if "严重的时间管理问题" in problem_titles or "时间管理偏超标" in problem_titles:
        urgent += [
            f"设置每日观看时长上限：工作日 ≤1.5h，休息日 ≤2.5h",
            f"每日视频点击数控制在 ≤{HEALTH['daily_videos']} 个",
            "实施「稍后再看」机制，发现兴趣视频先加入列表，固定时段集中观看",
        ]

    if "碎片化浏览成常态" in problem_titles:
        urgent.append("每次打开B站前设定目标：「我要看什么类型的内容」")
        mid += [
            "关闭首页推荐，改用分类订阅减少无目的刷视频",
            f"以深度观看 ≥{int(HEALTH['deep_watch_ratio']*100)}% 为日常标准",
        ]

    if "内容质量有待提升" in problem_titles:
        mid += [
            "优先观看时长 ≥10分钟 的内容，刻意减少短视频消费",
            "建立内容收藏库，记录值得复看的视频",
        ]

    long_ += [
        f"目标周评分：{HEALTH['weekly_score']}+/100",
        f"深度观看占比：≥{int(HEALTH['deep_watch_ratio']*100)}%",
        f"平均每日时长：≤{HEALTH['daily_time_sec']//3600}小时",
    ]

    return {"urgent": urgent, "mid": mid, "long": long_}


# ─── 格式化工具 ────────────────────────────────────────────────────────────────

def fmt_dur(seconds: int) -> str:
    seconds = int(seconds)
    h, m = divmod(seconds, 3600)
    m //= 60
    return f"{h}:{m:02d}"


def day_status(d: dict) -> str:
    t = d["total_watch_time"]
    f = d["fragment_count"] / max(d["total_videos"], 1)
    if t > 4 * 3600 or f > 0.8:
        return "🔴 严重超标"
    if t > 2 * 3600 or f > 0.5:
        return "⚠️ 偏超标"
    if d["score"] >= 65:
        return "✅ 良好"
    return "📊 中等"


# ─── Markdown 内容生成 ─────────────────────────────────────────────────────────

def build_markdown(week_number: int, monday: date, sunday: date,
                   day_stats: list[dict], agg: dict,
                   problems: list[dict], suggestions: dict,
                   ai_summary: str) -> str:

    week_str = f"{monday.month}.{monday.day}-{sunday.month}.{sunday.day}"
    title_date = f"{monday.year}.{week_str}"

    # frontmatter
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

    # 总体数据
    avg_h = agg["avg_daily_time"] / 3600
    time_eval  = "⚠️ 长时间浏览" if agg["avg_daily_time"] > HEALTH["daily_time_sec"] else "✅ 达标"
    video_eval = "🔴 严重碎片化" if agg["avg_daily_videos"] > 50 else ("⚠️ 偏多" if agg["avg_daily_videos"] > HEALTH["daily_videos"] else "✅ 达标")
    score_eval = "📊 中等水平" if agg["avg_score"] < HEALTH["weekly_score"] else "✅ 良好"

    lines += [
        "## 📈 本周总体数据",
        "",
        "| 指标 | 数值 | 评价 |",
        "|------|------|------|",
        f"| **总观看时长** | {agg['total_time']:,} 秒（{agg['total_time']/3600:.1f} 小时） | {time_eval} |",
        f"| **总视频数** | {agg['total_videos']} 个 | {video_eval} |",
        f"| **平均每日时长** | {avg_h:.2f} 小时 | {'❌ 过长' if avg_h > 3 else ('⚠️ 略长' if avg_h > 2 else '✅')} |",
        f"| **深度观看** | {agg['total_deep']} 个（占比 {agg['deep_ratio']*100:.1f}%） | {'✅' if agg['deep_ratio'] >= HEALTH['deep_watch_ratio'] else '⚠️ 偏低'} |",
        f"| **周平均评分** | {agg['avg_score']}/100 | {score_eval} |",
        f"| **平均完成度** | {agg['avg_completion']}% | {'✅' if agg['avg_completion'] >= HEALTH['avg_completion'] else '⚠️ 偏低'} |",
        "",
        "---",
        "",
    ]

    # 日均对比
    lines += [
        "## 📅 日均对比",
        "",
        "| 日期 | 视频数 | 时长 | 深度观看 | 评分 | 状态 |",
        "|------|--------|------|---------|------|------|",
    ]
    for d in day_stats:
        lines.append(
            f"| {d['date']} | {d['total_videos']} | "
            f"{d['total_watch_time']/3600:.1f}h | {d['deep_watch_count']} | "
            f"{d['score']} | {day_status(d)} |"
        )
    lines += ["", "---", ""]

    # 与健康标准对比
    fragment_pct   = agg["fragment_ratio"] * 100
    deep_pct       = agg["deep_ratio"] * 100
    score_gap      = agg["avg_score"] - HEALTH["weekly_score"]
    time_over_pct  = (agg["avg_daily_time"] / HEALTH["daily_time_sec"] - 1) * 100

    time_cell     = "✅" if time_over_pct <= 0 else f"❌ 超{time_over_pct:.0f}%"
    frag_limit    = HEALTH["fragment_ratio"] * 100
    frag_cell     = "✅" if fragment_pct <= frag_limit else f"❌ 超{fragment_pct - frag_limit:.1f}%"
    deep_target   = HEALTH["deep_watch_ratio"] * 100
    deep_cell     = "✅" if deep_pct >= deep_target else f"❌ 差{deep_target - deep_pct:.1f}%"
    score_cell    = "✅" if score_gap >= 0 else f"❌ 差{-score_gap:.1f}分"

    lines += [
        "## 📊 数据对标",
        "",
        "| 指标 | 本周 | 健康标准 | 差距 |",
        "|------|------|----------|------|",
        f"| 每日时长 | {avg_h:.2f}h | ≤{HEALTH['daily_time_sec']//3600}h | {time_cell} |",
        f"| 碎片视频占比 | {fragment_pct:.1f}% | ≤{frag_limit:.0f}% | {frag_cell} |",
        f"| 深度观看占比 | {deep_pct:.1f}% | ≥{deep_target:.0f}% | {deep_cell} |",
        f"| 周评分 | {agg['avg_score']}/100 | ≥{HEALTH['weekly_score']}/100 | {score_cell} |",
        "",
        "---",
        "",
    ]

    # AI 总结
    if ai_summary:
        lines += ["## 🤖 AI 总结", "", ai_summary.strip(), "", "---", ""]

    # 问题分析
    if problems:
        lines += ["## 🎯 本周问题分析", ""]
        for i, p in enumerate(problems, 1):
            lines.append(f"### {i}️⃣ {p['level']} {p['title']}")
            for detail in p["details"]:
                lines.append(f"- {detail}")
            lines.append("")
        lines += ["---", ""]

    # 改进建议
    lines += ["## 💡 改进建议", ""]
    if suggestions["urgent"]:
        lines += ["### 🔴 紧急行动", ""]
        for i, s in enumerate(suggestions["urgent"], 1):
            lines.append(f"{i}. {s}")
        lines.append("")
    if suggestions["mid"]:
        lines += ["### 🟡 中期优化", ""]
        for s in suggestions["mid"]:
            lines.append(f"- {s}")
        lines.append("")
    if suggestions["long"]:
        lines += ["### 🟢 长期目标", ""]
        for s in suggestions["long"]:
            lines.append(f"- {s}")
        lines.append("")
    lines += ["---", ""]

    # 下周目标
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

    # 相关日报链接
    lines += ["## 🔗 相关日报", ""]
    for d in day_stats:
        lines.append(f"- [[{d['date']}-B站总结]]")
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


# ─── AI 总结 ──────────────────────────────────────────────────────────────────

def generate_ai_summary(agg: dict, problems: list[dict], day_stats: list[dict]) -> str:
    problem_text = "\n".join(
        f"- {p['level']} {p['title']}：" + "；".join(p["details"])
        for p in problems
    )
    day_text = "\n".join(
        f"  {d['date']}：{d['total_videos']}个视频，{d['total_watch_time']/3600:.1f}h，评分{d['score']}"
        for d in day_stats
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
    result = subprocess.run(["claude", "-p", prompt], capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else ""


# ─── 文件归档 ──────────────────────────────────────────────────────────────────

def archive_week(week_number: int, monday: date, sunday: date,
                 day_stats: list[dict]) -> str:
    """
    将日报 .md 文件移动到周文件夹，返回目标文件夹路径。
    仅在周已结束时执行（sunday < today）。
    """
    if sunday >= date.today():
        print("   ⏭ 本周未结束，跳过归档")
        return SUMMARY_FOLDER

    week_str = f"{monday.month}.{monday.day}-{sunday.month}.{sunday.day}"
    folder_name = f"W{week_number}({monday.year}.{week_str})"
    dest = os.path.join(WEEKLY_FOLDER, folder_name)
    os.makedirs(dest, exist_ok=True)

    moved = 0
    for d in day_stats:
        src = os.path.join(SUMMARY_FOLDER, f"{d['date']}-B站总结.md")
        if os.path.exists(src):
            shutil.move(src, os.path.join(dest, os.path.basename(src)))
            moved += 1

    print(f"   📁 已归档 {moved} 个日报到 {folder_name}/")
    return dest


# ─── 主流程 ───────────────────────────────────────────────────────────────────

def generate_weekly_summary(week_number: int, monday: date, sunday: date):
    print(f"\n📅 第{week_number}周（{monday} ~ {sunday}）")

    # 加载数据
    day_stats = load_week_stats(monday, sunday)
    if not day_stats:
        print("❌ 未找到本周任何日报数据")
        return

    print(f"   读取到 {len(day_stats)} 天数据")

    # 计算
    agg         = calc_week_aggregates(day_stats)
    problems    = analyze_problems(agg, day_stats)
    suggestions = generate_suggestions(agg, problems)

    # AI 总结
    print("   🤖 生成 AI 总结...")
    ai_summary = generate_ai_summary(agg, problems, day_stats)

    # 生成 Markdown
    content = build_markdown(week_number, monday, sunday,
                             day_stats, agg, problems, suggestions, ai_summary)

    # 归档日报（仅当周已结束）
    dest_folder = archive_week(week_number, monday, sunday, day_stats)

    # 保存周总结
    filename = f"{monday.year}-W{week_number:02d}-周总结.md"
    out_path = os.path.join(dest_folder, filename)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"   ✅ 已保存: {out_path}")
    print(f"   📊 周均分: {agg['avg_score']}/100  |  问题数: {len(problems)}")


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "-1"
    try:
        week_number, monday, sunday = parse_week_arg(arg)
    except ValueError as e:
        print(f"参数错误: {e}")
        print("用法: python weekly_summary.py [-1|0|'2026-W10']")
        sys.exit(1)

    os.makedirs(WEEKLY_FOLDER, exist_ok=True)
    generate_weekly_summary(week_number, monday, sunday)


if __name__ == "__main__":
    main()
