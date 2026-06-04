# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SafeTrade 新币监控 + TradeOgre 差集检测 + PRL 挖矿教程的静态网页。每 5 分钟通过 GitHub Actions 抓取数据，部署到 GitHub Pages。

在线地址：https://tianyubabg.github.io/newcoins-monitor/

## Commands

```bash
# 本地构建（生成 _site/）
python src/fetch.py

# 本地预览（需要 HTTP 服务，否则 fetch 会被 CORS 拦截）
cd _site && python -m http.server 8080

# 提交并推送后 GitHub Actions 自动部署到 Pages
git add -A && git commit -m "message" && git push
```

## SafeTrade API 数据结构

两个关键端点：
- `/markets` — 返回币对列表，关键字段：`name`（如 PRL/USDT）、`base_unit`、`quote_unit`、`state`（"enabled"）、`created_at`
- `/tickers` — 返回行情字典，key 是 `base_unit+quote_unit` 的小写拼接（如 `prlusdt`），value 含 `last`、`volume`、`high`、`low`、`price_change_percent`

fetch.py 先从 markets 筛选 `state=enabled`，按 `created_at` 降序取前 6 个，再从 tickers 匹配行情。

## TradeOgre 差集检测

TradeOgre 原生 API 没有上架时间戳，采用**本地缓存差集**方式检测新币：

1. **`tradeogre_cache.json`**（项目根目录，通过 GHA `actions/cache` 跨运行持久化）存储所有已知交易对及其首次发现时间
2. 每次运行抓取 `/api/v1/markets` 全市场列表，与缓存对比，发现新交易对则记录当前时间
3. 按首次发现时间降序取前 6 个展示，前 14 天内发现的打 `NEW` 标签
4. 涨跌幅用 `initialprice`（上线价）与当前 `price` 计算总涨幅
5. 如果 API 被 Cloudflare 拦截，静默跳过不影响 SafeTrade 数据

TradeOgre 返回格式：`[{"BTC-XMR": {"initialprice":"...", "price":"...", "volume":"...", "high":"...", "low":"..."}}]`

## Architecture Notes

- **数据流**: SafeTrade (API) + TradeOgre (API+cache diff) → GitHub Actions (cron 5min) → `_site/coins.json` → JS fetch 渲染
- **前端**: 纯 HTML + inline CSS + vanilla JS，TradeOgre 用紫色主题区分于 SafeTrade 的蓝色
- **后端**: GitHub Actions + Python（urllib 标准库，零 pip 依赖）
- **缓存**: `tradeogre_cache.json` 通过 GHA actions/cache 持久化（key: `tradeogre-cache`），前端 fetch 追加 `?t=Date.now()` 防浏览器缓存
- **fetch.py 双重角色**: 既是 cron 抓取脚本，也是本地构建脚本。运行后复制 `src/*.html` 到 `_site/` 并写入 `coins.json`
- **时间处理**: `coins.json` 的 `updated` 字段使用 UTC+8（北京时间）；JS 中 `isRecent()` 判断上线是否 <=14 天

## 关键函数

- `fetch.py:fetch_json()` — GET 请求 API，检查 content-type 和首字符是否为 `[` / `{` 以防被 CDN 拦截返回 HTML
- `fetch.py:process_tradeogre()` — 抓取 TradeOgre 全市场，与缓存差集对比发现新币对，用 `initialprice` 算总涨跌幅
- `index.html:fmtNum()` — 数字格式化：>=1M 显示 M、>=1K 显示 K、<0.001 显示 8 位、<1 显示 6 位、其他 2 位小数
- `index.html:isRecent(dateStr)` — 判断上线日期是否在 14 天内，用于展示 NEW 标签
- `index.html:loadData()` — 每 300 秒轮询 `coins.json`，同时渲染 SafeTrade 和 TradeOgre 区域
- `index.html:renderTradeOgre(data)` — 渲染 TradeOgre 币对卡片，API 不可达时显示提示文字

## 注意事项

- **币数量**: `fetch.py` 中 `[:6]` 硬编码上限，修改需同时更新 HTML 中的 `data.coins.length` 展示
- **联系方式**: 微信 `wty_01_01`、QQ群 `928023037` 在 `index.html` 中多处硬编码，全局搜索修改
- **tutorial.html**: 完全独立的静态页面，从 `index.html` 底部链接跳转，修改需同步更新两个文件
- **API 安全**: `fetch_json()` 对异常和空响应做了防御处理（return None），调用方有兜底逻辑
- **GitHub Actions**: 工作流在 `push` 到 `main` 和 schedule `*/5 * * * *` 时触发，注意 Pages 部署有 concurrency 限制（同一时间只运行一个）
