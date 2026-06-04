# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SafeTrade 新币监控 + PRL 挖矿教程的静态网页。每 5 分钟通过 GitHub Actions 抓取 SafeTrade 最新上线币对行情，部署到 GitHub Pages。

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

## Architecture Notes

- **数据流**: SafeTrade public API → GitHub Actions (cron 5min) → `_site/coins.json` → 浏览器 JS fetch 渲染
- **前端**: 纯 HTML + inline CSS + vanilla JS（无框架、无构建工具、无 npm 依赖）
- **后端**: GitHub Actions + Python（urllib 标准库，零 pip 依赖）
- **缓存**: 前端 fetch URL 追加 `?t=Date.now()` 防浏览器缓存；GitHub Pages 默认 CDN 缓存 10 分钟
- **fetch.py 双重角色**: 既是 cron 抓取脚本，也是本地构建脚本。运行后复制 `src/*.html` 到 `_site/` 并写入 `coins.json`
- **时间处理**: `coins.json` 的 `updated` 字段使用 UTC+8（北京时间）；JS 中 `isRecent()` 判断上线是否 <=14 天

## 关键函数

- `fetch.py:fetch_json()` — GET 请求 API，检查 content-type 和首字符是否为 `[` / `{` 以防被 CDN 拦截返回 HTML
- `index.html:fmtNum()` — 数字格式化：>=1M 显示 M、>=1K 显示 K、<0.001 显示 8 位、<1 显示 6 位、其他 2 位小数
- `index.html:isRecent(dateStr)` — 判断上线日期是否在 14 天内，用于展示 NEW 标签
- `index.html:loadData()` — 每 300 秒轮询 `coins.json`，catch 网络错误展示错误提示

## 注意事项

- **币数量**: `fetch.py` 中 `[:6]` 硬编码上限，修改需同时更新 HTML 中的 `data.coins.length` 展示
- **联系方式**: 微信 `wty_01_01`、QQ群 `928023037` 在 `index.html` 中多处硬编码，全局搜索修改
- **tutorial.html**: 完全独立的静态页面，从 `index.html` 底部链接跳转，修改需同步更新两个文件
- **API 安全**: `fetch_json()` 对异常和空响应做了防御处理（return None），调用方有兜底逻辑
- **GitHub Actions**: 工作流在 `push` 到 `main` 和 schedule `*/5 * * * *` 时触发，注意 Pages 部署有 concurrency 限制（同一时间只运行一个）
