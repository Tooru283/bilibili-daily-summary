import os
from datetime import date

SUMMARY_FOLDER = "/Users/moca/Documents/笔记/研究生/04_Bilibili"
WEEKLY_FOLDER = os.path.join(SUMMARY_FOLDER, "周总结")

BILIBILI_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.bilibili.com",
}
BILIBILI_TIMEOUT = 10
BILIBILI_PAGELIST_TIMEOUT = 5



def summary_markdown_path(target_date: date) -> str:
    return os.path.join(SUMMARY_FOLDER, f"{target_date:%Y-%m-%d}-B站总结.md")



def stats_json_path(target_date: date) -> str:
    return os.path.join(SUMMARY_FOLDER, f".stats_{target_date:%Y-%m-%d}.json")



def weekly_archive_folder(week_number: int, monday: date, sunday: date) -> str:
    week_str = f"{monday.month}.{monday.day}-{sunday.month}.{sunday.day}"
    folder_name = f"W{week_number}({monday.year}.{week_str})"
    return os.path.join(WEEKLY_FOLDER, folder_name)



def weekly_summary_path(base_folder: str, week_number: int, monday: date) -> str:
    filename = f"{monday.year}-W{week_number:02d}-周总结.md"
    return os.path.join(base_folder, filename)



def _default_claude_cli() -> str:
    configured = os.environ.get("CLAUDE_CLI")
    if configured:
        return configured

    local_cli = os.path.expanduser("~/.local/bin/claude")
    if os.path.exists(local_cli):
        return local_cli

    return "claude"


CLAUDE_CLI = _default_claude_cli()
