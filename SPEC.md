# AI 工具新词雷达 — 项目开发规格（SPEC.md）

> 本文件是交给 Codex 的唯一权威需求文档。Codex 必须严格按本文件实现，遇到本文件未规定的细节，应选择**最简单、最易读**的方案，不得自行扩大范围或过度设计。

## 1. 项目目标（What & Why）

构建一个**面向海外用户、纯英文**的 Web 工具，自动从公开免费数据源中发现"AI 工具领域正在兴起的新词/新概念"，给每个新词打一个"机会分"，并以一个**每日更新的新词榜网页**呈现，同时提供**邮件订阅**让用户每周收到最新榜单周报。

核心价值：帮做 SEO / 独立开发 / 出海建站的人，比别人更早发现"搜索端还空白、但已经开始升温"的 AI 新词，从而抢占内容/工具流量红利。

目标用户：英文市场的 SEO 从业者、独立开发者、内容站/工具站站长。

---

## 2. MVP 范围（必须严格遵守）

### 2.1 本期要做的（In Scope）

- 自动抓取数据源（Hacker News、Product Hunt、厂商 RSS）
- 从抓取文本中识别"候选新词"
- 用 Google Trends 做"搜索端是否仍空白"的交叉验证
- 计算每个新词的机会分（Opportunity Score, 0–100）
- 生成静态网页：首页榜单页、每个新词的详情页、关于/方法论页
- 邮件订阅功能：收集邮箱 + **每周**自动群发一封榜单周报
  （数据抓取每天跑，邮件每周只发一次，避免用户因频繁邮件退订）
- 一份给编程小白看的中文 README

### 2.2 本期明确不做的（Out of Scope，禁止实现）

- ❌ 用户账号 / 登录系统
- ❌ Stripe 或任何付费 / 订阅收费功能
- ❌ 复杂的前端交互（筛选器、排序器、可视化仪表盘）
- ❌ 自定义关键词告警
- ❌ 数据库（MVP 用 Git 仓库内的 JSON 文件存数据，见 §6）
- ❌ X(Twitter) 数据源
- ❌ 任何付费第三方 API（Exploding Topics / Glimpse / Ahrefs / DataForSEO / Apify 等）
- ❌ 抓取 Google 首页判断竞争度（留待 V2）
- ❌ 每日发送邮件（邮件保持每周一封）

> 任何"为未来可能的功能提前搭架子"的行为都禁止。MVP 就按 MVP 的简单做。

---

## 3. 技术栈（钉死，不得替换）

| 层 | 技术 | 说明 |
|---|---|---|
| 前端 / 网页 | **Next.js（App Router）** | 用静态生成 SSG / ISR，SEO 友好 |
| 部署 | **Vercel 免费层** | 零成本，自带全球 CDN |
| 数据抓取脚本 | **Python 3** | HN/PH/RSS/Trends 生态成熟 |
| 定时运行 | **GitHub Actions（免费额度）** | **每天早上 7 点（UTC+8）** 定时执行抓取与页面更新 |
| 数据存储 | **仓库内 JSON 文件**（见 §6） | MVP 不用数据库 |
| 邮件服务 | **可替换的邮件 Provider（免费层）** | 在配置中以变量定义，不写死具体厂商 |

---

## 4. 定时任务规格（重要：时区说明必读）

### 4.1 核心概念：GitHub Actions 使用 UTC 时间

GitHub Actions 的 cron 表达式**全部以 UTC 时间为准**，不是本地时间。
本项目默认以 **UTC+8（北京 / 香港 / 新加坡时间）** 为基准，
"每天早上 7 点" = UTC 前一天 23:00。

换算对照表（供参考，如需改时区照此换算）：

| 目标时区 | 想要的本地时间 | 对应 UTC 时间 | cron 表达式 |
|---|---|---|---|
| UTC+8（北京） | 每天 07:00 | 前一天 23:00 | `0 23 * * *` |
| UTC+0（伦敦冬令时） | 每天 07:00 | 当天 07:00 | `0 7 * * *` |
| UTC-5（纽约冬令时） | 每天 07:00 | 当天 12:00 | `0 12 * * *` |

### 4.2 每日数据抓取任务（`daily_update.yml`）

- **触发时间**：每天 UTC 23:00（= 北京时间每天早上 07:00）
- **cron 表达式**：`0 23 * * *`
- **执行内容**：抓取 → 识别新词 → Trends 验证 → 打分 → 生成 JSON → commit → 触发 Vercel 重新部署

