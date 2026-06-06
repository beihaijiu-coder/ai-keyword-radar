"""这个文件负责从标题和摘要里抽取候选新词，并统计近期/历史出现次数。"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

import config


STOPWORD_TERMS = {
    "after",
    "ai",
    "ai s",
    "api",
    "app",
    "apps",
    "apple",
    "ask hn",
    "show hn",
    "launch hn",
    "hacker news",
    "product hunt",
    "meta",
    "node",
    "python",
    "swift",
    "there",
    "they",
    "trump",
    "what",
    "google",
    "openai",
    "anthropic",
    "microsoft",
    "github",
    "startup",
    "startups",
}

STOP_WORDS = {
    "a",
    "an",
    "and",
    "any",
    "are",
    "as",
    "at",
    "be",
    "building",
    "by",
    "for",
    "from",
    "how",
    "in",
    "into",
    "is",
    "it",
    "new",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "using",
    "with",
    "you",
    "your",
}

AI_CONTEXT_WORDS = (
    "ai",
    "agent",
    "agents",
    "agentic",
    "assistant",
    "automation",
    "benchmark",
    "browser",
    "chatbot",
    "coding",
    "copilot",
    "embedding",
    "eval",
    "fine tuning",
    "inference",
    "llm",
    "model",
    "multimodal",
    "prompt",
    "rag",
    "reasoning",
    "synthetic",
    "vector",
    "voice",
    "workflow",
)


def build_candidate_stats(items: list[dict[str, Any]], now: datetime | None = None) -> list[dict[str, Any]]:
    """统计每个候选词的近期频次、历史频次、来源和示例链接。"""

    now = now or datetime.now(timezone.utc)
    recent_start = now - timedelta(days=config.RECENT_WINDOW_DAYS)
    history_start = recent_start - timedelta(days=config.HISTORY_WINDOW_DAYS)

    stats: dict[str, dict[str, Any]] = {}

    for item in items:
        published_at = parse_item_datetime(item.get("published_at", "")) or now
        if published_at < history_start:
            continue

        text = f"{item.get('title', '')} {item.get('summary', '')}"
        candidates = extract_candidate_terms(text)

        # 同一个帖子里重复出现同一个词，只算一次，避免单篇文章刷高频次。
        for canonical_term, display_name in candidates.items():
            if canonical_term not in stats:
                stats[canonical_term] = {
                    "term": display_name,
                    "canonical_term": canonical_term,
                    "mention_count_recent": 0,
                    "mention_count_history": 0,
                    "sources": set(),
                    "example_links": [],
                    "display_names": Counter(),
                }

            term_stats = stats[canonical_term]
            term_stats["display_names"][display_name] += 1
            term_stats["sources"].add(item.get("source", "unknown"))

            if item.get("url") and item["url"] not in term_stats["example_links"]:
                term_stats["example_links"].append(item["url"])

            if published_at >= recent_start:
                term_stats["mention_count_recent"] += 1
            else:
                term_stats["mention_count_history"] += 1

    filtered_terms: list[dict[str, Any]] = []
    for term_stats in stats.values():
        if (
            term_stats["mention_count_recent"] >= config.MIN_RECENT_MENTIONS
            and term_stats["mention_count_history"] <= config.MAX_HISTORY_MENTIONS
        ):
            display_name = term_stats["display_names"].most_common(1)[0][0]
            filtered_terms.append(
                {
                    "term": display_name,
                    "canonical_term": term_stats["canonical_term"],
                    "mention_count_recent": term_stats["mention_count_recent"],
                    "mention_count_history": term_stats["mention_count_history"],
                    "sources": sorted(term_stats["sources"]),
                    "example_links": term_stats["example_links"][:5],
                }
            )

    filtered_terms.sort(
        key=lambda item: (
            item["mention_count_recent"],
            len(item["sources"]),
            -item["mention_count_history"],
        ),
        reverse=True,
    )
    return filtered_terms


def extract_candidate_terms(text: str) -> dict[str, str]:
    """用简单规则抽取名词短语和产品名，避免引入复杂 NLP 依赖。"""

    candidates: dict[str, str] = {}
    clean_text = clean_source_text(text)

    # 规则 1：抽取包含 AI 语境词的 2-4 词短语，例如 "agent browser"、"AI coding assistant"。
    words = re.findall(r"[A-Za-z][A-Za-z0-9-]*", clean_text)
    for start_index in range(len(words)):
        for phrase_length in range(2, 5):
            phrase_words = words[start_index : start_index + phrase_length]
            if len(phrase_words) != phrase_length:
                continue
            phrase = " ".join(phrase_words)
            lower_phrase = phrase.lower()
            if has_ai_context(lower_phrase):
                add_candidate(candidates, phrase)

    # 规则 2：抽取标题式产品名或概念名，例如 "Claude Code"、"Gemini CLI"。
    title_case_pattern = r"\b(?:AI|API|CLI|GPT|LLM|RAG|[A-Z][A-Za-z0-9]+)(?:\s+(?:AI|API|CLI|GPT|LLM|RAG|[A-Z][A-Za-z0-9]+)){1,3}\b"
    for match in re.finditer(title_case_pattern, clean_text):
        add_candidate(candidates, match.group(0))

    return candidates


def add_candidate(candidates: dict[str, str], raw_candidate: str) -> None:
    """清洗并保存一个候选词。"""

    display_name = normalize_display_name(raw_candidate)
    canonical_term = display_name.lower()

    if not is_useful_candidate(display_name, canonical_term):
        return
    candidates[canonical_term] = display_name


def normalize_display_name(value: str) -> str:
    """把候选词清成适合展示的格式。"""

    value = value.replace("-", " ")
    value = re.sub(r"\s+", " ", value).strip(" \t\r\n:;,.!?()[]{}\"'")
    value = re.sub(r"^(Show HN|Ask HN|Launch HN)\s*[:\-]\s*", "", value, flags=re.IGNORECASE)
    return value.strip()


def is_useful_candidate(display_name: str, canonical_term: str) -> bool:
    """过滤明显不是新词的短语。"""

    if canonical_term in STOPWORD_TERMS:
        return False
    if len(canonical_term) < 4 or len(canonical_term) > 60:
        return False
    if canonical_term.startswith(("the ", "and ", "for ", "with ")):
        return False

    words = canonical_term.split()
    if len(words) > 4:
        return False
    if all(word in STOP_WORDS for word in words):
        return False
    if words[0] in STOP_WORDS or words[-1] in STOP_WORDS:
        return False
    if any(word in STOP_WORDS for word in words):
        return False
    if len(words) == 1:
        return False
    return True


def clean_source_text(text: str) -> str:
    """去掉 URL 和 HTML 标签，减少抽词噪音。"""

    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\b([A-Za-z]+)'s\b", r"\1", text)
    return " ".join(text.split())


def has_ai_context(lower_phrase: str) -> bool:
    """判断短语是否真的包含 AI 语境词，避免把 air 里的 ai 误判成 AI。"""

    tokens = lower_phrase.split()
    token_set = set(tokens)
    for context_word in AI_CONTEXT_WORDS:
        if " " in context_word:
            if re.search(rf"\b{re.escape(context_word)}\b", lower_phrase):
                return True
        elif context_word in token_set:
            return True
    return False


def parse_item_datetime(value: str) -> datetime | None:
    """把来源中的时间统一成 UTC datetime。"""

    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def slugify_term(term: str) -> str:
    """把词转成详情页 URL 使用的 slug。"""

    slug = re.sub(r"[^a-z0-9]+", "-", term.lower()).strip("-")
    return slug or "term"
