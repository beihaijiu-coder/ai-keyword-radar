"""这个文件负责每周读取最近 7 天榜单，并给订阅者发送周报邮件。"""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen

import config


def main() -> None:
    """每周邮件任务入口。"""

    subscribers = load_subscribers()
    if not subscribers:
        print("[info] no subscribers, skip weekly email.")
        return

    top_terms = load_recent_high_score_terms()
    if not top_terms:
        print("[info] no terms in the last 7 days, skip weekly email.")
        return

    for subscriber in subscribers:
        email = subscriber.get("email", "")
        if not email:
            continue
        send_weekly_email(email, top_terms)


def load_subscribers() -> list[dict[str, Any]]:
    """读取订阅者列表。"""

    if not config.SUBSCRIBERS_FILE.exists():
        return []
    try:
        payload = json.loads(config.SUBSCRIBERS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if isinstance(payload, list):
        return payload
    return []


def load_recent_high_score_terms() -> list[dict[str, Any]]:
    """读取过去 7 天 history JSON，按 slug 去重并保留最高分。"""

    today = date.today()
    terms_by_slug: dict[str, dict[str, Any]] = {}

    for days_ago in range(7):
        history_date = today - timedelta(days=days_ago)
        history_file = config.HISTORY_DIR / f"{history_date.isoformat()}.json"
        if not history_file.exists():
            continue

        try:
            payload = json.loads(history_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue

        for term in payload.get("terms", []):
            if term.get("opportunity_score", 0) < 60:
                continue
            slug = term.get("slug", "")
            if not slug:
                continue
            existing = terms_by_slug.get(slug)
            if existing is None or term["opportunity_score"] > existing["opportunity_score"]:
                terms_by_slug[slug] = term

    terms = list(terms_by_slug.values())
    terms.sort(key=lambda item: item.get("opportunity_score", 0), reverse=True)
    return terms[:10]


def send_weekly_email(email: str, terms: list[dict[str, Any]]) -> None:
    """发送单封邮件；没有配置 provider 时进入 dry-run，方便本地验证。"""

    subject = f"{config.EMAIL_SUBJECT_PREFIX}: {len(terms)} rising AI terms"
    text_body = build_text_email(email, terms)
    html_body = build_html_email(email, terms)

    if not config.EMAIL_API_URL or not config.EMAIL_FROM:
        print(f"[dry-run] would send weekly email to {email}: {subject}")
        return

    payload = {
        "provider": config.EMAIL_PROVIDER,
        "from": config.EMAIL_FROM,
        "to": email,
        "subject": subject,
        "text": text_body,
        "html": html_body,
    }
    request_headers = {"Content-Type": "application/json"}
    if config.EMAIL_API_KEY:
        request_headers["Authorization"] = f"Bearer {config.EMAIL_API_KEY}"

    request = Request(
        config.EMAIL_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=request_headers,
        method="POST",
    )

    try:
        with urlopen(request, timeout=30) as response:
            print(f"[info] sent email to {email}: HTTP {response.status}")
    except Exception as exc:  # noqa: BLE001 - 单个邮箱失败不影响其他订阅者。
        print(f"[warning] failed to send email to {email}: {exc}")


def build_text_email(email: str, terms: list[dict[str, Any]]) -> str:
    """生成纯文本邮件，确保任何邮件客户端都能阅读。"""

    lines = ["This week's rising AI terms:", ""]
    for index, term in enumerate(terms, start=1):
        lines.append(f"{index}. {term['term']} — Opportunity Score: {term['opportunity_score']}")
        lines.append(f"   {term['trend_note']}")
        lines.append(f"   {config.SITE_URL.rstrip('/')}/term/{term['slug']}")
        lines.append("")

    lines.append(f"Unsubscribe: {build_unsubscribe_url(email)}")
    return "\n".join(lines)


def build_html_email(email: str, terms: list[dict[str, Any]]) -> str:
    """生成 HTML 邮件，并包含一键退订链接。"""

    items = []
    for term in terms:
        term_url = f"{config.SITE_URL.rstrip('/')}/term/{term['slug']}"
        items.append(
            "<li>"
            f"<strong>{escape_html(term['term'])}</strong> "
            f"(Opportunity Score: {term['opportunity_score']})"
            f"<br>{escape_html(term['trend_note'])}"
            f"<br><a href=\"{term_url}\">View term page</a>"
            "</li>"
        )

    return (
        "<h1>This week's rising AI terms</h1>"
        "<ol>"
        + "".join(items)
        + "</ol>"
        f"<p><a href=\"{build_unsubscribe_url(email)}\">Unsubscribe</a></p>"
    )


def build_unsubscribe_url(email: str) -> str:
    """生成一键退订链接。"""

    return f"{config.SITE_URL.rstrip('/')}/api/unsubscribe?email={quote(email)}"


def escape_html(value: str) -> str:
    """最小 HTML 转义，避免邮件内容破坏 HTML 结构。"""

    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


if __name__ == "__main__":
    main()
