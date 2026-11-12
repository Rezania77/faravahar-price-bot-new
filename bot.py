import os
import json
import requests
from pathlib import Path

BOT_TOKEN = os.environ["BOT_TOKEN"]
BALE_BOT_TOKEN = os.environ["BALE_BOT_TOKEN"]

TELEGRAM_CHANNEL = "@FaravaharCoin"
BALE_CHANNEL = "@faravaharcoin"

API_URL = "https://raw.githubusercontent.com/iran-market/iran-market.github.io/main/data/latest-toman.json"

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
BALE_URL = f"https://tapi.bale.ai/bot{BALE_BOT_TOKEN}/sendMessage"

STATE_FILE = Path("previous_prices.json")

SYMBOLS = {
    "GOLD_18K_IRR": "طلای ۱۸ عیار (هر گرم)",
    "COIN_EMAMI_IRR": "تمام سکه",
    "COIN_HALF_IRR": "نیم‌ سکه",
    "COIN_QUARTER_IRR": "ربع‌ سکه",
    "USD_IRR_FREE": "دلار آزاد",
}

def get_prices():
    response = requests.get(API_URL, timeout=30)
    response.raise_for_status()
    payload = response.json()

    categories = payload["data"]["categories"]
    prices = {}

    required_symbols = {
        "GOLD_18K_IRR",
        "COIN_EMAMI_IRR",
        "COIN_HALF_IRR",
        "COIN_QUARTER_IRR",
        "USD_IRR_FREE",
    }

    for items in categories.values():
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict) and item.get("symbol") in required_symbols:
                    prices[item["symbol"]] = item

    missing = required_symbols - prices.keys()
    if missing:
        raise ValueError(f"Missing price data: {', '.join(sorted(missing))}")

    for symbol, item in prices.items():
        if item.get("stale") is True:
            raise ValueError(f"Stale price data: {symbol}")

        if not item.get("timestamp"):
            raise ValueError(f"Missing timestamp: {symbol}")

    return prices

def to_toman(item):
    price = float(item["price"])
    currency = item.get("currency", "")

    if currency == "IRR":
        price /= 10

    return int(price)

def send_message(url, channel, message):
    response = requests.post(
        url,
        json={
            "chat_id": channel,
            "text": message,
            "disable_web_page_preview": True
        },
        timeout=30
    )
    response.raise_for_status()

    result = response.json()
    if not result.get("ok"):
        raise RuntimeError(str(result))

def main():
    previous = {}

    if STATE_FILE.exists():
        previous = json.loads(STATE_FILE.read_text())

    prices = get_prices()
    current = {}
    lines = ["📊 قیمت طلا، سکه و دلار", ""]

    for symbol, title in SYMBOLS.items():
        item = prices.get(symbol)

        if not item or item.get("price") is None:
            raise ValueError(f"قیمت {symbol} موجود نیست")

        value = to_toman(item)
        current[symbol] = value

        old = previous.get(symbol)

        if old is None or value == old:
            arrow = "➖"
        elif value > old:
            arrow = "🔺"
        else:
            arrow = "🔻"

        lines.append(f"{arrow} {title}: {value:,} تومان")

    lines += [
        "",
        "⚠️ قیمت‌ها تقریبی‌اند و ممکن است با بازار تفاوت داشته باشند.",
        "جهت استعلام دقیق قیمت و مشاوره با شماره 09129572767 تماس بگیرید."
    ]

    message = "\n".join(lines)

    send_message(TELEGRAM_URL, TELEGRAM_CHANNEL, message)
    print("Telegram message sent")

    send_message(BALE_URL, BALE_CHANNEL, message)
    print("Bale message sent")

    STATE_FILE.write_text(
        json.dumps(current, ensure_ascii=False, indent=2)
    )

    print("Published successfully")

if __name__ == "__main__":
    main()
