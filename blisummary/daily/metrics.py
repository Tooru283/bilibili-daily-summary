from collections import defaultdict
from datetime import datetime, timedelta



def filter_history_by_date(history_list, target_date):
    """筛选指定日期的浏览记录"""
    filtered = []
    for item in history_list:
        view_time = datetime.fromtimestamp(item["view_at"]).date()
        if view_time == target_date:
            filtered.append(item)
    return filtered



def filter_today_history(history_list):
    return filter_history_by_date(history_list, datetime.now().date())



def filter_yesterday_history(history_list):
    yesterday = (datetime.now() - timedelta(days=1)).date()
    return filter_history_by_date(history_list, yesterday)



def classify_videos(history_list):
    """按时长分类视频"""
    long_videos = []
    medium_videos = []
    short_videos = []
    fragment_videos = []

    for item in history_list:
        duration = item.get("duration", 0)
        if duration >= 600:
            long_videos.append(item)
        elif duration >= 180:
            medium_videos.append(item)
        else:
            short_videos.append(item)
            if item.get("progress", 0) < 60:
                fragment_videos.append(item)

    return {
        "long": long_videos,
        "medium": medium_videos,
        "short": short_videos,
        "fragment": fragment_videos,
    }



def calculate_video_stats(classified):
    """计算分类视频统计"""
    long_videos = classified["long"]
    medium_videos = classified["medium"]
    short_videos = classified["short"]
    fragment_videos = classified["fragment"]

    long_quality = [video for video in long_videos if video.get("watch_percent", 0) >= 50]
    medium_quality = [video for video in medium_videos if video.get("watch_percent", 0) >= 70]
    short_quality = [video for video in short_videos if video.get("watch_percent", 0) >= 90]

    return {
        "long_video": {
            "count": len(long_videos),
            "quality_count": len(long_quality),
            "total_time": sum(video.get("progress", 0) for video in long_videos),
        },
        "medium_video": {
            "count": len(medium_videos),
            "quality_count": len(medium_quality),
            "total_time": sum(video.get("progress", 0) for video in medium_videos),
        },
        "short_video": {
            "count": len(short_videos),
            "quality_count": len(short_quality),
            "fragment_count": len(fragment_videos),
            "total_time": sum(video.get("progress", 0) for video in short_videos),
        },
    }



def calculate_quality_scores(classified, stats):
    """计算质量评分（1-5星）"""
    long_videos = classified["long"]
    short_videos = classified["short"]

    if long_videos:
        avg_completion = sum(video.get("watch_percent", 0) for video in long_videos) / len(long_videos)
        knowledge_gain = min(5, max(1, int(avg_completion / 20)))
        thinking_depth = min(5, max(1, stats["long_video"]["quality_count"]))
        production_quality = min(5, max(1, int(avg_completion / 15)))
    else:
        knowledge_gain = thinking_depth = production_quality = 0

    if short_videos:
        quality_ratio = stats["short_video"]["quality_count"] / len(short_videos) if short_videos else 0
        fragment_ratio = stats["short_video"]["fragment_count"] / len(short_videos) if short_videos else 0
        info_density = min(5, max(0, int(quality_ratio * 5)))
        practical_value = min(5, max(0, int((1 - fragment_ratio) * 3)))
        emotional_value = min(5, max(1, int(quality_ratio * 3) + 1))
    else:
        info_density = practical_value = emotional_value = 0

    return {
        "long_video": {
            "knowledge_gain": knowledge_gain,
            "thinking_depth": thinking_depth,
            "production_quality": production_quality,
        },
        "short_video": {
            "info_density": info_density,
            "practical_value": practical_value,
            "emotional_value": emotional_value,
        },
    }



def calculate_behavior_metrics(history_list, stats):
    """计算行为指标"""
    total_watch_time = sum(video.get("progress", 0) for video in history_list)
    total_duration = sum(video.get("duration", 0) for video in history_list)
    avg_completion = round(total_watch_time / total_duration * 100, 1) if total_duration > 0 else 0

    hour_stats = defaultdict(int)
    for item in history_list:
        hour = datetime.fromtimestamp(item["view_at"]).hour
        hour_stats[hour] += 1

    peak_hour = max(hour_stats.items(), key=lambda pair: pair[1])[0] if hour_stats else 0
    quality_time = stats["long_video"]["total_time"] + stats["medium_video"]["total_time"]
    quality_time_ratio = round(quality_time / total_watch_time, 2) if total_watch_time > 0 else 0

    return {
        "avg_completion": avg_completion,
        "peak_hour": f"{peak_hour:02d}:00",
        "quality_time_ratio": quality_time_ratio,
    }



