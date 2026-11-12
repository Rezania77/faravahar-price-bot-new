
import requests
import json
from datetime import datetime
from pathlib import Path

TELEGRAM_TOKEN = __import__("os").environ["BOT_TOKEN"]
BALE_TOKEN = __import__("os").environ["BALE_BOT_TOKEN"]

TELEGRAM_CHANNEL = "@FaravaharCoin"
BALE_CHANNEL = "@faravaharcoin"

API_URL = "https://raw.githubusercontent.com/iran-market/iran-market.github.io/main/data/popular.json"

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
    return {
        item["symbol"]: item
        for item in payload["data"]
    }

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

        value = int(float(item["price"]))
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

    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    bale_url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/sendMessage"

    send_message(telegram_url, TELEGRAM_CHANNEL, message)
    print("Telegram message sent")

    send_message(bale_url, BALE_CHANNEL, message)
    print("Bale message sent")

    STATE_FILE.write_text(
        json.dumps(current, ensure_ascii=False, indent=2)
    )

    print("Published successfully")

if __name__ == "__main__":
    main()
