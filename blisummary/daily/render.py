from blisummary.common.formatting import format_duration



def format_history_top10(history_list):
    """格式化TOP10历史记录"""
    sorted_list = sorted(history_list, key=lambda item: item.get("progress", 0), reverse=True)[:10]

    lines = []
    for index, item in enumerate(sorted_list, 1):
        view_time = item.get("view_time")
        if not view_time:
            from datetime import datetime

            view_time = datetime.fromtimestamp(item["view_at"]).strftime("%H:%M")
        title = item.get("title", "")
        author = item.get("author", "")
        tname = item.get("tname", "")
        progress = format_duration(item.get("progress", 0))
        duration = format_duration(item.get("duration", 0))
        watch_percent = item.get("watch_percent", 0)
        bvid = item.get("bvid", "")

        lines.append(
            f"{index}. [{title}](https://www.bilibili.com/video/{bvid})\n"
            f"   - UP: {author} | 分区: {tname}\n"
            f"   - 观看: {progress}/{duration} ({watch_percent}%) | 时间: {view_time}"
        )
    return "\n".join(lines)



def generate_time_heatmap(hour_stats):
    """生成时间分布热力图"""
    lines = ["### 🕐 时间分布热力图", ""]

    if not hour_stats:
        return "### 🕐 时间分布热力图\n\n暂无数据"

    active_hours = sorted([hour for hour in hour_stats.keys() if hour_stats[hour] > 0])
    if not active_hours:
        return "### 🕐 时间分布热力图\n\n暂无数据"

    header = "| 时段 | " + " | ".join([f"{hour:02d}:00" for hour in active_hours]) + " |"
    separator = "|------| " + " | ".join(["------" for _ in active_hours]) + " |"
    counts = "| 视频数 | " + " | ".join([str(hour_stats.get(hour, 0)) for hour in active_hours]) + " |"
    density = "| 密度 | " + " | ".join([_get_density(hour_stats.get(hour, 0)) for hour in active_hours]) + " |"

    lines.extend([header, separator, counts, density])
    lines.append("")
    lines.append("**时段分析：**")

    peak_hour = max(hour_stats.items(), key=lambda pair: pair[1])
    lines.append(f"- 📈 高峰时段：{peak_hour[0]:02d}:00（{peak_hour[1]}个视频）")

    morning = sum(hour_stats.get(hour, 0) for hour in range(6, 12))
    afternoon = sum(hour_stats.get(hour, 0) for hour in range(12, 18))
    evening = sum(hour_stats.get(hour, 0) for hour in range(18, 24))
    night = sum(hour_stats.get(hour, 0) for hour in range(0, 6))

    total = morning + afternoon + evening + night
    if total > 0:
        if morning > 0:
            lines.append(f"- 🌅 上午(6-12点)：{morning}个（{round(morning / total * 100)}%）")
        if afternoon > 0:
            lines.append(f"- ☀️ 下午(12-18点)：{afternoon}个（{round(afternoon / total * 100)}%）")
        if evening > 0:
            lines.append(f"- 🌙 晚上(18-24点)：{evening}个（{round(evening / total * 100)}%）")
        if night > 0:
            lines.append(f"- 🌃 深夜(0-6点)：{night}个（{round(night / total * 100)}%）")

    return "\n".join(lines)



def _get_density(count):
    if count == 0:
        return "⚪"
    if count <= 3:
        return "🟡" * min(count, 3)
    if count <= 7:
        return "🟠" * 3
    return "🔴" * 3



def _stars(count):
    return "★" * count + "☆" * (5 - count)



