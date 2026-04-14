from datetime import date
from typing import Any, NotRequired, TypedDict

HistoryItem = dict[str, Any]


class VideoBucketStats(TypedDict):
    count: int
    quality_count: int
    total_time: int


class ShortVideoStats(TypedDict):
    count: int
    quality_count: int
    fragment_count: int
    total_time: int


class VideoStats(TypedDict):
    long_video: VideoBucketStats
    medium_video: VideoBucketStats
    short_video: ShortVideoStats


class BehaviorMetrics(TypedDict):
    avg_completion: float
    peak_hour: str
    quality_time_ratio: float


class StoredDayStats(TypedDict):
    total_videos: int
    total_watch_time: int
    deep_watch_count: int
    avg_completion: float
    quality_time_ratio: float
    fragment_count: int
    score: int
    video_positions: NotRequired[dict[str, int]]


class LoadedDayStats(StoredDayStats):
    date: date


class SummaryResult(TypedDict):
    stats: dict[str, Any]
    video_stats: VideoStats
    behavior_metrics: BehaviorMetrics
    score: int
