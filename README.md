# AI 工具新词雷达

## 1. 这个项目是干嘛的

这是一个面向英文市场的 Web 工具：每天从 Hacker News、Product Hunt、厂商博客 RSS 里发现正在冒头的 AI 工具新词，计算机会分，并生成一个英文榜单网站；每周给订阅者发一封榜单周报。

## 2. 项目目录说明

- `SPEC.md`：项目需求文档，开发时以它为准。
- `scripts/`：Python 抓取、抽词、Trends 验证、评分、发邮件脚本。
- `scripts/config.py`：所有可调参数都放这里。
- `data/terms/latest.json`：首页读取的最新榜单。
- `data/terms/<slug>.json`：每个新词的详情页数据。
- `data/terms/history/YYYY-MM-DD.json`：每天归档一次历史榜单。
- `data/subscribers.json`：邮件订阅者，只保存邮箱和订阅时间。
- `web/`：Next.js 网站，包含首页、详情页、关于页、订阅 API。
- `.github/workflows/daily_update.yml`：每天自动抓取并更新数据。
- `.github/workflows/weekly_email.yml`：每周自动发送邮件周报。

## 3. 如何在本地跑起来

先打开终端，进入项目目录：

```bash
cd /Volumes/北海酒/新词新站
```

安装 Python 依赖：

```bash
python3 -m pip install -r requirements.txt
```

生成榜单 JSON：

```bash
python3 scripts/build_data.py
```

安装网站依赖并启动本地网站：

```bash
cd web
npm install
npm run dev
```

浏览器打开：

```text
http://localhost:3000
```

本地验证顺序：

- 第一步最小闭环：运行 `python3 scripts/build_data.py`，确认 `data/terms/latest.json` 被生成；再打开首页看榜单。
- 第二步 Product Hunt：在 `.env` 或 GitHub Secrets 里配置 `PRODUCTHUNT_TOKEN`，重新运行脚本，日志里会出现 Product Hunt 抓取数量。
- 第三步 RSS：修改 `scripts/config.py` 里的 `RSS_FEEDS`，重新运行脚本，日志里会出现 RSS 抓取数量。
- 第四步 Google Trends：安装 `pytrends` 后运行脚本，`data/trends_cache.json` 会缓存查询结果。
- 第五步机会分：查看 `latest.json`，每个词都有 `velocity_score`、`search_gap_score`、`source_diversity_score`、`opportunity_score`。
- 第六步页面与订阅：打开首页提交邮箱，确认 `data/subscribers.json` 增加邮箱；打开 `/about` 和 `/term/<slug>`。
- 第七步工作流：把项目推到 GitHub 后，在 Actions 页面手动运行两个 workflow 验证。

## 4. 如何配置

复制环境变量示例：

```bash
cp .env.example .env
```

### 增减厂商 RSS 列表

打开 `scripts/config.py`，修改 `RSS_FEEDS`：

```python
RSS_FEEDS = [
    "https://openai.com/blog/rss.xml",
    "https://blog.anthropic.com/rss",
]
```

### 修改新词识别参数

仍然在 `scripts/config.py` 里修改：

```python
RECENT_WINDOW_DAYS = 7
HISTORY_WINDOW_DAYS = 90
MIN_RECENT_MENTIONS = 3
MAX_HISTORY_MENTIONS = 1
```

### 调整机会分权重

在 `scripts/config.py` 里修改这三项，三项加起来应等于 `1.0`：

```python
WEIGHT_VELOCITY = 0.4
WEIGHT_SEARCH_GAP = 0.4
WEIGHT_SOURCE_DIVERSITY = 0.2
```

### 配置邮件 provider

项目不写死具体邮件厂商。你选择一个邮件服务后，把它的 API 地址和密钥放到环境变量：

```bash
EMAIL_PROVIDER=
EMAIL_API_KEY=
EMAIL_API_URL=
EMAIL_FROM=
SITE_URL=https://你的域名
```

如果没有配置 `EMAIL_API_URL` 或 `EMAIL_FROM`，`python3 scripts/send_email.py` 会进入 dry-run，只打印要发送的内容，不真的发邮件。

## 5. 定时任务说明

GitHub Actions 的 cron 使用 UTC 时间，不是北京时间。

- 每天早上 7 点（北京时间）自动抓取 + 更新网站：workflow 里写 `0 23 * * *`。
- 每周二早上 7 点（北京时间）自动群发邮件周报：workflow 里写 `0 23 * * 1`。
- 北京时间 07:00 = UTC 前一天 23:00。

如果你想改成北京时间 09:00，就要换算成 UTC 01:00，cron 写：

```yaml
cron: "0 1 * * *"
```

## 6. 如何部署到 Vercel

1. 把整个项目推到 GitHub。
2. 在 Vercel 新建项目，选择这个 GitHub 仓库。
3. 使用仓库根目录部署；项目里已经有 `vercel.json`，会进入 `web/` 构建 Next.js。
4. 在 Vercel 环境变量里填写 `.env.example` 里的变量。
5. 在 GitHub 仓库 Settings → Secrets and variables → Actions 里填写 `PRODUCTHUNT_TOKEN` 和邮件相关 secrets。
6. Vercel 连接 GitHub 后，每次 `daily_update.yml` 提交新的 JSON，Vercel 会自动重新部署。

## 7. 常见问题 / 注意事项

### pytrends 被限流怎么办

`scripts/verify_trends.py` 已经做了重试、本地缓存，并保证同一次运行中相邻请求间隔不少于 10 秒。如果仍然被限流，可以先降低 `scripts/config.py` 里的 `MAX_TERMS_TO_SCORE`，过一段时间再恢复。

### Reddit API 商业用途警告

⚠️ 商业化前需重新评估 Reddit 商用条款，商业访问起步价约 $12,000/月。本 MVP 默认 `ENABLE_REDDIT = False`，不要在商业化前打开。

### 密钥安全提示

`.env` 文件不能提交到 Git。真实 token 只放在本地 `.env`、Vercel 环境变量或 GitHub Secrets 里。

### GitHub Actions 时区说明

Actions 的 cron 是 UTC。北京时间是 UTC+8，所以北京时间早上 7 点要写成 UTC 前一天 23 点，也就是 `0 23 * * *`。