def generate_video_classification_stats(video_stats, quality_scores):
    """生成视频分类统计"""
    lines = ["## 📦 视频分类统计", ""]
    lines.append("### 按时长分类")
    lines.append("")
    lines.append("| 类型 | 数量 | 高质量数 | 观看时长 | 质量占比 |")
    lines.append("|------|------|----------|----------|----------|")

    long_video = video_stats["long_video"]
    medium_video = video_stats["medium_video"]
    short_video = video_stats["short_video"]

    long_ratio = round(long_video["quality_count"] / long_video["count"] * 100) if long_video["count"] > 0 else 0
    medium_ratio = round(medium_video["quality_count"] / medium_video["count"] * 100) if medium_video["count"] > 0 else 0
    short_ratio = round(short_video["quality_count"] / short_video["count"] * 100) if short_video["count"] > 0 else 0

    lines.append(f"| 长视频(>10min) | {long_video['count']} | {long_video['quality_count']} | {format_duration(long_video['total_time'])} | {long_ratio}% |")
    lines.append(f"| 中视频(3-10min) | {medium_video['count']} | {medium_video['quality_count']} | {format_duration(medium_video['total_time'])} | {medium_ratio}% |")
    lines.append(f"| 短视频(<3min) | {short_video['count']} | {short_video['quality_count']} | {format_duration(short_video['total_time'])} | {short_ratio}% |")
    lines.append(f"| └─ 碎片(<1min) | {short_video['fragment_count']} | - | - | - |")
    lines.append("")
    lines.append("### 质量评分（1-5星）")
    lines.append("")
    lines.append("**长视频质量**")
    lines.append(f"- 知识增量：{_stars(quality_scores['long_video']['knowledge_gain'])}")
    lines.append(f"- 思考深度：{_stars(quality_scores['long_video']['thinking_depth'])}")
    lines.append(f"- 制作质量：{_stars(quality_scores['long_video']['production_quality'])}")
    lines.append("")
    lines.append("**短视频质量**")
    lines.append(f"- 信息密度：{_stars(quality_scores['short_video']['info_density'])}")
    lines.append(f"- 实用价值：{_stars(quality_scores['short_video']['practical_value'])}")
    lines.append(f"- 情绪价值：{_stars(quality_scores['short_video']['emotional_value'])}")
    lines.append("")
    return "\n".join(lines)



def generate_quality_rating(history_list, classified):
    """生成内容质量评分"""
    lines = ["## ⭐ 今日精华内容", ""]

    long_videos = sorted(classified["long"], key=lambda item: item.get("watch_percent", 0), reverse=True)[:3]
    short_quality = [item for item in classified["short"] if item.get("watch_percent", 0) >= 80]
    short_quality = sorted(short_quality, key=lambda item: item.get("progress", 0), reverse=True)[:2]
    worst = [item for item in history_list if item.get("progress", 0) < 30]
    worst = sorted(worst, key=lambda item: item.get("progress", 0))[:3]

    if long_videos:
        lines.append("### 🏆 最佳长视频")
        lines.append("")
        for item in long_videos:
            stars_count = min(5, int(item["watch_percent"] / 20))
            stars_str = _stars(stars_count)
            bvid = item.get("bvid", "")
            duration_str = format_duration(item["duration"])
            lines.append(f"- **[{item['title']}](https://www.bilibili.com/video/{bvid})** - {stars_str}")
            lines.append(f"  - UP: {item['author']} | 完成度: {item['watch_percent']}% | 时长: {duration_str}")
            lines.append("  - 💬 为什么值得：_记录你的感受_")
            lines.append("  - 🎯 适合人群：_填写推荐理由_")
        lines.append("")

    if short_quality:
        lines.append("### 👍 最佳短视频")
        lines.append("")
        for item in short_quality:
            bvid = item.get("bvid", "")
            lines.append(f"- **[{item['title']}](https://www.bilibili.com/video/{bvid})**")
            lines.append(f"  - UP: {item['author']} | 完成度: {item['watch_percent']}%")
        lines.append("")

    if worst:
        lines.append("### ⚠️ 最差点击（避免再次点击）")
        lines.append("")
        for item in worst:
            lines.append(f"- {item['title']} - ★☆☆☆☆")
            lines.append(f"  - 观看仅{item['progress']}秒")
        lines.append("")

    return "\n".join(lines)



