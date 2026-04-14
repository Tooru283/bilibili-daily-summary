from datetime import date, timedelta
import re


HEALTH = {
    "daily_time_sec": int(3.5 * 3600),
    "daily_warn_sec": int(4.5 * 3600),
    "daily_severe_sec": int(5.5 * 3600),
    "daily_videos": 60,
    "deep_watch_ratio": 0.30,
    "fragment_ratio": 0.45,
    "weekly_score": 65,
    "avg_completion": 28.0,
}



def get_week_bounds(offset: int = -1) -> tuple[int, date, date]:
    """返回 (week_number, monday, sunday)，offset=-1 为上周，0 为本周"""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    monday += timedelta(weeks=offset)
    sunday = monday + timedelta(days=6)
    week_number = monday.isocalendar()[1]
    return week_number, monday, sunday



def parse_week_arg(arg: str) -> tuple[int, date, date]:
    """解析命令行参数，支持 -1/0 或 '2026-W10'"""
    if re.fullmatch(r"-?\d+", arg):
        return get_week_bounds(int(arg))
    match = re.fullmatch(r"(\d{4})-W(\d{1,2})", arg)
    if match:
        year, week_number = int(match.group(1)), int(match.group(2))
        jan4 = date(year, 1, 4)
        week1_monday = jan4 - timedelta(days=jan4.weekday())
        monday = week1_monday + timedelta(weeks=week_number - 1)
        sunday = monday + timedelta(days=6)
        return week_number, monday, sunday
    raise ValueError(f"无法解析参数: {arg}")



def calc_week_aggregates(day_stats: list[dict]) -> dict:
    """计算周汇总指标"""
    if not day_stats:
        return {}

    total_videos = sum(day["total_videos"] for day in day_stats)
    total_time = sum(day["total_watch_time"] for day in day_stats)
    total_deep = sum(day["deep_watch_count"] for day in day_stats)
    total_fragments = sum(day["fragment_count"] for day in day_stats)
    avg_score = round(sum(day["score"] for day in day_stats) / len(day_stats), 1)
    avg_completion = round(sum(day["avg_completion"] for day in day_stats) / len(day_stats), 1)

    days = len(day_stats)
    return {
        "days": days,
        "total_videos": total_videos,
        "total_time": total_time,
        "total_deep": total_deep,
        "total_fragments": total_fragments,
        "avg_daily_time": total_time / days,
        "avg_daily_videos": total_videos / days,
        "avg_score": avg_score,
        "avg_completion": avg_completion,
        "deep_ratio": round(total_deep / total_videos, 3) if total_videos else 0,
        "fragment_ratio": round(total_fragments / total_videos, 3) if total_videos else 0,
        "best_day": max(day_stats, key=lambda day: day["score"]),
        "worst_day": min(day_stats, key=lambda day: day["score"]),
    }



def analyze_problems(agg: dict, day_stats: list[dict]) -> list[dict]:
    """根据数据自动检测问题。"""
    problems = []

    over_days = [day for day in day_stats if day["total_watch_time"] > HEALTH["daily_warn_sec"]]
    severe_days = [day for day in day_stats if day["total_watch_time"] > HEALTH["daily_severe_sec"]]
    if severe_days:
        details = [
            f"{day['date']} 观看 {day['total_watch_time']/3600:.1f}h（超严重线 {(day['total_watch_time'] - HEALTH['daily_severe_sec'])/3600:.1f}h）"
            for day in severe_days
        ]
        worst = max(severe_days, key=lambda day: day["total_watch_time"])
        details.append(
            f"峰值日 {worst['date']}：{worst['total_videos']}个视频，平均每视频仅 {worst['total_watch_time']/max(worst['total_videos'], 1)/60:.1f} 分钟"
        )
        problems.append({"title": "严重的时间管理问题", "level": "🔴", "details": details})
    elif over_days:
        details = [
            f"{day['date']} 观看 {day['total_watch_time']/3600:.1f}h，超过警告线 {HEALTH['daily_warn_sec']//3600}h"
            for day in over_days
        ]
        problems.append({"title": "时间管理偏超标", "level": "🟡", "details": details})

    if agg["fragment_ratio"] > HEALTH["fragment_ratio"]:
        avg_min = agg["total_time"] / max(agg["total_videos"], 1) / 60
        problems.append({
            "title": "碎片化浏览成常态",
            "level": "🔴" if agg["fragment_ratio"] > 0.7 else "🟡",
            "details": [
                f"本周 {agg['total_videos']} 个视频 ÷ {agg['total_time']/3600:.1f}h = 平均每个视频仅 {avg_min:.1f} 分钟",
                f"深度观看仅 {agg['total_deep']} 个，占比 {agg['deep_ratio']*100:.1f}%（目标 ≥{HEALTH['deep_watch_ratio']*100:.0f}%）",
                f"碎片视频 {agg['total_fragments']} 个，占比 {agg['fragment_ratio']*100:.1f}%",
            ],
        })

    if agg["avg_score"] < HEALTH["weekly_score"]:
        gap = HEALTH["weekly_score"] - agg["avg_score"]
        problems.append({
            "title": "内容质量有待提升",
            "level": "🔴" if gap > 20 else "🟡",
            "details": [
                f"周平均评分 {agg['avg_score']}/100（目标 {HEALTH['weekly_score']}，差 {gap:.1f}分）",
                f"平均完成度 {agg['avg_completion']}%（目标 ≥{HEALTH['avg_completion']}%）",
            ],
        })

    scores = [day["score"] for day in day_stats]
    if len(scores) >= 3 and all(scores[index] >= scores[index + 1] for index in range(len(scores) - 1)):
        problems.append({
            "title": "评分持续下滑",
            "level": "🟡",
            "details": [f"本周评分走势：{' → '.join(map(str, scores))}，呈连续下降趋势"],
        })

    return problems



def generate_suggestions(agg: dict, problems: list[dict]) -> dict:
    """根据问题自动生成分层建议"""
    urgent, mid, long_term = [], [], []
    problem_titles = {problem["title"] for problem in problems}

    if "严重的时间管理问题" in problem_titles or "时间管理偏超标" in problem_titles:
        urgent += [
            "设置每日观看时长上限：工作日 ≤3h，休息日 ≤4h（含学习内容）",
            f"每日视频点击数控制在 ≤{HEALTH['daily_videos']} 个",
            "实施「稍后再看」机制，发现兴趣视频先加入列表，固定时段集中观看",
        ]

    if "碎片化浏览成常态" in problem_titles:
        urgent.append("每次打开B站前设定目标：「我要看什么类型的内容」")
        mid += [
            "关闭首页推荐，改用分类订阅减少无目的刷视频",
            f"以深度观看 ≥{int(HEALTH['deep_watch_ratio'] * 100)}% 为日常标准",
        ]

    if "内容质量有待提升" in problem_titles:
        mid += [
            "优先观看时长 ≥10分钟 的内容，刻意减少短视频消费",
            "建立内容收藏库，记录值得复看的视频",
        ]

    long_term += [
        f"目标周评分：{HEALTH['weekly_score']}+/100",
        f"深度观看占比：≥{int(HEALTH['deep_watch_ratio'] * 100)}%",
        f"平均每日时长：≤{HEALTH['daily_time_sec']//3600}小时",
    ]

    return {"urgent": urgent, "mid": mid, "long": long_term}
