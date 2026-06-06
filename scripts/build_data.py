"""这个文件串起每日任务：抓取、抽词、验证、打分，并生成 data 目录里的 JSON。"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import config
from extract_terms import build_candidate_stats, slugify_term
from fetch_hackernews import fetch_hackernews_items
from fetch_producthunt import fetch_producthunt_items
from fetch_rss import fetch_rss_items
from score import (
    build_trend_note,
    calculate_opportunity_score,
    calculate_search_gap_score,
    calculate_source_diversity_score,
    calculate_velocity_score,
)
from verify_trends import TrendsVerifier


def main() -> None:
    """每日运行入口。"""

    ensure_data_files_exist()
    now = datetime.now(timezone.utc)
    days_back = config.RECENT_WINDOW_DAYS + config.HISTORY_WINDOW_DAYS

    source_items = fetch_all_sources(days_back)
    print(f"[info] fetched {len(source_items)} raw items")

    candidate_terms = build_candidate_stats(source_items, now=now)
    print(f"[info] found {len(candidate_terms)} candidate terms")

    scored_terms = build_scored_terms(candidate_terms, now)
    latest_payload = {
        "updated_at": now.isoformat(),
        "terms": scored_terms[: config.MAX_TERMS_IN_LATEST],
    }

    write_json(config.TERMS_DIR / "latest.json", latest_payload)
    write_json(config.HISTORY_DIR / f"{now.date().isoformat()}.json", latest_payload)

    for term in scored_terms:
        write_json(config.TERMS_DIR / f"{term['slug']}.json", term)

    print(f"[info] wrote {len(scored_terms)} term files")


def fetch_all_sources(days_back: int) -> list[dict[str, Any]]:
    """按配置抓取所有数据源；任一数据源失败不影响其他数据源。"""

    source_items: list[dict[str, Any]] = []

    if config.ENABLE_HACKERNEWS:
        source_items.extend(safe_fetch("Hacker News", fetch_hackernews_items, days_back))

    if config.ENABLE_PRODUCTHUNT:
        source_items.extend(safe_fetch("Product Hunt", fetch_producthunt_items, days_back))

    if config.ENABLE_RSS:
        source_items.extend(safe_fetch("RSS", fetch_rss_items, days_back))

    return source_items


def safe_fetch(source_name: str, fetch_function: Callable[[int], list[dict[str, Any]]], days_back: int) -> list[dict[str, Any]]:
    """数据源容错：失败只记录日志，不中断主流程。"""

    try:
        items = fetch_function(days_back)
        print(f"[info] {source_name}: {len(items)} items")
        return items
    except Exception as exc:  # noqa: BLE001 - 这里必须兜底，符合任一数据源失败不中断的要求。
        print(f"[warning] {source_name} failed: {exc}")
        return []


def build_scored_terms(candidate_terms: list[dict[str, Any]], now: datetime) -> list[dict[str, Any]]:
    """给候选词补齐 slug、分数、趋势说明和首次发现时间。"""

    verifier = TrendsVerifier()
    existing_terms = load_existing_terms()
    scored_terms: list[dict[str, Any]] = []

    for candidate in candidate_terms[: config.MAX_TERMS_TO_SCORE]:
        slug = slugify_term(candidate["term"])
        existing_term = existing_terms.get(slug, {})
        trends_interest = verifier.get_search_interest(candidate["term"])

        velocity_score = calculate_velocity_score(
            candidate["mention_count_recent"],
            candidate["mention_count_history"],
        )
        search_gap_score = calculate_search_gap_score(trends_interest)
        source_diversity_score = calculate_source_diversity_score(len(candidate["sources"]))
        opportunity_score = calculate_opportunity_score(
            velocity_score,
            search_gap_score,
            source_diversity_score,
        )

        scored_terms.append(
            {
                "term": candidate["term"],
                "slug": slug,
                "first_seen": existing_term.get("first_seen", now.date().isoformat()),
                "sources": candidate["sources"],
                "mention_count_recent": candidate["mention_count_recent"],
                "mention_count_history": candidate["mention_count_history"],
                "velocity_score": velocity_score,
                "search_gap_score": search_gap_score,
                "source_diversity_score": source_diversity_score,
                "opportunity_score": opportunity_score,
                "trend_note": build_trend_note(
                    candidate["mention_count_recent"],
                    candidate["mention_count_history"],
                    trends_interest,
                ),
                "example_links": candidate["example_links"],
            }
        )

    scored_terms.sort(key=lambda item: item["opportunity_score"], reverse=True)
    return scored_terms


def load_existing_terms() -> dict[str, dict[str, Any]]:
    """读取已有详情 JSON，用于每日去重并保留 first_seen。"""

    existing_terms: dict[str, dict[str, Any]] = {}
    if not config.TERMS_DIR.exists():
        return existing_terms

    for term_file in config.TERMS_DIR.glob("*.json"):
        if term_file.name == "latest.json":
            continue
        try:
            payload = json.loads(term_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        slug = payload.get("slug")
        if slug:
            existing_terms[slug] = payload
    return existing_terms


def ensure_data_files_exist() -> None:
    """第一次运行时创建空数据文件。"""

    config.TERMS_DIR.mkdir(parents=True, exist_ok=True)
    config.HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    if not config.SUBSCRIBERS_FILE.exists():
        write_json(config.SUBSCRIBERS_FILE, [])
    if not (config.TERMS_DIR / "latest.json").exists():
        write_json(config.TERMS_DIR / "latest.json", {"updated_at": "", "terms": []})


def write_json(path: Path, payload: Any) -> None:
    """统一写 JSON，保证格式易读。"""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