def generate_up_recommendations(stats):
    """生成优质UP主推荐列表"""
    lines = ["## 👤 今日发现的优质创作者", ""]
    top_authors = stats["authors"][:5]
    if not top_authors:
        return ""

    lines.append("### 重点关注的UP主")
    lines.append("")
    lines.append("| UP主 | 观看时长 | 视频数 | 推荐指数 |")
    lines.append("|------|----------|--------|----------|")

    for author, data in top_authors:
        time_str = format_duration(data["watch_time"])
        mid = data.get("mid", "")
        if data["watch_time"] >= 1800:
            stars = "⭐⭐⭐⭐⭐"
        elif data["watch_time"] >= 900:
            stars = "⭐⭐⭐⭐"
        elif data["watch_time"] >= 300:
            stars = "⭐⭐⭐"
        else:
            stars = "⭐⭐"

        author_link = f"[{author}](https://space.bilibili.com/{mid})" if mid else author
        lines.append(f"| {author_link} | {time_str} | {data['count']} | {stars} |")

    lines.append("")
    return "\n".join(lines)



def generate_goal_tracking(stats, video_stats, content_score, advanced_score):
    """生成目标管理追踪"""
    lines = ["## 🎯 每日目标追踪", ""]

    video_goal = 130
    time_goal = int(4 * 3600)
    deep_goal = 5

    total_videos = stats["total_videos"]
    total_time = stats["total_watch_time"]
    deep_count = stats["deep_watch_count"]

    lines.append("### 基础目标")
    lines.append("")
    lines.append("| 目标 | 实际 | 目标 | 状态 |")
    lines.append("|------|------|------|------|")

    video_status = "✅" if total_videos <= video_goal else "❌"
    time_status = "✅" if total_time <= time_goal else "❌"
    deep_status = "✅" if deep_count >= deep_goal else "❌"

    lines.append(f"| 视频数量 | {total_videos}个 | ≤{video_goal}个 | {video_status} |")
    lines.append(f"| 总时长 | {format_duration(total_time)} | ≤{format_duration(time_goal)} | {time_status} |")
    lines.append(f"| 深度观看 | {deep_count}个 | ≥{deep_goal}个 | {deep_status} |")
    lines.append("")
    lines.append("### 内容质量评分")
    lines.append("")
    lines.append("| 维度 | 得分 | 权重 | 加权分 |")
    lines.append("|------|------|------|--------|")
    lines.append(f"| 长视频质量 | {content_score['long_score']} | 40% | {round(content_score['long_score'] * 0.4, 1)} |")
    lines.append(f"| 中视频质量 | {content_score['medium_score']} | 30% | {round(content_score['medium_score'] * 0.3, 1)} |")
    lines.append(f"| 短视频质量 | {content_score['short_score']} | 20% | {round(content_score['short_score'] * 0.2, 1)} |")
    lines.append(f"| 碎片化控制 | {content_score['fragment_penalty']} | 10% | {round(content_score['fragment_penalty'] * 0.1, 1)} |")
    lines.append(f"| **内容质量总分** | - | - | **{content_score['total']}** |")
    lines.append("")
    lines.append("### 行为健康评分")
    lines.append("")
    lines.append("| 维度 | 得分 | 权重 | 说明 |")
    lines.append("|------|------|------|------|")
    lines.append(f"| 时间效率 | {advanced_score['time_efficiency']} | 20% | 高质量时间占比 |")
    lines.append(f"| 行为健康 | {advanced_score['behavior_health']} | 20% | 碎片化控制 |")
    lines.append(f"| 内容质量 | {content_score['total']} | 30% | 多维质量评分 |")
    lines.append(f"| 学习总量 | {advanced_score['learning_volume_score']} | 20% | 质量内容时长（长+中视频） |")
    lines.append(f"| 深度学习 | {advanced_score['deep_learning_bonus'] * 2} | 10% | 长视频≥80%完成（{advanced_score['deep_long_count']}个）|")

    total_score = round(
        advanced_score["time_efficiency"] * 0.2
        + advanced_score["behavior_health"] * 0.2
        + content_score["total"] * 0.3
        + advanced_score["learning_volume_score"] * 0.2
        + advanced_score["deep_learning_bonus"] * 2 * 0.1
    )

    lines.append("")
    lines.append(f"### 📊 今日综合得分：{total_score}/100")
    lines.append("")
    return "\n".join(lines), total_score



