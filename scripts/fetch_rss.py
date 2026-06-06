"""这个文件负责抓取厂商博客 RSS/Atom，全部使用公开 feed。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.request import Request
from xml.etree import ElementTree

import config
from http_utils import open_url


def fetch_rss_items(days_back: int) -> list[dict[str, Any]]:
    """逐个抓取 RSS feed；单个 feed 失败只记录日志，不影响其他 feed。"""

    since_time = datetime.now(timezone.utc) - timedelta(days=days_back)
    all_items: list[dict[str, Any]] = []

    for feed_url in config.RSS_FEEDS:
        try:
            all_items.extend(fetch_one_feed(feed_url, since_time))
        except Exception as exc:  # noqa: BLE001 - 这里故意兜底，保证整体流程不中断。
            print(f"[warning] RSS feed failed: {feed_url} - {exc}")

    return all_items


def fetch_one_feed(feed_url: str, since_time: datetime) -> list[dict[str, Any]]:
    """抓取并解析单个 RSS 或 Atom feed。"""

    request = Request(feed_url, headers={"User-Agent": "ai-term-radar-mvp/1.0"})
    with open_url(request, timeout=30) as response:
        feed_text = response.read().decode("utf-8", errors="replace")

    root = ElementTree.fromstring(feed_text)

    if root.tag.endswith("rss"):
        return parse_rss_feed(root, feed_url, since_time)
    return parse_atom_feed(root, feed_url, since_time)


def parse_rss_feed(root: ElementTree.Element, feed_url: str, since_time: datetime) -> list[dict[str, Any]]:
    """解析传统 RSS 格式。"""

    items: list[dict[str, Any]] = []
    for item in root.findall("./channel/item"):
        title = get_child_text(item, "title")
        summary = get_child_text(item, "description")
        link = get_child_text(item, "link")
        published_text = get_child_text(item, "pubDate")
        published_at = parse_feed_datetime(published_text)

        if published_at and published_at < since_time:
            continue
        if not title:
            continue

        items.append(
            {
                "source": "rss",
                "title": title,
                "summary": summary,
                "url": link or feed_url,
                "published_at": (published_at or datetime.now(timezone.utc)).isoformat(),
            }
        )
    return items


def parse_atom_feed(root: ElementTree.Element, feed_url: str, since_time: datetime) -> list[dict[str, Any]]:
    """解析 Atom 格式。"""

    namespace = {"atom": "http://www.w3.org/2005/Atom"}
    entries = root.findall(".//atom:entry", namespace)
    items: list[dict[str, Any]] = []

    for entry in entries:
        title = get_child_text(entry, "atom:title", namespace)
        summary = get_child_text(entry, "atom:summary", namespace) or get_child_text(entry, "atom:content", namespace)
        link = get_atom_link(entry, namespace) or feed_url
        published_text = get_child_text(entry, "atom:published", namespace) or get_child_text(entry, "atom:updated", namespace)
        published_at = parse_feed_datetime(published_text)

        if published_at and published_at < since_time:
            continue
        if not title:
            continue

        items.append(
            {
                "source": "rss",
                "title": title,
                "summary": summary,
                "url": link,
                "published_at": (published_at or datetime.now(timezone.utc)).isoformat(),
            }
        )
    return items


def get_child_text(element: ElementTree.Element, child_name: str, namespace: dict[str, str] | None = None) -> str:
    """安全读取 XML 子节点文本。"""

    child = element.find(child_name, namespace or {})
    if child is None or child.text is None:
        return ""
    return " ".join(child.text.split())


def get_atom_link(element: ElementTree.Element, namespace: dict[str, str]) -> str:
    """Atom 的链接通常放在 link 标签的 href 属性里。"""

    for link in element.findall("atom:link", namespace):
        href = link.attrib.get("href", "")
        if href:
            return href
    return ""


def parse_feed_datetime(value: str) -> datetime | None:
    """兼容 RSS 的邮件格式时间和 Atom 的 ISO 时间。"""

    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        pass
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None
