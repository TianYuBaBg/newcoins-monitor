"""定时抓取 SafeTrade 新币数据，生成 _site/coins.json + _site/index.html"""

import json
import os
import shutil
import time
import urllib.request

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "_site")
SRC_DIR = os.path.dirname(os.path.abspath(__file__))

SAFETRADE_MARKETS = "https://safe.trade/api/v2/trade/public/markets"
SAFETRADE_TICKERS = "https://safe.trade/api/v2/trade/public/tickers"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"


def fetch_json(url: str):
    """GET JSON from SafeTrade public API, return None if blocked or error."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            ct = resp.headers.get("content-type", "")
            body = resp.read().decode()
            if "text/html" in ct or not body.strip().startswith(("[", "{")):
                return None
            return json.loads(body)
    except Exception:
        return None


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    markets = fetch_json(SAFETRADE_MARKETS)
    tickers = fetch_json(SAFETRADE_TICKERS)

    coins = []
    if markets and tickers:
        enabled = [m for m in markets if m.get("state") == "enabled"]
        enabled.sort(key=lambda m: m.get("created_at", ""), reverse=True)
        for m in enabled[:6]:
            name = m.get("name", "")
            key = (m.get("base_unit", "") + m.get("quote_unit", "")).lower()
            t = tickers.get(key, {})
            coins.append({
                "name": name,
                "base": m.get("base_unit", ""),
                "quote": m.get("quote_unit", ""),
                "created_at": m.get("created_at", ""),
                "last": t.get("last", "—"),
                "change": t.get("price_change_percent", "—"),
                "volume": t.get("volume", "—"),
                "high": t.get("high", "—"),
                "low": t.get("low", "—"),
            })

    data = {
        "coins": coins,
        "updated": time.strftime(
            "%Y-%m-%d %H:%M:%S",
            time.localtime(time.time() + 8 * 3600),  # UTC+8
        ),
    }

    path_coins = os.path.join(OUTPUT_DIR, "coins.json")
    with open(path_coins, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    path_src_html = os.path.join(SRC_DIR, "index.html")
    path_dst_html = os.path.join(OUTPUT_DIR, "index.html")
    if os.path.exists(path_src_html):
        shutil.copy2(path_src_html, path_dst_html)

    path_src_tutorial = os.path.join(SRC_DIR, "tutorial.html")
    path_dst_tutorial = os.path.join(OUTPUT_DIR, "tutorial.html")
    if os.path.exists(path_src_tutorial):
        shutil.copy2(path_src_tutorial, path_dst_tutorial)

    count = len(coins)
    print(f"[OK] {count} coins -> {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
