from datetime import datetime

import browser_cookie3
import requests

from blisummary.config import BILIBILI_HEADERS, BILIBILI_PAGELIST_TIMEOUT, BILIBILI_TIMEOUT



def get_bilibili_cookies():
    """从浏览器自动获取 B站 Cookie，依次尝试 Chrome、Safari、Firefox"""
    for loader, name in [
        (browser_cookie3.chrome, "Chrome"),
        (browser_cookie3.safari, "Safari"),
        (browser_cookie3.firefox, "Firefox"),
    ]:
        try:
            jar = loader(domain_name=".bilibili.com")
            if any(cookie.name == "SESSDATA" for cookie in jar):
                print(f"   ✅ 已从 {name} 读取 B站 Cookie")
                return jar
        except Exception:
            continue
    raise RuntimeError("未能从浏览器获取 B站 Cookie，请确保已在浏览器中登录 B站")



def bilibili_get(url, headers=None, cookies=None, timeout=BILIBILI_TIMEOUT):
    """请求 B站接口；若系统代理导致证书校验异常，则绕过环境代理重试一次。"""
    request_headers = headers or BILIBILI_HEADERS
    try:
        return requests.get(url, headers=request_headers, cookies=cookies, timeout=timeout)
    except requests.exceptions.SSLError:
        print("   ⚠️ 检测到 SSL 校验异常，正在绕过系统代理重试...")
        with requests.Session() as session:
            session.trust_env = False
            return session.get(url, headers=request_headers, cookies=cookies, timeout=timeout)



def get_video_pagelist(bvid, cookies, headers=None, cache=None):
    """获取视频分P列表，按 bvid 缓存避免重复请求"""
    if cache is None:
        cache = {}
    if bvid in cache:
        return cache[bvid]

    try:
        url = f"https://api.bilibili.com/x/player/pagelist?bvid={bvid}"
        response = bilibili_get(url, headers=headers, cookies=cookies, timeout=BILIBILI_PAGELIST_TIMEOUT)
        data = response.json()
        result = data["data"] if data.get("code") == 0 else None
    except Exception:
        result = None

    cache[bvid] = result
    return result



def enrich_multipart_history(day_history, prev_video_positions, cookies):
    """修正分P视频数据，消除重复计算并补全今天新看的P。"""
    regular = []
    bvid_best = {}
    pagelist_cache = {}

    for item in day_history:
        page_info = item.get("page") or {}
        page_num = page_info.get("page") or 1
        bvid = item.get("bvid", "")

        if page_num <= 1 or not bvid:
            regular.append(item)
            continue

        existing = bvid_best.get(bvid)
        if existing is None:
            bvid_best[bvid] = item
            continue

        existing_page = (existing.get("page") or {}).get("page", 1) or 1
        if page_num > existing_page:
            bvid_best[bvid] = item

    enriched = []
    for bvid, item in bvid_best.items():
        page_info = item.get("page") or {}
        page_num = page_info.get("page") or 1
        page_duration = page_info.get("duration", 0)
        progress = item.get("progress", 0)

        if progress == -1:
            progress = page_duration

        effective_duration = page_duration if page_duration > 0 else item.get("duration", 0)
        effective_progress = progress
        prev_page = prev_video_positions.get(bvid)

        if prev_page is not None and page_num > prev_page + 1:
            pagelist = get_video_pagelist(bvid, cookies, headers=BILIBILI_HEADERS, cache=pagelist_cache)
            if pagelist and len(pagelist) >= page_num:
                for part in pagelist[prev_page: page_num - 1]:
                    effective_duration += part["duration"]
                    effective_progress += part["duration"]

        new_item = dict(item)
        new_item["duration"] = effective_duration
        new_item["progress"] = effective_progress
        new_item["watch_percent"] = (
            round(effective_progress / effective_duration * 100, 1)
            if effective_duration > 0 else 0
        )
        enriched.append(new_item)

    return regular + enriched



def get_bilibili_history(cookies, pages=None, max_pages=50, until_date=None):
    """获取B站浏览历史记录。指定 until_date 时，会持续拉取到覆盖该日期为止。"""
    all_history = []
    page = 1
    page_limit = pages if pages is not None else max_pages

    while page <= page_limit:
        url = f"https://api.bilibili.com/x/v2/history?pn={page}&ps=30"
        response = bilibili_get(url, headers=BILIBILI_HEADERS, cookies=cookies, timeout=BILIBILI_TIMEOUT)
        data = response.json()

        if data["code"] != 0:
            print(f"请求失败: {data['message']}")
            break

        items = data.get("data") or []
        if not items:
            break

        oldest_view_date = None

        for item in items:
            total_duration = item.get("duration", 0)
            progress = item.get("progress", 0)
            page_info = item.get("page") or {}
            page_duration = page_info.get("duration", 0)
            effective_duration = page_duration if page_duration > 0 else total_duration

            if progress == -1:
                progress = effective_duration

            title = item.get("title", "")
            page_num = page_info.get("page") or 1
            if page_num > 1:
                title = f"{title} P{page_num}"

            view_at = item.get("view_at", 0)
            oldest_view_date = datetime.fromtimestamp(view_at).date()

            all_history.append({
                "title": title,
                "author": item.get("owner", {}).get("name", ""),
                "mid": item.get("owner", {}).get("mid", ""),
                "desc": item.get("desc", ""),
                "view_at": view_at,
                "duration": effective_duration,
                "progress": progress,
                "watch_percent": round(progress / effective_duration * 100, 1) if effective_duration > 0 else 0,
                "bvid": item.get("bvid", ""),
                "tname": item.get("tname", ""),
                "page": page_info,
            })

        if len(items) < 30:
            break
        if until_date and oldest_view_date and oldest_view_date < until_date:
            break

        page += 1

    return all_history
