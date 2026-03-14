import subprocess
import requests
import os
import json
from datetime import datetime, timedelta
from collections import defaultdict
import browser_cookie3

# 保存路径
SUMMARY_FOLDER = "/Users/moca/Documents/笔记/研究生/Blisummary"

# 获取脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def get_bilibili_cookies():
    """从浏览器自动获取 B站 Cookie，依次尝试 Chrome、Safari、Firefox"""
    for loader, name in [
        (browser_cookie3.chrome, "Chrome"),
        (browser_cookie3.safari, "Safari"),
        (browser_cookie3.firefox, "Firefox"),
    ]:
        try:
            jar = loader(domain_name=".bilibili.com")
            # 检查是否包含必要的 SESSDATA
            if any(c.name == "SESSDATA" for c in jar):
                print(f"   ✅ 已从 {name} 读取 B站 Cookie")
                return jar
        except Exception:
            continue
    raise RuntimeError("未能从浏览器获取 B站 Cookie，请确保已在浏览器中登录 B站")

def get_bilibili_history(cookies, pages=5):
    """获取B站浏览历史记录"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.bilibili.com'
    }

    all_history = []
    for page in range(1, pages + 1):
        url = f'https://api.bilibili.com/x/v2/history?pn={page}&ps=30'
        response = requests.get(url, headers=headers, cookies=cookies)
        data = response.json()

        if data['code'] != 0:
            print(f"请求失败: {data['message']}")
            break

        for item in data['data']:
            duration = item.get('duration', 0)
            progress = item.get('progress', 0)
            
            if progress == -1:
                progress = duration
            
            all_history.append({
                'title': item.get('title', ''),
                'author': item.get('owner', {}).get('name', ''),
                'mid': item.get('owner', {}).get('mid', ''),
                'desc': item.get('desc', ''),
                'view_at': item.get('view_at', 0),
                'duration': duration,
                'progress': progress,
                'watch_percent': round(progress / duration * 100, 1) if duration > 0 else 0,
                'bvid': item.get('bvid', ''),
                'tname': item.get('tname', ''),
            })

    return all_history


def filter_history_by_date(history_list, target_date):
    """筛选指定日期的浏览记录"""
    filtered = []
    for item in history_list:
        view_time = datetime.fromtimestamp(item['view_at']).date()
        if view_time == target_date:
            filtered.append(item)
    return filtered


def filter_today_history(history_list):
    """筛选出今天的浏览记录"""
    return filter_history_by_date(history_list, datetime.now().date())


def filter_yesterday_history(history_list):
    """筛选出昨天的浏览记录"""
    yesterday = (datetime.now() - timedelta(days=1)).date()
    return filter_history_by_date(history_list, yesterday)


def format_duration(seconds):
    """格式化时长为 mm:ss 或 hh:mm:ss"""
    if seconds < 3600:
        return f"{seconds // 60}:{seconds % 60:02d}"
    else:
        return f"{seconds // 3600}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"


def classify_videos(history_list):
    """按时长分类视频"""
    long_videos = []
    medium_videos = []
    short_videos = []
    fragment_videos = []
    
    for item in history_list:
        duration = item.get('duration', 0)
        if duration >= 600:
            long_videos.append(item)
        elif duration >= 180:
            medium_videos.append(item)
        else:
            short_videos.append(item)
            if item.get('progress', 0) < 60:
                fragment_videos.append(item)
    
    return {
        'long': long_videos,
        'medium': medium_videos,
        'short': short_videos,
        'fragment': fragment_videos,
    }


def calculate_video_stats(classified):
    """计算分类视频统计"""
    long_videos = classified['long']
    medium_videos = classified['medium']
    short_videos = classified['short']
    fragment_videos = classified['fragment']
    
    long_quality = [v for v in long_videos if v.get('watch_percent', 0) >= 50]
    medium_quality = [v for v in medium_videos if v.get('watch_percent', 0) >= 70]
    short_quality = [v for v in short_videos if v.get('watch_percent', 0) >= 90]
    
    return {
        'long_video': {
            'count': len(long_videos),
            'quality_count': len(long_quality),
            'total_time': sum(v.get('progress', 0) for v in long_videos),
        },
        'medium_video': {
            'count': len(medium_videos),
            'quality_count': len(medium_quality),
            'total_time': sum(v.get('progress', 0) for v in medium_videos),
        },
        'short_video': {
            'count': len(short_videos),
            'quality_count': len(short_quality),
            'fragment_count': len(fragment_videos),
            'total_time': sum(v.get('progress', 0) for v in short_videos),
        },
    }


def calculate_quality_scores(classified, stats):
    """计算质量评分（1-5星）"""
    long_videos = classified['long']
    short_videos = classified['short']
    
    if long_videos:
        avg_completion = sum(v.get('watch_percent', 0) for v in long_videos) / len(long_videos)
        knowledge_gain = min(5, max(1, int(avg_completion / 20)))
        thinking_depth = min(5, max(1, stats['long_video']['quality_count']))
        production_quality = min(5, max(1, int(avg_completion / 15)))
    else:
        knowledge_gain = thinking_depth = production_quality = 0
    
    if short_videos:
        quality_ratio = stats['short_video']['quality_count'] / len(short_videos) if short_videos else 0
        fragment_ratio = stats['short_video']['fragment_count'] / len(short_videos) if short_videos else 0
        info_density = min(5, max(0, int(quality_ratio * 5)))
        practical_value = min(5, max(0, int((1 - fragment_ratio) * 3)))
        emotional_value = min(5, max(1, int(quality_ratio * 3) + 1))
    else:
        info_density = practical_value = emotional_value = 0
    
    return {
        'long_video': {
            'knowledge_gain': knowledge_gain,
            'thinking_depth': thinking_depth,
            'production_quality': production_quality,
        },
        'short_video': {
            'info_density': info_density,
            'practical_value': practical_value,
            'emotional_value': emotional_value,
        },
    }


def calculate_behavior_metrics(history_list, stats):
    """计算行为指标"""
    total_watch_time = sum(v.get('progress', 0) for v in history_list)
    total_duration = sum(v.get('duration', 0) for v in history_list)
    
    avg_completion = round(total_watch_time / total_duration * 100, 1) if total_duration > 0 else 0
    
    hour_stats = defaultdict(int)
    for item in history_list:
        hour = datetime.fromtimestamp(item["view_at"]).hour
        hour_stats[hour] += 1
    
    peak_hour = max(hour_stats.items(), key=lambda x: x[1])[0] if hour_stats else 0
    
    quality_time = stats['long_video']['total_time'] + stats['medium_video']['total_time']
    quality_time_ratio = round(quality_time / total_watch_time, 2) if total_watch_time > 0 else 0
    
    return {
        'avg_completion': avg_completion,
        'peak_hour': f"{peak_hour:02d}:00",
        'quality_time_ratio': quality_time_ratio,
    }


def calculate_content_quality_score(video_stats, quality_scores):
    """计算内容质量总分"""
    long_base = min(100, video_stats['long_video']['quality_count'] * 20)
    long_quality_avg = (
        quality_scores['long_video']['knowledge_gain'] +
        quality_scores['long_video']['thinking_depth'] +
        quality_scores['long_video']['production_quality']
    ) / 15
    long_score = long_base * long_quality_avg
    
    medium_score = min(100, video_stats['medium_video']['quality_count'] * 30)
    
    short_base = min(100, video_stats['short_video']['quality_count'] * 40)
    short_quality_avg = (
        quality_scores['short_video']['info_density'] +
        quality_scores['short_video']['practical_value'] +
        quality_scores['short_video']['emotional_value']
    ) / 15
    short_score = short_base * short_quality_avg
    
    fragment_penalty = max(0, 100 - (video_stats['short_video']['fragment_count'] - 10) * 5)
    
    total = (long_score * 0.4) + (medium_score * 0.3) + (short_score * 0.2) + (fragment_penalty * 0.1)
    
    return {
        'long_score': round(long_score, 1),
        'medium_score': round(medium_score, 1),
        'short_score': round(short_score, 1),
        'fragment_penalty': round(fragment_penalty, 1),
        'total': round(total, 1),
    }


def calculate_advanced_score(video_stats, behavior_metrics, classified):
    """计算高级评分"""
    time_efficiency = min(100, behavior_metrics['quality_time_ratio'] * 200)
    behavior_health = max(0, 100 - video_stats['short_video']['fragment_count'] * 1.5)

    # 学习总量得分：质量内容总时长（长+中视频），每30分钟+20分，上限100
    quality_total_minutes = (
        video_stats['long_video']['total_time'] +
        video_stats['medium_video']['total_time']
    ) / 60
    learning_volume_score = min(100, quality_total_minutes / 30 * 20)

    # 深度学习奖励：长视频完成度≥80%，每个+10分，上限50（归一化到100）
    deep_long_count = sum(1 for v in classified['long'] if v.get('watch_percent', 0) >= 80)
    deep_learning_bonus = min(50, deep_long_count * 10)

    return {
        'time_efficiency': round(time_efficiency, 1),
        'behavior_health': round(behavior_health, 1),
        'learning_volume_score': round(learning_volume_score, 1),
        'deep_learning_bonus': round(deep_learning_bonus, 1),
        'deep_long_count': deep_long_count,
    }


def format_history_top10(history_list):
    """格式化TOP10历史记录"""
    sorted_list = sorted(history_list, key=lambda x: x.get("progress", 0), reverse=True)[:10]
    
    lines = []
    for i, item in enumerate(sorted_list, 1):
        view_time = datetime.fromtimestamp(item["view_at"]).strftime("%H:%M")
        title = item.get("title", "")
        author = item.get("author", "")
        tname = item.get("tname", "")
        progress = format_duration(item.get("progress", 0))
        duration = format_duration(item.get("duration", 0))
        watch_percent = item.get("watch_percent", 0)
        bvid = item.get("bvid", "")
        
        lines.append(
            f"{i}. [{title}](https://www.bilibili.com/video/{bvid})\n"
            f"   - UP: {author} | 分区: {tname}\n"
            f"   - 观看: {progress}/{duration} ({watch_percent}%) | 时间: {view_time}"
        )
    return "\n".join(lines)


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
    
    sorted_categories = sorted(category_stats.items(), key=lambda x: x[1]["watch_time"], reverse=True)
    sorted_authors = sorted(author_stats.items(), key=lambda x: x[1]["watch_time"], reverse=True)
    
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


def generate_time_heatmap(hour_stats):
    """生成时间分布热力图"""
    lines = ["### 🕐 时间分布热力图", ""]
    
    if not hour_stats:
        return "### 🕐 时间分布热力图\n\n暂无数据"
    
    active_hours = sorted([h for h in hour_stats.keys() if hour_stats[h] > 0])
    
    if not active_hours:
        return "### 🕐 时间分布热力图\n\n暂无数据"
    
    header = "| 时段 | " + " | ".join([f"{h:02d}:00" for h in active_hours]) + " |"
    separator = "|------| " + " | ".join(["------" for _ in active_hours]) + " |"
    counts = "| 视频数 | " + " | ".join([str(hour_stats.get(h, 0)) for h in active_hours]) + " |"
    
    def get_density(count):
        if count == 0:
            return "⚪"
        elif count <= 3:
            return "🟡" * min(count, 3)
        elif count <= 7:
            return "🟠" * 3
        else:
            return "🔴" * 3
    
    density = "| 密度 | " + " | ".join([get_density(hour_stats.get(h, 0)) for h in active_hours]) + " |"
    
    lines.extend([header, separator, counts, density])
    lines.append("")
    lines.append("**时段分析：**")
    
    peak_hour = max(hour_stats.items(), key=lambda x: x[1])
    lines.append(f"- 📈 高峰时段：{peak_hour[0]:02d}:00（{peak_hour[1]}个视频）")
    
    morning = sum(hour_stats.get(h, 0) for h in range(6, 12))
    afternoon = sum(hour_stats.get(h, 0) for h in range(12, 18))
    evening = sum(hour_stats.get(h, 0) for h in range(18, 24))
    night = sum(hour_stats.get(h, 0) for h in range(0, 6))
    
    total = morning + afternoon + evening + night
    if total > 0:
        if morning > 0:
            lines.append(f"- 🌅 上午(6-12点)：{morning}个（{round(morning/total*100)}%）")
        if afternoon > 0:
            lines.append(f"- ☀️ 下午(12-18点)：{afternoon}个（{round(afternoon/total*100)}%）")
        if evening > 0:
            lines.append(f"- 🌙 晚上(18-24点)：{evening}个（{round(evening/total*100)}%）")
        if night > 0:
            lines.append(f"- 🌃 深夜(0-6点)：{night}个（{round(night/total*100)}%）")
    
    return "\n".join(lines)


def generate_video_classification_stats(video_stats, quality_scores):
    """生成视频分类统计"""
    lines = ["## 📦 视频分类统计", ""]
    
    lines.append("### 按时长分类")
    lines.append("")
    lines.append("| 类型 | 数量 | 高质量数 | 观看时长 | 质量占比 |")
    lines.append("|------|------|----------|----------|----------|")
    
    long = video_stats['long_video']
    medium = video_stats['medium_video']
    short = video_stats['short_video']
    
    long_ratio = round(long['quality_count'] / long['count'] * 100) if long['count'] > 0 else 0
    medium_ratio = round(medium['quality_count'] / medium['count'] * 100) if medium['count'] > 0 else 0
    short_ratio = round(short['quality_count'] / short['count'] * 100) if short['count'] > 0 else 0
    
    lines.append(f"| 长视频(>10min) | {long['count']} | {long['quality_count']} | {format_duration(long['total_time'])} | {long_ratio}% |")
    lines.append(f"| 中视频(3-10min) | {medium['count']} | {medium['quality_count']} | {format_duration(medium['total_time'])} | {medium_ratio}% |")
    lines.append(f"| 短视频(<3min) | {short['count']} | {short['quality_count']} | {format_duration(short['total_time'])} | {short_ratio}% |")
    lines.append(f"| └─ 碎片(<1min) | {short['fragment_count']} | - | - | - |")
    
    lines.append("")
    lines.append("### 质量评分（1-5星）")
    lines.append("")
    
    def stars(n):
        return "★" * n + "☆" * (5 - n)
    
    lines.append("**长视频质量**")
    lines.append(f"- 知识增量：{stars(quality_scores['long_video']['knowledge_gain'])}")
    lines.append(f"- 思考深度：{stars(quality_scores['long_video']['thinking_depth'])}")
    lines.append(f"- 制作质量：{stars(quality_scores['long_video']['production_quality'])}")
    lines.append("")
    lines.append("**短视频质量**")
    lines.append(f"- 信息密度：{stars(quality_scores['short_video']['info_density'])}")
    lines.append(f"- 实用价值：{stars(quality_scores['short_video']['practical_value'])}")
    lines.append(f"- 情绪价值：{stars(quality_scores['short_video']['emotional_value'])}")
    lines.append("")
    
    return "\n".join(lines)


def generate_quality_rating(history_list, classified):
    """生成内容质量评分"""
    lines = ["## ⭐ 今日精华内容", ""]
    
    long_videos = sorted(classified['long'], key=lambda x: x.get('watch_percent', 0), reverse=True)[:3]
    short_quality = [v for v in classified['short'] if v.get('watch_percent', 0) >= 80]
    short_quality = sorted(short_quality, key=lambda x: x.get('progress', 0), reverse=True)[:2]
    worst = [v for v in history_list if v.get('progress', 0) < 30]
    worst = sorted(worst, key=lambda x: x.get('progress', 0))[:3]
    
    if long_videos:
        lines.append("### 🏆 最佳长视频")
        lines.append("")
        for item in long_videos:
            stars_count = min(5, int(item['watch_percent'] / 20))
            stars_str = "★" * stars_count + "☆" * (5 - stars_count)
            bvid = item.get("bvid", "")
            duration_str = format_duration(item["duration"])
            lines.append(f"- **[{item['title']}](https://www.bilibili.com/video/{bvid})** - {stars_str}")
            lines.append(f"  - UP: {item['author']} | 完成度: {item['watch_percent']}% | 时长: {duration_str}")
            lines.append(f"  - 💬 为什么值得：_记录你的感受_")
            lines.append(f"  - 🎯 适合人群：_填写推荐理由_")
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
    
    video_goal = 60
    time_goal = 3 * 3600
    deep_goal = 6
    
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
    lines.append(f"| 深度学习 | {advanced_score['deep_learning_bonus']*2} | 10% | 长视频≥80%完成（{advanced_score['deep_long_count']}个）|")

    total_score = round(
        advanced_score['time_efficiency'] * 0.2 +
        advanced_score['behavior_health'] * 0.2 +
        content_score['total'] * 0.3 +
        advanced_score['learning_volume_score'] * 0.2 +
        advanced_score['deep_learning_bonus'] * 2 * 0.1
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
    avg_percent = round(stats['total_watch_time'] / stats['total_duration'] * 100, 1) if stats['total_duration'] > 0 else 0
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
    
    if stats["total_watch_time"] > 2 * 3600:
        tags.append("长时间浏览")
    
    if behavior_metrics['avg_completion'] < 15:
        tags.append("碎片化警告")
    
    if stats["categories"]:
        top_category = stats["categories"][0][0]
        weight = stats["categories"][0][1]["watch_time"] / stats["total_watch_time"] * 100 if stats["total_watch_time"] > 0 else 0
        if weight > 30:
            tags.append(f"{top_category}偏好")
    
    if stats["deep_watch_count"] >= 3:
        tags.append("深度观看达标")
    
    if behavior_metrics['quality_time_ratio'] > 0.5:
        tags.append("高质量观看")
    
    return tags


def generate_content_types(stats):
    """生成内容类型标签"""
    types = []
    for category, data in stats["categories"][:5]:
        if data["watch_time"] > 300:
            types.append(category)
    return types


def generate_reflection_template(stats, video_stats, classified):
    """生成反思模板"""
    lines = ["## 📝 反思日记", ""]
    
    deep_long = [v for v in classified['long'] if v.get('watch_percent', 0) >= 50]
    fragment_count = video_stats['short_video']['fragment_count']
    
    lines.append("### 今日做得好的地方")
    if deep_long:
        for item in deep_long[:2]:
            lines.append(f"- 深度观看《{item['title']}》（{item['watch_percent']}%）")
    else:
        lines.append("- _（记录今天的亮点）_")
    lines.append("")
    
    lines.append("### 需要改进的地方")
    if fragment_count > 10:
        lines.append(f"- 碎片化浏览严重（{fragment_count}个视频<1分钟）")
    if stats["total_watch_time"] > 3 * 3600:
        lines.append(f"- 总时长过长（{format_duration(stats['total_watch_time'])}）")
    lines.append("- _（分析不足之处）_")
    lines.append("")
    
    lines.append("### 明天行动计划")
    lines.append("1. 设定：最多点开30个视频")
    lines.append("2. 策略：长视频先看简介和弹幕，决定是否值得投入")
    lines.append("3. 时间管理：_（填写具体计划）_")
    lines.append("")
    
    return "\n".join(lines)


def load_stats_by_date(target_date):
    """加载指定日期的统计数据"""
    os.makedirs(SUMMARY_FOLDER, exist_ok=True)
    date_str = target_date.strftime("%Y-%m-%d")
    stats_file = os.path.join(SUMMARY_FOLDER, f".stats_{date_str}.json")
    
    if os.path.exists(stats_file):
        with open(stats_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def load_yesterday_stats():
    """加载昨日统计数据"""
    yesterday = (datetime.now() - timedelta(days=1)).date()
    return load_stats_by_date(yesterday)


def save_stats_by_date(target_date, stats, video_stats, behavior_metrics, score):
    """保存指定日期的统计数据"""
    os.makedirs(SUMMARY_FOLDER, exist_ok=True)
    date_str = target_date.strftime("%Y-%m-%d")
    stats_file = os.path.join(SUMMARY_FOLDER, f".stats_{date_str}.json")
    
    save_data = {
        "total_videos": stats["total_videos"],
        "total_watch_time": stats["total_watch_time"],
        "deep_watch_count": stats["deep_watch_count"],
        "avg_completion": behavior_metrics["avg_completion"],
        "quality_time_ratio": behavior_metrics["quality_time_ratio"],
        "fragment_count": video_stats["short_video"]["fragment_count"],
        "score": score,
    }
    
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(save_data, f)


def save_today_stats(stats, video_stats, behavior_metrics, score):
    """保存今日统计数据"""
    save_stats_by_date(datetime.now().date(), stats, video_stats, behavior_metrics, score)


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
    
    # 观看时长
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
    
    # 视频数量
    diff = stats["total_videos"] - yesterday_stats.get("total_videos", 0)
    diff_str = f"+{diff}" if diff > 0 else str(diff)
    emoji = "📈" if diff > 0 else ("📉" if diff < 0 else "➡️")
    lines.append(f"| 视频数量 | {stats['total_videos']} | {yesterday_stats.get('total_videos', 0)} | {diff_str} | {emoji} |")
    
    # 平均完成度
    diff = round(behavior_metrics['avg_completion'] - yesterday_stats.get('avg_completion', 0), 1)
    diff_str = f"+{diff}%" if diff > 0 else f"{diff}%"
    emoji = "📈" if diff > 0 else ("📉" if diff < 0 else "➡️")
    lines.append(f"| 平均完成度 | {behavior_metrics['avg_completion']}% | {yesterday_stats.get('avg_completion', 0)}% | {diff_str} | {emoji} |")
    
    # 深度观看
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


def generate_summary_with_claude(stats_text, classification_text, quality_text):
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
    
    result = subprocess.run(
        ["/opt/homebrew/bin/claude", "-p", prompt],
        capture_output=True,
        text=True
    )
    return result.stdout


def get_yesterday_summary_file_path():
    """获取昨天总结文件路径"""
    yesterday = (datetime.now() - timedelta(days=1)).date()
    yesterday_str = yesterday.strftime("%Y-%m-%d")
    filename = f"{yesterday_str}-B站总结.md"
    return os.path.join(SUMMARY_FOLDER, filename)


def should_regenerate_yesterday_summary():
    """判断是否需要重新生成昨天的总结
    
    条件：昨天的总结不存在，或者不是在昨天23:30之后/今天生成的
    """
    file_path = get_yesterday_summary_file_path()
    
    # 文件不存在，需要生成
    if not os.path.exists(file_path):
        return True
    
    # 获取文件修改时间
    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
    
    # 昨天 23:30
    yesterday = (datetime.now() - timedelta(days=1)).date()
    cutoff_time = datetime.combine(yesterday, datetime.strptime("23:30", "%H:%M").time())
    
    # 如果文件修改时间早于昨天23:30，需要重新生成
    if file_mtime < cutoff_time:
        return True
    
    return False


def generate_summary_for_date(history_list, target_date, prev_day_stats=None):
    """为指定日期生成总结"""
    date_str = target_date.strftime("%Y-%m-%d")
    week_number = target_date.isocalendar()[1]
    
    # 筛选指定日期的记录
    day_history = filter_history_by_date(history_list, target_date)
    
    if not day_history:
        print(f"📅 {date_str} 没有观看记录")
        return None
    
    print(f"📅 正在生成 {date_str} 的总结（{len(day_history)}条记录）...")
    
    # 计算统计数据
    stats = calculate_statistics(day_history)
    classified = classify_videos(day_history)
    video_stats = calculate_video_stats(classified)
    quality_scores = calculate_quality_scores(classified, video_stats)
    behavior_metrics = calculate_behavior_metrics(day_history, video_stats)
    content_score = calculate_content_quality_score(video_stats, quality_scores)
    advanced_score = calculate_advanced_score(video_stats, behavior_metrics, classified)
    
    # 生成各部分内容
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
    
    # 保存统计数据
    save_stats_by_date(target_date, stats, video_stats, behavior_metrics, total_score)
    
    # 生成标签
    tags = generate_tags(stats, video_stats, behavior_metrics)
    content_types = generate_content_types(stats)
    
    # 生成 AI 总结
    print(f"   🤖 生成 AI 总结...")
    summary = generate_summary_with_claude(stats_text, classification_text, quality_text)
    
    # 生成完整内容
    hours = round(stats['total_watch_time'] / 3600, 1)
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
    
    # 保存文件
    os.makedirs(SUMMARY_FOLDER, exist_ok=True)
    filename = f"{date_str}-B站总结.md"
    file_path = os.path.join(SUMMARY_FOLDER, filename)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"   ✅ 已保存到: {file_path}")
    
    return {
        "stats": stats,
        "video_stats": video_stats,
        "behavior_metrics": behavior_metrics,
        "score": total_score,
    }


def main():
    """主函数"""
    # 自动从浏览器读取 Cookie
    cookies = get_bilibili_cookies()

    # 获取历史记录（多获取几页以确保包含昨天的数据）
    print("📥 获取B站历史记录...")
    history = get_bilibili_history(cookies, pages=8)
    
    if not history:
        print("❌ 获取历史记录失败")
        return
    
    print(f"   获取到 {len(history)} 条记录")
    
    # 检查是否需要重新生成昨天的总结
    print("\n🔄 检查昨日总结...")
    if should_regenerate_yesterday_summary():
        yesterday = (datetime.now() - timedelta(days=1)).date()
        
        # 加载前天的统计数据用于对比
        day_before_yesterday = yesterday - timedelta(days=1)
        prev_stats = load_stats_by_date(day_before_yesterday)
        
        print("   ⚠️ 昨日总结需要重新生成...")
        generate_summary_for_date(history, yesterday, prev_stats)
    else:
        print("   ✅ 昨日总结已是最新，跳过")
    
    # 生成今天的总结
    print("\n📊 生成今日总结...")
    today = datetime.now().date()
    yesterday_stats = load_yesterday_stats()
    
    result = generate_summary_for_date(history, today, yesterday_stats)
    
    if result:
        print(f"\n🎉 完成！今日得分：{result['score']}/100")
    else:
        print("\n📭 今天没有观看记录")


if __name__ == "__main__":
    main()
