"""这个文件负责从 Hacker News Algolia 官方公开 API 抓取 AI 相关帖子。"""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from html import unescape
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request

from http_utils import open_url


HACKERNEWS_API_URL = "https://hn.algolia.com/api/v1/search_by_date"


def fetch_hackernews_items(days_back: int) -> list[dict[str, Any]]:
    """抓取指定天数内的 HN 帖子，失败时抛出异常交给上层记录日志。"""

    since_timestamp = int((datetime.now(timezone.utc) - timedelta(days=days_back)).timestamp())
    all_items: list[dict[str, Any]] = []

    # 多抓几页，避免只拿到当天少量结果。HN Algolia 免费公开接口不需要 key。
    for page_number in range(3):
        query_params = {
            "query": "AI",
            "tags": "story",
            "hitsPerPage": "100",
            "page": str(page_number),
            "numericFilters": f"created_at_i>{since_timestamp}",
        }
        request_url = f"{HACKERNEWS_API_URL}?{urlencode(query_params)}"
        request = Request(request_url, headers={"User-Agent": "ai-term-radar-mvp/1.0"})

        with open_url(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))

        for hit in payload.get("hits", []):
            title = clean_text(hit.get("title", ""))
            summary = clean_text(hit.get("story_text", "") or hit.get("comment_text", ""))
            url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"

            if not title:
                continue

            all_items.append(
                {
                    "source": "hackernews",
                    "title": title,
                    "summary": summary,
                    "url": url,
                    "published_at": hit.get("created_at", ""),
                }
            )

        # 给公开 API 一点间隔，避免短时间连续请求。
        time.sleep(1)

    return all_items


def clean_text(value: str) -> str:
    """把 HTML 转义和多余空白清掉，后续抽词更稳定。"""

    return " ".join(unescape(value or "").split())