> ⚠️ Codex 注意：workflow 文件中 cron 表达式旁边**必须加注释**，写明：
> `# UTC 23:00 = 北京时间 07:00（UTC+8）`

### 4.3 每周邮件周报任务（`weekly_email.yml`）

- **触发时间**：每周一 UTC 23:00（= 北京时间周二早上 07:00）
- **cron 表达式**：`0 23 * * 1`
- **执行内容**：读取过去 7 天的 history JSON → 汇总高机会分新词 → 群发邮件周报（含退订链接）

> 邮件与抓取分开触发，互不干扰。抓取失败不影响邮件发送，邮件失败不影响网站更新。

### 4.4 两个 workflow 文件位置

```
.github/workflows/
├── daily_update.yml    # 每天早上 7 点（UTC+8）：抓取→打分→生成JSON→部署
└── weekly_email.yml    # 每周一次：汇总7天新词→群发邮件周报
```

---

## 5. 系统数据流（端到端流程）

```
【每日任务】GitHub Actions — cron: 0 23 * * * (UTC) = 北京时间每天 07:00
        │
        ▼
   Python 抓取脚本
   ├── Hacker News (Algolia API，无需 key)
   ├── Product Hunt (V2 GraphQL API，免费 token)
   └── 厂商博客 RSS 列表（纯 RSS，零成本）
        │
        ▼
   抽取候选新词（名词短语 / 产品名）
        │
        ▼
   新词识别：近期升温 & 历史空白（见 §7.1）
        │
        ▼
   Google Trends 交叉验证（pytrends，控频 + 缓存）
        │
        ▼
   计算机会分 0–100（见 §7.2）
        │
        ▼
   写入 data/terms/latest.json
   写入 data/terms/<slug>.json（每个新词）
   写入 data/terms/history/<YYYY-MM-DD>.json（按日归档）
        │
        ▼
   commit 进仓库 → 触发 Vercel 重新构建 → 网站每日更新

【每周任务】GitHub Actions — cron: 0 23 * * 1 (UTC) = 北京时间周二 07:00
        │
        ▼
   读取过去 7 天 data/terms/history/*.json
        │
        ▼
   筛选本周新出现的高机会分新词
        │
        ▼
   群发邮件周报（含退订链接）给 data/subscribers.json 中所有订阅者
```

---

## 6. 数据存储约定（用 Git 当数据库）

抓取脚本的所有产物以 JSON 文件形式提交进仓库，Next.js 构建时读取这些文件生成页面。

### 目录结构

```
data/
├── terms/
│   ├── latest.json                   # 最新一次每日运行的新词榜（首页读它）
│   ├── <slug>.json                   # 每个新词一个文件（详情页读它）
│   └── history/
│       └── <YYYY-MM-DD>.json         # 按日归档（配合每日抓取频率）
└── subscribers.json                  # 邮件订阅者列表（仅邮箱+订阅时间）
```

> 注意：历史档案**按日存储**（`YYYY-MM-DD.json`），不按周存储，以配合每日抓取的频率。

### 每个新词 JSON 的字段结构（Codex 必须遵守此结构）

```json
{
  "term": "example-new-term",
  "slug": "example-new-term",
  "first_seen": "2026-06-06",
  "sources": ["hackernews", "producthunt"],
  "mention_count_recent": 14,
  "mention_count_history": 1,
  "velocity_score": 80,
  "search_gap_score": 90,
  "source_diversity_score": 67,
  "opportunity_score": 79,
  "trend_note": "Gaining traction on social channels; Google search volume still low — window is open.",
  "example_links": [
    "https://news.ycombinator.com/item?id=XXXXX"
  ]
}
```

---

## 7. 核心算法规格（产品心脏，必须按规则实现）

### 7.1 候选新词识别

从 HN / PH / RSS 抓回的标题与摘要文本中，抽取名词短语与产品名作为候选词。
判定一个词为"候选新词"需同时满足：

- **近期升温**：在最近 `RECENT_WINDOW_DAYS` 天内的出现频次 ≥ `MIN_RECENT_MENTIONS`
- **历史空白**：在更早的 `HISTORY_WINDOW_DAYS` 天历史窗口内的出现频次 ≤ `MAX_HISTORY_MENTIONS`

所有参数必须写成**集中配置项**（见 §8），初始默认值：

