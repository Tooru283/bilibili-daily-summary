# B站观看总结生成器

一个本地 Python 项目，用于分析 **B站观看历史**，生成适配 **Obsidian + Dataview** 的日报与周报。

当前版本已经从单体脚本重构为按职责拆分的 package。README 重点说明：**项目定位、模块边界、运行方式、后续维护入口**。

---

## 1. 项目定位

这是一个**本地个人分析工具**。

核心能力：

- 从浏览器读取 B站 Cookie
- 拉取观看历史并兼容分 P / SSL 异常场景
- 生成日报 Markdown
- 基于日报缓存聚合生成周报
- 调用 Claude CLI 生成自然语言总结

设计目标：

- 明确“抓数 / 分析 / 渲染 / AI / 存储”边界
- 为测试、类型和新报表扩展留出口

---

## 2. 项目结构

```text
Blisummary/
├── daily_summary.py                 # 日报 CLI 入口
├── weekly_summary.py                # 周报 CLI 入口
├── run_summary.sh                   # 定时运行脚本
├── README.md
└── blisummary/
    ├── config.py                    # 配置与路径 helper
    ├── models.py                    # 共享 TypedDict
    ├── common/
    │   ├── ai.py                    # Claude CLI 调用
    │   └── formatting.py            # 通用格式化
    ├── bilibili/
    │   └── client.py                # Cookie / API / 分P补全 / SSL fallback
    ├── storage/
    │   └── stats_store.py           # .stats 与 frontmatter 读写
    ├── daily/
    │   ├── metrics.py               # 日报统计与评分
    │   ├── render.py                # 日报渲染
    │   └── service.py               # 日报流程编排
    └── weekly/
        ├── analytics.py             # 周报聚合与问题分析
        ├── render.py                # 周报渲染与归档
        └── service.py               # 周报流程编排
```

---

## 3. 模块边界

| 模块                                                                | 作用                                          |
| ------------------------------------------------------------------- | --------------------------------------------- |
| [daily_summary.py](daily_summary.py)                                   | 解析 `--date` 并调用日报 service            |
| [weekly_summary.py](weekly_summary.py)                                 | 解析周参数并调用周报 service                  |
| [blisummary/config.py](blisummary/config.py)                           | 输出目录、文件命名规则、Claude CLI 定位       |
| [blisummary/bilibili/client.py](blisummary/bilibili/client.py)         | B站 Cookie、历史接口、分 P 补全、SSL fallback |
| [blisummary/storage/stats_store.py](blisummary/storage/stats_store.py) | 日报缓存保存/读取、frontmatter 恢复           |
| [blisummary/daily/metrics.py](blisummary/daily/metrics.py)             | 日报业务规则、分类、评分                      |
| [blisummary/daily/render.py](blisummary/daily/render.py)               | 日报 Markdown 文本片段                        |
| [blisummary/daily/service.py](blisummary/daily/service.py)             | 日报主流程                                    |
| [blisummary/weekly/analytics.py](blisummary/weekly/analytics.py)       | 周报聚合、阈值分析、建议生成                  |
| [blisummary/weekly/render.py](blisummary/weekly/render.py)             | 周报 Markdown 与归档                          |
| [blisummary/weekly/service.py](blisummary/weekly/service.py)           | 周报主流程                                    |
| [blisummary/common/ai.py](blisummary/common/ai.py)                     | Claude 调用封装                               |
| [blisummary/common/formatting.py](blisummary/common/formatting.py)     | 通用格式化能力                                |

分层约定：

- **metrics / analytics**：业务规则与计算
- **render**：文本渲染
- **service**：流程编排
- **bilibili / common / storage**：外部系统与基础设施

---

## 4. 关键数据流

### 日报

```text
daily_summary.py
  -> daily.service.run_daily_summary()
     -> bilibili.client.get_bilibili_history()
     -> daily.metrics.*
     -> daily.render.*
     -> common.ai.run_claude_prompt()
     -> storage.stats_store.save_stats_by_date()
     -> 输出日报 Markdown
```

### 周报

```text
weekly_summary.py
  -> weekly.service.generate_weekly_summary()
     -> storage.stats_store.load_week_stats()
     -> weekly.analytics.*
     -> common.ai.run_claude_prompt()
     -> weekly.render.build_markdown()
     -> weekly.render.archive_week()
     -> 输出周报 Markdown
```

说明：周报**不直接请求 B站 API**，而是依赖日报缓存 `.stats_YYYY-MM-DD.json`。

---

## 5. 运行方式

### 环境要求

- Python 3.10+
- `requests`
- `browser-cookie3`
- Claude CLI

### 安装依赖

```bash
pip install requests browser-cookie3
npm install -g @anthropic-ai/claude-code
claude login
```

### 日报

```bash
python daily_summary.py
python daily_summary.py --date 2026-04-01
```

### 周报

```bash
python weekly_summary.py
python weekly_summary.py 0
python weekly_summary.py 2026-W10
```

---

## 6. 配置入口

主要配置集中在 [blisummary/config.py](blisummary/config.py)。

常见修改点：

- `SUMMARY_FOLDER`：输出目录
- `CLAUDE_CLI`：Claude CLI 路径
- `summary_markdown_path()` / `stats_json_path()`：日报文件命名规则
- `weekly_archive_folder()` / `weekly_summary_path()`：周报归档与文件命名规则

其他规则入口：

- 周报健康阈值： [blisummary/weekly/analytics.py](blisummary/weekly/analytics.py) 的 `HEALTH`
- 日报目标规则： [blisummary/daily/render.py](blisummary/daily/render.py) 的 `generate_goal_tracking()`
- 视频分类标准： [blisummary/daily/metrics.py](blisummary/daily/metrics.py) 的 `classify_videos()`

---

## 7. 输出结构

```text
04_Bilibili/
├── 2026-04-13-B站总结.md
├── .stats_2026-04-13.json
└── 周总结/
    └── W15(2026.4.6-4.12)/
        ├── 2026-04-07-B站总结.md
        └── 2026-W15-周总结.md
```

- `*.md`：人读文档
- `.stats_*.json`：周报依赖的日报缓存
- `周总结/Wxx(...)`：已结束周的归档目录

---

## 8. 已处理的关键兼容点

- **SSL 证书异常**：在 [blisummary/bilibili/client.py](blisummary/bilibili/client.py) 中对 `SSLError` 做 `trust_env=False` fallback
- **`--date` 模式历史不足**：按目标日期动态扩大抓取范围，直到覆盖目标日
- **`.stats` 丢失恢复**：优先读取 JSON，缺失时从日报 frontmatter 尽量恢复核心字段

---

## 9. 维护建议

推荐优先顺序：

1. 给 [blisummary/daily/metrics.py](blisummary/daily/metrics.py)、[blisummary/weekly/analytics.py](blisummary/weekly/analytics.py)、[blisummary/storage/stats_store.py](blisummary/storage/stats_store.py) 补最小测试
2. 继续收紧 `TypedDict` 与函数返回类型
3. 逐步抽离 prompt 模板和更多阈值配置
4. 再考虑月报、趋势分析、CSV/JSON 导出
