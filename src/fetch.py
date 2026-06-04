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
TRADE_OGRE_MARKETS = "https://tradeogre.com/api/v1/markets"
CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "tradeogre_cache.json")
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


def process_tradeogre():
    """抓取 TradeOgre 全市场，通过缓存差集找出最新上线币对。"""
    raw = fetch_json(TRADE_OGRE_MARKETS)
    if not raw or not isinstance(raw, list):
        print("[TO] API blocked or empty, skip")
        return []

    # 构建币对 -> 行情字典
    info_map = {}
    for item in raw:
        for name, info in item.items():
            info_map[name] = info

    # 加载已知交易对缓存
    cache = {"pairs": {}}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, encoding="utf-8") as f:
                cache = json.load(f)
        except Exception:
            pass

    now_ts = time.strftime(
        "%Y-%m-%d %H:%M:%S",
        time.localtime(time.time() + 8 * 3600),
    )
    known = cache.get("pairs", {})

    # 记录新出现的交易对
    for name in info_map:
        if name not in known:
            known[name] = now_ts
            print(f"[TO] New pair detected: {name}")

    # 按首次发现时间降序，取前 6
    sorted_pairs = sorted(known.items(), key=lambda x: x[1], reverse=True)

    coins = []
    for name, first_seen in sorted_pairs[:6]:
        info = info_map.get(name, {})
        parts = name.split("-", 1)
        base, quote = parts[0], parts[1] if len(parts) > 1 else ""

        # 用 initialprice 算总涨跌幅
        change = "—"
        initial = info.get("initialprice")
        price = info.get("price")
        if initial and price and initial != "—" and price != "—":
            try:
                ip, p = float(initial), float(price)
                if ip > 0:
                    pct = (p - ip) / ip * 100
                    change = f"{'+' if pct >= 0 else ''}{pct:.2f}%"
            except Exception:
                pass

        coins.append({
            "name": name,
            "base": base,
            "quote": quote,
            "first_seen": first_seen,
            "last": price or "—",
            "change": change,
            "volume": info.get("volume", "—"),
            "high": info.get("high", "—"),
            "low": info.get("low", "—"),
        })

    # 持久化缓存
    cache["pairs"] = known
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)

    print(f"[TO] {len(coins)} newest pairs (cache has {len(known)} total)")
    return coins


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
        "tradeogre": process_tradeogre(),
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