| 参数 | 默认值 | 含义 |
|---|---|---|
| `RECENT_WINDOW_DAYS` | `7` | 近期窗口（天） |
| `HISTORY_WINDOW_DAYS` | `90` | 历史窗口（天） |
| `MIN_RECENT_MENTIONS` | `3` | 近期最少出现次数 |
| `MAX_HISTORY_MENTIONS` | `1` | 历史最多允许出现次数 |

### 7.2 机会分（Opportunity Score, 0–100）

由三个子分加权得到，权重写成可配置项：

| 子分 | 含义 | 方向 |
|---|---|---|
| `velocity_score` | 近期频次相对历史的增长幅度，归一化 0–100 | 增长越快分越高 |
| `search_gap_score` | 用 pytrends 查该词当前搜索热度，归一化 0–100 | 搜索量越低分越高（窗口越开） |
| `source_diversity_score` | 该词在多少个不同数据源出现，归一化 0–100 | 来源越多分越高 |

```
opportunity_score = w1 * velocity_score
                  + w2 * search_gap_score
                  + w3 * source_diversity_score
```

初始权重（可配置）：`w1=0.4, w2=0.4, w3=0.2`

### 7.3 限流与健壮性规则（必须遵守）

- **pytrends 限流保护**：必须实现请求重试、失败跳过、结果本地缓存；
  每日运行频率提高后尤其注意控频，单次运行内相邻请求间隔不少于 10 秒。
- **数据源容错**：任一数据源抓取失败时，**不得中断整个流程**，
  应记录错误日志并用其余数据源继续。
- **每日去重**：同一个词如果前一天已在榜单中，今日再次出现时**更新频次数据**，
  不重复创建新条目，避免数据冗余。

---

## 8. 配置集中化（小白可调）

所有"可能需要调整"的参数**集中放在一个配置文件** `scripts/config.py`，
禁止散落在各处代码里。

```python
import os

# ============================
# 数据源配置
# ============================

# 是否启用各数据源（True / False）
ENABLE_HACKERNEWS   = True
ENABLE_PRODUCTHUNT  = True
ENABLE_RSS          = True
ENABLE_REDDIT       = False  # ⚠️ 商业化前需重新评估 Reddit 商用条款

# Product Hunt API Token（从环境变量读取，不要硬编码）
PRODUCTHUNT_TOKEN = os.environ.get("PRODUCTHUNT_TOKEN", "")

# 厂商博客 RSS 列表（可自行增减）
RSS_FEEDS = [
    "https://openai.com/blog/rss.xml",
    "https://blog.anthropic.com/rss",
    "https://blog.google/technology/ai/rss/",
    "https://huggingface.co/blog/feed.xml",
    "https://mistral.ai/news/rss",
    # 继续在此添加...
]

# ============================
# 定时任务时区备注（实际 cron 在 .github/workflows/ 里配置）
# ============================
# 每日抓取：cron `0 23 * * *`   = UTC 23:00 = 北京时间每天 07:00
# 每周邮件：cron `0 23 * * 1`   = UTC 周一 23:00 = 北京时间周二 07:00

# ============================
# 新词识别参数
# ============================
RECENT_WINDOW_DAYS    = 7    # 近期窗口（天）
HISTORY_WINDOW_DAYS   = 90   # 历史窗口（天）
MIN_RECENT_MENTIONS   = 3    # 近期最少出现次数
MAX_HISTORY_MENTIONS  = 1    # 历史最多允许出现次数

# ============================
# 机会分权重（三项之和应 = 1.0）
# ============================
WEIGHT_VELOCITY         = 0.4
WEIGHT_SEARCH_GAP       = 0.4
WEIGHT_SOURCE_DIVERSITY = 0.2

# ============================
# 邮件配置（从环境变量读取，不要硬编码）
# ============================
EMAIL_PROVIDER      = os.environ.get("EMAIL_PROVIDER", "")
EMAIL_API_KEY       = os.environ.get("EMAIL_API_KEY", "")
EMAIL_FROM          = os.environ.get("EMAIL_FROM", "")
EMAIL_SUBJECT_PREFIX = "This Week's Rising AI Terms"  # 周报邮件标题前缀
```

---

## 9. 页面规格（共 3 类，全英文）

### 9.1 首页 / 榜单页（`/`）

- 读取 `data/terms/latest.json`，展示最新一次每日运行的新词榜
- 每条显示：term 名称、opportunity_score、trend_note、来源标签（HN / PH / RSS）
- 页面顶部放**邮件订阅框**（输入框 + 提交按钮，提交后写入 `data/subscribers.json`）
- 页面显示"最后更新时间"（最近一次每日抓取的时间）
- SEO 主入口：`<title>` 和 `<meta description>` 必须包含目标关键词

