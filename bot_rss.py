import feedparser
import requests
import re
import os
import json

# Konfigurasi Baru
RSS_URL = "https://politepaul.com/fd/KQAvZFImsXrT.xml"
TOKEN = "8479247479:AAE-9m6EniTIXfCIFssE294v04EulVgpg1M"
CHAT_ID = "-1003839747899"
DB_FILE = "last_link.txt"

def send_telegram(caption, image_url):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    payload = {
        "chat_id": CHAT_ID,
        "caption": caption,
        "parse_mode": "Markdown",
        "photo": image_url,
        "reply_markup": json.dumps({
            "inline_keyboard": [
                [{"text": "🎬 Cek Disini", "url": "https://t.me/+w6XDg0Ap0yhlY2I9"}],
                [{"text": "📞 Hub. Admin", "url": "https://t.me/ksrfsj_bot"}]
            ]
        })
    }
    try:
        r = requests.post(url, data=payload)
        return r.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

def run():
    feed = feedparser.parse(RSS_URL)
    last_link = ""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            last_link = f.read().strip()

    entries = feed.entries[::-1]
    new_last_link = last_link

    for entry in entries:
        if entry.link == last_link:
            continue
        
        # Cari gambar poster (bukan .svg)
        all_images = re.findall(r'src="([^"]+)"', entry.description)
        image_url = ""
        for img in all_images:
            if not img.endswith('.svg'):
                image_url = img
                break
        
        if image_url and image_url.startswith('/'):
            image_url = f"https://m.21cineplex.com{image_url}"

        if not image_url:
            continue

        caption = f"🎬 **{entry.title}**"
        print(f"Mengirim: {entry.title}")
        res = send_telegram(caption, image_url)
        
        if res and res.get("ok"):
            new_last_link = entry.link

    if new_last_link != last_link:
        with open(DB_FILE, "w") as f:
            f.write(new_last_link)

if __name__ == "__main__":
    run()
