# NewCoins Monitor — SafeTrade 新币监控

每 5 分钟自动抓取 SafeTrade 交易所最新上线的币对，展示实时行情。

**在线地址：** https://tianyubabg.github.io/newcoins-monitor/

## 功能

- 自动抓取 SafeTrade 最近上线币对（目前显示 6 个）
- 展示价格、24h 涨跌幅、成交额、最高/最低价
- 上线 14 天内的币对有 `NEW` 标签
- 每 5 分钟通过 GitHub Actions 自动更新数据
- 完全静态部署，无需服务器

## 技术栈

- **数据源：** SafeTrade 公开 API（markets + tickers）
- **抓取脚本：** Python（`urllib`，零外部依赖）
- **自动化：** GitHub Actions（cron `*/5 * * * *`）
- **前端：** 纯 HTML + CSS + JavaScript
- **托管：** GitHub Pages

## 联系方式

QQ群 928023037 · 微信 wty_01_01

## 本地运行

```bash
python src/fetch.py
# 生成 _site/ 目录，直接用浏览器打开 _site/index.html 即可预览
```

## License

MIT