### 9.2 新词详情页（`/term/[slug]`）

- 每个新词独立 URL（吃长尾搜索流量）
- 读取 `data/terms/<slug>.json`
- 展示：term 名称、机会分及三个子分、首次发现时间、来源列表、示例链接、趋势说明
- `<title>` 格式：`{term} — Trending AI Term | [网站名]`

### 9.3 关于 / 方法论页（`/about`）

- 英文，讲清楚"我们如何发现新词、机会分怎么算、每天几点更新"
- 建立用户信任，同时承载关键词排名
- 包含一节 **Privacy Policy**（GDPR 要求）

### 9.4 视觉风格

- 干净、信息密度高的**数据工具风**（参考 Exploding Topics 的克制风格）
- 不要花哨动效、不要复杂 UI 组件
- 预留广告位 / 联盟链接位的 DOM 节点（class 命名 `ad-slot`），MVP 阶段**留空不放内容**

---

## 10. 合规与数据使用边界（红线，必须遵守）

1. **仅使用官方 / 公开免费接口**：严格遵守各平台速率限制与服务条款（ToS）。
2. **Reddit 合规**：免费 API 明确不允许商业用途，默认关闭（`ENABLE_REDDIT = False`）。
   代码注释与 README 必须标注：
   "⚠️ 商业化前需重新评估 Reddit 商用条款，商业访问起步价约 $12,000/月"
3. **数据范围**：仅处理海外公开的产品 / 技术趋势信息，不涉及个人数据（除订阅邮箱外）。
4. **邮件订阅 GDPR 合规**：
   - 用户主动填写邮箱视为同意订阅
   - 每封邮件必须包含**一键退订链接**
   - `subscribers.json` 只存邮箱与订阅时间，不存其他个人信息
   - 退订后立即从列表中删除
5. **Privacy Policy**：网站必须提供隐私政策页面（置于 `/about` 底部或独立 `/privacy` 页）。

---

## 11. 代码规范与可维护性约束（最高优先级）

> 维护者是编程小白。**可读性与可维护性 > 简洁 > 性能 / 优雅**。

### 11.1 强制规则

- **可读性第一**：宁可代码长一点、啰嗦一点，也要让人一眼看懂。**禁止炫技写法，禁止过度抽象**。
- **按功能拆文件**：一个文件只做一类事，文件名自描述。
- **命名像大白话**：变量、函数名直接表达含义（如 `count_recent_mentions`），不用缩写黑话。
- **关键逻辑配中文注释**：注释解释"这一步在做什么、为什么这么做"，不只是翻译代码。
- **每个文件开头**用一段注释说明"这个文件是干嘛的"。
- **只用主流稳定的库**，能不加依赖就不加；禁止引入冷门依赖。
- **不为未来功能提前搭架子**，严格按 MVP 范围实现。
- **密钥 / Token 一律从环境变量读取**，绝不硬编码进代码。

### 11.2 Python 脚本文件命名规范

```
scripts/
├── config.py              # 所有可配置参数（§8）
├── fetch_hackernews.py    # 抓取 Hacker News 数据
├── fetch_producthunt.py   # 抓取 Product Hunt 数据
├── fetch_rss.py           # 抓取厂商 RSS 数据
├── extract_terms.py       # 从原始文本中抽取候选新词
├── verify_trends.py       # Google Trends 交叉验证（pytrends）
├── score.py               # 计算机会分
├── build_data.py          # 汇总生成 data/*.json（每日运行）
└── send_email.py          # 群发周报邮件（每周触发，非每日）
```

---

## 12. 推荐项目目录结构