def format_statistics(stats):
    """格式化统计数据"""
    lines = []
    lines.append("## 📊 基础统计")
    lines.append("")
    lines.append("| 指标 | 数值 |")
    lines.append("|------|------|")
    lines.append(f"| 观看视频数 | {stats['total_videos']} |")
    lines.append(f"| 总观看时长 | {format_duration(stats['total_watch_time'])} |")
    lines.append(f"| 视频总时长 | {format_duration(stats['total_duration'])} |")
    avg_percent = round(stats["total_watch_time"] / stats["total_duration"] * 100, 1) if stats["total_duration"] > 0 else 0
    lines.append(f"| 平均完成度 | {avg_percent}% |")
    lines.append(f"| 深度观看(>80%) | {stats['deep_watch_count']}个 |")
    lines.append(f"| 碎片浏览(<1分钟) | {stats['shallow_watch_count']}个 |")
    lines.append("")
    lines.append("### 📁 分区统计")
    lines.append("")
    lines.append("| 分区 | 视频数 | 观看时长 | 占比 |")
    lines.append("|------|--------|----------|------|")
    for category, data in stats["categories"][:5]:
        time_str = format_duration(data["watch_time"])
        weight = round(data["watch_time"] / stats["total_watch_time"] * 100, 1) if stats["total_watch_time"] > 0 else 0
        lines.append(f"| {category} | {data['count']} | {time_str} | {weight}% |")
    return "\n".join(lines)



def generate_tags(stats, video_stats, behavior_metrics):
    """生成智能标签"""
    tags = ["bilibili", "每日总结"]
    if stats["total_watch_time"] > 5 * 3600:
        tags.append("长时间浏览")
    if behavior_metrics["avg_completion"] < 8:
        tags.append("碎片化警告")
    if stats["categories"]:
        top_category = stats["categories"][0][0]
        weight = stats["categories"][0][1]["watch_time"] / stats["total_watch_time"] * 100 if stats["total_watch_time"] > 0 else 0
        if weight > 30:
            tags.append(f"{top_category}偏好")
    if stats["deep_watch_count"] >= 10:
        tags.append("深度观看达标")
    if behavior_metrics["quality_time_ratio"] > 0.5:
        tags.append("高质量观看")
    return tags



def generate_content_types(stats):
    """生成内容类型标签"""
    content_types = []
    for category, data in stats["categories"][:5]:
        if data["watch_time"] > 300:
            content_types.append(category)
    return content_types



def generate_reflection_template(stats, video_stats, classified):
    """生成反思模板"""
    lines = ["## 📝 反思日记", ""]
    deep_long = [item for item in classified["long"] if item.get("watch_percent", 0) >= 50]
    fragment_count = video_stats["short_video"]["fragment_count"]

    lines.append("### 今日做得好的地方")
    if deep_long:
        for item in deep_long[:2]:
            lines.append(f"- 深度观看《{item['title']}》（{item['watch_percent']}%）")
    else:
        lines.append("- _（记录今天的亮点）_")
    lines.append("")

    lines.append("### 需要改进的地方")
    if fragment_count > 40:
        lines.append(f"- 碎片化浏览严重（{fragment_count}个视频<1分钟）")
    if stats["total_watch_time"] > 5 * 3600:
        lines.append(f"- 总时长过长（{format_duration(stats['total_watch_time'])}）")
    lines.append("- _（分析不足之处）_")
    lines.append("")

    lines.append("### 明天行动计划")
    lines.append("1. 设定：视频数量控制在100个以内")
    lines.append("2. 策略：长视频先看简介和弹幕，决定是否值得投入")
    lines.append("3. 时间管理：观看总时长控制在 4 小时以内")
    lines.append("")
    return "\n".join(lines)



