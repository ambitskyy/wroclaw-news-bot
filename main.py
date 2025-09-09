import asyncio
import json
import os
from datetime import datetime, timedelta
from utils.rss_reader import get_all_news
from utils.telegram_bot import send_post
from telegram import Bot
from deep_translator import GoogleTranslator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

TELEGRAM_TOKEN = "7668443459:AAHjZXC3HSU5aqWEwCC9wK5dYCcNRgCVB74"
TELEGRAM_CHAT_ID = "-1002153990851"  # заміни на свій

STATE_FILE = "state.json"

def load_sent_links():
    if not os.path.exists(STATE_FILE):
        return []
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_sent_links(sent_links):
    with open(STATE_FILE, "w") as f:
        json.dump(sent_links, f, indent=2)

def cleanup_old_links(sent_links):
    three_days_ago = datetime.now() - timedelta(days=3)
    fresh = []
    for item in sent_links:
        try:
            link_date = datetime.strptime(item["date"], "%Y-%m-%d")
            if link_date >= three_days_ago:
                fresh.append(item)
        except Exception as e:
            logger.warning(f"❗ Помилка дати: {e}")
    return fresh

def is_already_sent(sent_links, link):
    return any(item["link"] == link for item in sent_links)

async def main():
    logger.info("🔄 Початок перевірки новин...")

    sources = [ 
        "https://www.wroclaw.pl/ua/rss",
        "https://wroclawskiefakty.pl/feed/",
        "https://www.wroclaw.pl/rss/komunikacja",
        "https://www.wroclaw.pl/rss/dla-mieszkanca",
        "https://www.wroclaw.pl/rss/kultura",
        "https://www.wroclaw.pl/rss/nauka",
        "https://www.wroclaw.pl/rss/sport",
        "https://www.wroclaw.pl/rss/biznes",
        "https://www.wroclaw.pl/rss/turystyka",
        "https://www.radiowroclaw.pl/rss",
        "https://wroclaw.naszemiasto.pl/rss",
        "https://gazetawroclawska.pl/rss",
        "https://tuwroclaw.com/rss.xml",
        "https://www.wroclaw112.pl/feed/",
        "https://wroclaw.eska.pl/rss.xml"
    ]
    
    bot = Bot(token=TELEGRAM_TOKEN)
    logger.info(f"🔗 Завантаження новин з {len(sources)} джерел...")

    news_items = get_all_news(sources)
    logger.info(f"📥 Отримано {len(news_items)} новин")

    news_items.sort(key=lambda x: x.get("published", datetime.min), reverse=True)

    sent_links = load_sent_links()
    sent_links = cleanup_old_links(sent_links)
    logger.info(f"📦 Вже надіслано {len(sent_links)} новин за останні 3 дні")

    for item in news_items:
        link = item.get('link')
        if link and not is_already_sent(sent_links, link):
            try:
                item['title'] = GoogleTranslator(source='auto', target='uk').translate(item['title'])
                item['summary'] = GoogleTranslator(source='auto', target='uk').translate(item['summary'])
                logger.info(f"🌍 Перекладено: {item['title']}")
            except Exception as e:
                logger.warning(f"⚠️ Помилка перекладу: {e}")
            
            logger.info(f"🚀 Надсилаємо новину: {item['title']}")
            await send_post(bot, TELEGRAM_CHAT_ID, item)
            sent_links.append({
                "link": link,
                "date": datetime.now().strftime("%Y-%m-%d")
            })
            save_sent_links(sent_links)
            logger.info("✅ Найсвіжіша новина надіслана")
            break
    else:
        logger.info("ℹ️ Нових новин немає")

async def loop_forever():
    while True:
        await main()
        await asyncio.sleep(1800)  # кожні 30 хв

if __name__ == "__main__":
    asyncio.run(loop_forever())