```
项目根目录/
├── SPEC.md                          # 本文件
├── README.md                        # 给小白的中文说明（见 §13）
├── .env.example                     # 环境变量示例（不含真实密钥）
├── .gitignore                       # 忽略 .env、node_modules、__pycache__ 等
│
├── scripts/                         # Python 抓取 & 处理脚本
│   ├── config.py
│   ├── fetch_hackernews.py
│   ├── fetch_producthunt.py
│   ├── fetch_rss.py
│   ├── extract_terms.py
│   ├── verify_trends.py
│   ├── score.py
│   ├── build_data.py
│   └── send_email.py
│
├── data/                            # 生成的 JSON 数据（Git 当数据库）
│   ├── terms/
│   │   ├── latest.json              # 最新榜单
│   │   ├── <slug>.json              # 每个新词独立文件
│   │   └── history/
│   │       └── <YYYY-MM-DD>.json    # 按日归档
│   └── subscribers.json
│
├── web/                             # Next.js 前端
│   ├── app/
│   │   ├── page.tsx                 # 首页 / 榜单页
│   │   ├── term/
│   │   │   └── [slug]/
│   │   │       └── page.tsx         # 新词详情页
│   │   └── about/
│   │       └── page.tsx             # 关于 / 方法论页
│   ├── components/                  # 可复用 UI 组件
│   ├── public/                      # 静态资源
│   └── package.json
│
└── .github/
    └── workflows/
        ├── daily_update.yml         # cron: 0 23 * * *  → 每天北京时间 07:00 抓取+部署
        └── weekly_email.yml         # cron: 0 23 * * 1  → 每周二北京时间 07:00 发邮件周报
```

---

## 13. 必须交付的 README（给小白）

用**中文、大白话**写一份 `README.md`，必须包含以下所有章节：

1. **这个项目是干嘛的**（一句话说清楚）
2. **项目目录说明**（每个文件夹/关键文件是干嘛的）
3. **如何在本地跑起来**（从零开始，假设读者没有编程基础）
4. **如何配置**
   - 怎么增减厂商 RSS 列表
   - 怎么改新词识别参数（窗口天数、频次阈值）
   - 怎么调机会分权重
   - 怎么配置邮件 provider
5. **定时任务说明**
   - 每天早上 7 点（北京时间）自动抓取 + 更新网站
   - 每周二早上 7 点（北京时间）自动群发邮件周报
   - GitHub Actions cron 使用 UTC 时间：北京时间 07:00 = UTC 前一天 23:00
   - 如何修改触发时间（含时区换算说明）
6. **如何部署到 Vercel**（步骤说明）
7. **常见问题 / 注意事项**，必须包含：
   - pytrends 被限流怎么办
   - ⚠️ Reddit API 商业用途警告
   - 密钥安全提示（.env 文件不能提交到 Git）
   - GitHub Actions 时区说明（UTC vs 北京时间换算）

---

## 14. 验收标准（Definition of Done）

全部满足以下条件，才算 MVP 完成：

- [ ] 本地与 GitHub Actions 均能跑通完整链路：抓取 → 识别 → 验证 → 打分 → 生成 JSON
- [ ] `daily_update.yml` cron 为 `0 23 * * *`，文件内注释注明"UTC 23:00 = 北京时间 07:00"
- [ ] `weekly_email.yml` cron 为 `0 23 * * 1`，文件内注释注明"UTC 周一 23:00 = 北京时间周二 07:00"
- [ ] 历史档案按日存储（`data/terms/history/YYYY-MM-DD.json`）
- [ ] Next.js 能读取 JSON 并正确构建三类页面
- [ ] 新词详情页每个词有独立可访问 URL（`/term/<slug>`）
- [ ] 首页显示"最后更新时间"
- [ ] 邮件订阅框能收集邮箱并写入 `data/subscribers.json`
- [ ] 存在可运行的周报群发脚本，邮件含退订链接，**每周触发而非每日**
- [ ] 所有可调参数集中在 `scripts/config.py`，README 能指导小白完成配置与部署
- [ ] 代码符合 §11 全部规范
- [ ] 任一数据源失败不影响整体流程（有错误日志输出）
- [ ] 网站包含 Privacy Policy 内容

---

## 15. 给 Codex 的开发顺序建议

> 请严格按以下顺序分步实现，**每完成一步告知用户如何本地验证**，再进行下一步。不得跳步，不得一次性全部实现。

**第一步（最小闭环）**
搭好项目目录骨架，只接入 Hacker News 一个数据源，完成：
"抓取 → 识别候选新词 → 生成 `data/terms/latest.json` → Next.js 渲染最简榜单网页"
**不做**其他数据源、机会分、详情页、邮件。

**第二步**：加入 Product Hunt 数据源。

**第三步**：加入厂商 RSS 数据源。

**第四步**：加入 Google Trends 验证（pytrends，含限流保护）。

**第五步**：实现完整机会分计算（§7.2）。

**第六步**：完善三个页面（详情页 + 关于页），加入邮件订阅功能。

**第七步**：配置两个 GitHub Actions workflow
（`daily_update.yml` 每天 UTC 23:00 + `weekly_email.yml` 每周一 UTC 23:00），
完善 README。

---

*最后更新：2026-06-06*