def generate_comparison(stats, behavior_metrics, yesterday_stats):
    """生成与昨日对比"""
    lines = ["### 📈 与昨日对比", ""]

    if not yesterday_stats:
        lines.append("| 指标 | 今日 | 昨日 | 变化 | 趋势 |")
        lines.append("|------|------|------|------|------|")
        lines.append(f"| 观看时长 | {format_duration(stats['total_watch_time'])} | - | - | ⏸️ 初次 |")
        lines.append(f"| 视频数量 | {stats['total_videos']} | - | - | ⏸️ 初次 |")
        lines.append(f"| 平均完成度 | {behavior_metrics['avg_completion']}% | - | - | ⏸️ 初次 |")
        lines.append(f"| 深度观看 | {stats['deep_watch_count']} | - | - | ⏸️ 初次 |")
        lines.append("")
        return "\n".join(lines)

    lines.append("| 指标 | 今日 | 昨日 | 变化 | 趋势 |")
    lines.append("|------|------|------|------|------|")

    diff = stats["total_watch_time"] - yesterday_stats.get("total_watch_time", 0)
    if diff > 0:
        diff_str = f"+{format_duration(diff)}"
        emoji = "📈"
    elif diff < 0:
        diff_str = f"-{format_duration(abs(diff))}"
        emoji = "📉"
    else:
        diff_str = "0"
        emoji = "➡️"
    lines.append(f"| 观看时长 | {format_duration(stats['total_watch_time'])} | {format_duration(yesterday_stats.get('total_watch_time', 0))} | {diff_str} | {emoji} |")

    diff = stats["total_videos"] - yesterday_stats.get("total_videos", 0)
    diff_str = f"+{diff}" if diff > 0 else str(diff)
    emoji = "📈" if diff > 0 else ("📉" if diff < 0 else "➡️")
    lines.append(f"| 视频数量 | {stats['total_videos']} | {yesterday_stats.get('total_videos', 0)} | {diff_str} | {emoji} |")

    diff = round(behavior_metrics["avg_completion"] - yesterday_stats.get("avg_completion", 0), 1)
    diff_str = f"+{diff}%" if diff > 0 else f"{diff}%"
    emoji = "📈" if diff > 0 else ("📉" if diff < 0 else "➡️")
    lines.append(f"| 平均完成度 | {behavior_metrics['avg_completion']}% | {yesterday_stats.get('avg_completion', 0)}% | {diff_str} | {emoji} |")

    diff = stats["deep_watch_count"] - yesterday_stats.get("deep_watch_count", 0)
    diff_str = f"+{diff}" if diff > 0 else str(diff)
    emoji = "📈" if diff > 0 else ("📉" if diff < 0 else "➡️")
    lines.append(f"| 深度观看 | {stats['deep_watch_count']} | {yesterday_stats.get('deep_watch_count', 0)} | {diff_str} | {emoji} |")
    lines.append("")
    return "\n".join(lines)



def generate_dataview_queries():
    """生成 Dataview 查询模板"""
    return """## 🔍 数据查询

### 本周观看记录
```dataview
TABLE WITHOUT ID
  file.link as "日期",
  video_count as "视频数",
  round(total_time / 3600, 1) as "小时",
  score as "得分"
FROM #bilibili
WHERE week_number = this.week_number AND date.year = this.date.year
SORT date DESC
```

### 视频分类趋势
```dataview
TABLE WITHOUT ID
  file.link as "日期",
  video_stats.long_video.quality_count as "优质长视频",
  video_stats.short_video.fragment_count as "碎片视频",
  behavior_metrics.quality_time_ratio * 100 + "%" as "优质时间比"
FROM #bilibili
WHERE date >= date(today) - dur(7 days)
SORT date DESC
```

### 碎片化警告记录
```dataview
TABLE WITHOUT ID
  file.link as "日期",
  video_count as "视频数",
  behavior_metrics.avg_completion + "%" as "完成度"
FROM #bilibili AND #碎片化警告
SORT date DESC
LIMIT 5
```
"""