def calculate_content_quality_score(video_stats, quality_scores):
    """计算内容质量总分"""
    long_base = min(100, video_stats["long_video"]["quality_count"] * 20)
    long_quality_avg = (
        quality_scores["long_video"]["knowledge_gain"]
        + quality_scores["long_video"]["thinking_depth"]
        + quality_scores["long_video"]["production_quality"]
    ) / 15
    long_score = long_base * long_quality_avg

    medium_score = min(100, video_stats["medium_video"]["quality_count"] * 30)

    short_base = min(100, video_stats["short_video"]["quality_count"] * 40)
    short_quality_avg = (
        quality_scores["short_video"]["info_density"]
        + quality_scores["short_video"]["practical_value"]
        + quality_scores["short_video"]["emotional_value"]
    ) / 15
    short_score = short_base * short_quality_avg

    fragment_penalty = max(0, 100 - (video_stats["short_video"]["fragment_count"] - 10) * 5)
    total = (long_score * 0.4) + (medium_score * 0.3) + (short_score * 0.2) + (fragment_penalty * 0.1)

    return {
        "long_score": round(long_score, 1),
        "medium_score": round(medium_score, 1),
        "short_score": round(short_score, 1),
        "fragment_penalty": round(fragment_penalty, 1),
        "total": round(total, 1),
    }



def calculate_advanced_score(video_stats, behavior_metrics, classified):
    """计算高级评分"""
    time_efficiency = min(100, behavior_metrics["quality_time_ratio"] * 200)
    behavior_health = max(0, 100 - video_stats["short_video"]["fragment_count"] * 1.5)

    quality_total_minutes = (
        video_stats["long_video"]["total_time"] + video_stats["medium_video"]["total_time"]
    ) / 60
    learning_volume_score = min(100, quality_total_minutes / 30 * 20)
    deep_long_count = sum(1 for video in classified["long"] if video.get("watch_percent", 0) >= 80)
    deep_learning_bonus = min(50, deep_long_count * 10)

    return {
        "time_efficiency": round(time_efficiency, 1),
        "behavior_health": round(behavior_health, 1),
        "learning_volume_score": round(learning_volume_score, 1),
        "deep_learning_bonus": round(deep_learning_bonus, 1),
        "deep_long_count": deep_long_count,
    }



def calculate_statistics(history_list):
    """计算统计数据"""
    total_watch_time = sum(item.get("progress", 0) for item in history_list)
    total_duration = sum(item.get("duration", 0) for item in history_list)

    category_stats = {}
    for item in history_list:
        tname = item.get("tname", "未知")
        progress = item.get("progress", 0)
        if tname not in category_stats:
            category_stats[tname] = {"count": 0, "watch_time": 0}
        category_stats[tname]["count"] += 1
        category_stats[tname]["watch_time"] += progress

    author_stats = {}
    for item in history_list:
        author = item.get("author", "未知")
        mid = item.get("mid", "")
        progress = item.get("progress", 0)
        if author not in author_stats:
            author_stats[author] = {"count": 0, "watch_time": 0, "mid": mid}
        author_stats[author]["count"] += 1
        author_stats[author]["watch_time"] += progress

    hour_stats = defaultdict(int)
    for item in history_list:
        hour = datetime.fromtimestamp(item["view_at"]).hour
        hour_stats[hour] += 1

    deep_watch_count = sum(1 for item in history_list if item.get("watch_percent", 0) >= 80)
    shallow_watch_count = sum(1 for item in history_list if item.get("progress", 0) < 60)

    sorted_categories = sorted(category_stats.items(), key=lambda pair: pair[1]["watch_time"], reverse=True)
    sorted_authors = sorted(author_stats.items(), key=lambda pair: pair[1]["watch_time"], reverse=True)

    return {
        "total_videos": len(history_list),
        "total_watch_time": total_watch_time,
        "total_duration": total_duration,
        "categories": sorted_categories,
        "authors": sorted_authors,
        "hour_stats": dict(hour_stats),
        "deep_watch_count": deep_watch_count,
        "shallow_watch_count": shallow_watch_count,
    }
