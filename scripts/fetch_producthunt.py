"""这个文件负责从 Product Hunt V2 GraphQL API 抓取最近发布的产品。"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.request import Request

import config
from http_utils import open_url


PRODUCTHUNT_API_URL = "https://api.producthunt.com/v2/api/graphql"


def fetch_producthunt_items(days_back: int) -> list[dict[str, Any]]:
    """抓取 Product Hunt 最近产品；没有 token 时直接跳过，保证主流程不中断。"""

    if not config.PRODUCTHUNT_TOKEN:
        print("[warning] PRODUCTHUNT_TOKEN is empty, skip Product Hunt.")
        return []

    query = """
    query RecentPosts {
      posts(first: 80, order: NEWEST) {
        edges {
          node {
            id
            name
            tagline
            url
            createdAt
          }
        }
      }
    }
    """

    request = Request(
        PRODUCTHUNT_API_URL,
        data=json.dumps({"query": query}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {config.PRODUCTHUNT_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "ai-term-radar-mvp/1.0",
        },
        method="POST",
    )

    with open_url(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))

    if payload.get("errors"):
        raise RuntimeError(f"Product Hunt API error: {payload['errors']}")

    since_time = datetime.now(timezone.utc) - timedelta(days=days_back)
    items: list[dict[str, Any]] = []

    for edge in payload.get("data", {}).get("posts", {}).get("edges", []):
        node = edge.get("node", {})
        created_at = parse_datetime(node.get("createdAt", ""))
        if created_at and created_at < since_time:
            continue

        name = (node.get("name") or "").strip()
        tagline = (node.get("tagline") or "").strip()
        if not name and not tagline:
            continue

        items.append(
            {
                "source": "producthunt",
                "title": name,
                "summary": tagline,
                "url": node.get("url", ""),
                "published_at": node.get("createdAt", ""),
            }
        )

    return items


def parse_datetime(value: str) -> datetime | None:
    """解析 Product Hunt 返回的 ISO 时间。"""

    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
