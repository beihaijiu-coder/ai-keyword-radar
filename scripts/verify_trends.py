"""这个文件负责用 pytrends 做 Google Trends 验证，并实现缓存、重试和限流。"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import config


class TrendsVerifier:
    """一个小的 Google Trends 查询器，避免把 pytrends 逻辑散落到主流程里。"""

    def __init__(self, cache_file: Path | None = None) -> None:
        self.cache_file = cache_file or config.TRENDS_CACHE_FILE
        self.cache = self.load_cache()
        self.last_request_time: float | None = None
        self.pytrends_client = None

    def get_search_interest(self, term: str) -> int | None:
        """返回 0-100 的搜索热度；失败时返回 None，让主流程继续。"""

        if not config.ENABLE_GOOGLE_TRENDS:
            return None

        cached_value = self.cache.get(term.lower())
        if cached_value is not None:
            return cached_value.get("interest")

        client = self.get_pytrends_client()
        if client is None:
            return None

        for attempt in range(1, config.TRENDS_RETRY_TIMES + 1):
            try:
                self.wait_for_rate_limit()
                client.build_payload([term], timeframe=config.TRENDS_TIMEFRAME, geo=config.TRENDS_GEO)
                trends_data = client.interest_over_time()
                interest = self.read_interest_from_dataframe(trends_data, term)
                self.cache[term.lower()] = {
                    "interest": interest,
                    "checked_at": datetime.now(timezone.utc).isoformat(),
                }
                self.save_cache()
                return interest
            except Exception as exc:  # noqa: BLE001 - pytrends 可能抛出多种网络/限流错误。
                print(f"[warning] Google Trends failed for '{term}' (attempt {attempt}): {exc}")
                time.sleep(attempt * 3)

        return None

    def get_pytrends_client(self):
        """延迟导入 pytrends；没安装时跳过，避免整个脚本崩掉。"""

        if self.pytrends_client is not None:
            return self.pytrends_client

        try:
            from pytrends.request import TrendReq
        except Exception as exc:  # noqa: BLE001
            print(f"[warning] pytrends is unavailable, skip Google Trends: {exc}")
            return None

        self.pytrends_client = TrendReq(hl="en-US", tz=0)
        return self.pytrends_client

    def wait_for_rate_limit(self) -> None:
        """保证同一次运行中相邻两次 Trends 请求间隔不少于 10 秒。"""

        now = time.time()
        if self.last_request_time is not None:
            elapsed_seconds = now - self.last_request_time
            wait_seconds = config.TRENDS_MIN_SECONDS_BETWEEN_REQUESTS - elapsed_seconds
            if wait_seconds > 0:
                time.sleep(wait_seconds)
        self.last_request_time = time.time()

    def read_interest_from_dataframe(self, trends_data, term: str) -> int:
        """从 pytrends 返回的数据里取平均热度。"""

        if trends_data is None or trends_data.empty or term not in trends_data:
            return 0
        values = [int(value) for value in trends_data[term].tolist()]
        if not values:
            return 0
        return round(sum(values) / len(values))

    def load_cache(self) -> dict:
        """读取本地缓存，缓存坏了就重新开始。"""

        if not self.cache_file.exists():
            return {}
        try:
            return json.loads(self.cache_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def save_cache(self) -> None:
        """保存缓存，降低每天重复查询同一个词的概率。"""

        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache_file.write_text(json.dumps(self.cache, ensure_ascii=False, indent=2), encoding="utf-8")
