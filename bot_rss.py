import feedparser
import requests
import re
import os
import json
from io import BytesIO

# ================= KONFIGURASI =================
RSS_URL = "https://politepaul.com/fd/KQAvZFImsXrT.xml"
TOKEN = "8479247479:AAE-9m6EniTIXfCIFssE294v04EulVgpg1M"
CHAT_ID = "-1003839747899"
DB_FILE = "last_link.txt"
# ===============================================

def send_telegram(caption, image_url):
    keyboard = json.dumps({
        "inline_keyboard": [
            [{"text": "🎬 Cek Disini", "url": "https://t.me/+w6XDg0Ap0yhlY2I9"}],
            [{"text": "📞 Hub. Admin", "url": "https://t.me/ksrfsj_bot"}]
        ]
    })

    if image_url:
        try:
            # Unduh gambar ke memori (mirip cara Pipedream memproses event)
            img_data = requests.get(image_url, timeout=20, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            if img_data.status_code == 200:
                photo = BytesIO(img_data.content)
                photo.name = 'poster.jpg'
                
                url_photo = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
                files = {'photo': photo}
                data = {
                    "chat_id": CHAT_ID,
                    "caption": caption,
                    "parse_mode": "Markdown",
                    "reply_markup": keyboard
                }
                r = requests.post(url_photo, files=files, data=data)
                res = r.json()
                if res.get("ok"):
                    return res
        except Exception as e:
            print(f"Gagal unduh/kirim gambar: {e}")

    # Cadangan: Kirim Teks jika gambar tetap gagal
    url_msg = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    r_text = requests.post(url_msg, data={
        "chat_id": CHAT_ID,
        "text": caption,
        "parse_mode": "Markdown",
        "reply_markup": keyboard
    })
    return r_text.json()

def run():
    print("Mengecek RSS...")
    feed = feedparser.parse(RSS_URL)
    if not feed.entries: return

    last_link = ""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            last_link = f.read().strip()

    # Ambil 5 entri terakhir untuk dicek (agar tidak terlewat)
    entries = feed.entries[:5][::-1]

    for entry in entries:
        if entry.link != last_link:
            print(f"Memproses: {entry.title}")
            
            # Cari gambar dengan pola yang lebih luas (seperti Pipedream)
            image_url = ""
            img_match = re.search(r'src="([^"]+)"', entry.description)
            if img_match:
                image_url = img_match.group(1)
                if image_url.startswith('/'):
                    image_url = f"https://m.21cineplex.com{image_url}"

            caption = f"🎬 **{entry.title}**"
            res = send_telegram(caption, image_url)
            
            if res and res.get("ok"):
                last_link = entry.link
                with open(DB_FILE, "w") as f:
                    f.write(last_link)
    
if __name__ == "__main__":
    run()
