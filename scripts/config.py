"""这个文件集中放所有可调参数，方便不懂代码的人以后修改。"""

import os
from pathlib import Path


# ============================
# 项目路径配置
# ============================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
TERMS_DIR = DATA_DIR / "terms"
HISTORY_DIR = TERMS_DIR / "history"
SUBSCRIBERS_FILE = DATA_DIR / "subscribers.json"
TRENDS_CACHE_FILE = DATA_DIR / "trends_cache.json"


# ============================
# 数据源配置
# ============================

# 是否启用各数据源（True / False）
ENABLE_HACKERNEWS = True
ENABLE_PRODUCTHUNT = True
ENABLE_RSS = True
ENABLE_REDDIT = False  # ⚠️ 商业化前需重新评估 Reddit 商用条款，商业访问起步价约 $12,000/月

# Product Hunt API Token（从环境变量读取，不要硬编码）
PRODUCTHUNT_TOKEN = os.environ.get("PRODUCTHUNT_TOKEN", "")

# 厂商博客 RSS 列表（可自行增减）
RSS_FEEDS = [
    "https://openai.com/blog/rss.xml",
    "https://blog.anthropic.com/rss",
    "https://blog.google/technology/ai/rss/",
    "https://huggingface.co/blog/feed.xml",
    # "https://mistral.ai/news/rss",  # 2026-06-06 检查为 404，确认恢复后再打开。
]


# ============================
# 定时任务时区备注（实际 cron 在 .github/workflows/ 里配置）
# ============================
# 每日抓取：cron `0 23 * * *` = UTC 23:00 = 北京时间每天 07:00
# 每周邮件：cron `0 23 * * 1` = UTC 周一 23:00 = 北京时间周二 07:00


# ============================
# 新词识别参数
# ============================

RECENT_WINDOW_DAYS = 7
HISTORY_WINDOW_DAYS = 90
MIN_RECENT_MENTIONS = 3
MAX_HISTORY_MENTIONS = 1


# ============================
# 机会分权重（三项之和应 = 1.0）
# ============================

WEIGHT_VELOCITY = 0.4
WEIGHT_SEARCH_GAP = 0.4
WEIGHT_SOURCE_DIVERSITY = 0.2


# ============================
# Google Trends 配置
# ============================

ENABLE_GOOGLE_TRENDS = True
TRENDS_GEO = "US"
TRENDS_TIMEFRAME = "now 7-d"
TRENDS_MIN_SECONDS_BETWEEN_REQUESTS = 10
TRENDS_RETRY_TIMES = 3

# 控制单次运行最多验证多少个词，避免 pytrends 请求过多被限流。
MAX_TERMS_TO_SCORE = 30
MAX_TERMS_IN_LATEST = 30


# ============================
# 邮件配置（从环境变量读取，不要硬编码）
# ============================

EMAIL_PROVIDER = os.environ.get("EMAIL_PROVIDER", "")
EMAIL_API_KEY = os.environ.get("EMAIL_API_KEY", "")
EMAIL_API_URL = os.environ.get("EMAIL_API_URL", "")
EMAIL_FROM = os.environ.get("EMAIL_FROM", "")
EMAIL_SUBJECT_PREFIX = "This Week's Rising AI Terms"

# 用于生成邮件中的退订链接
SITE_URL = os.environ.get("SITE_URL", "http://localhost:3000")
