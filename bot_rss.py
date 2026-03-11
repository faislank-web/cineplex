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
            # Mengikuti Header dari CURL yang kamu berikan
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
                "Referer": "https://m.21cineplex.com/",
                "sec-ch-ua-platform": '"Windows"'
            }
            
            print(f"Mencoba download gambar: {image_url}")
            img_res = requests.get(image_url, headers=headers, timeout=30)
            
            if img_res.status_code == 200:
                photo = BytesIO(img_res.content)
                photo.name = 'poster.jpg'
                
                url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
                files = {'photo': photo}
                payload = {
                    "chat_id": CHAT_ID,
                    "caption": caption,
                    "parse_mode": "Markdown",
                    "reply_markup": keyboard
                }
                r = requests.post(url, files=files, data=payload)
                if r.json().get("ok"):
                    return r.json()
                print(f"Telegram Reject: {r.json()}")
        except Exception as e:
            print(f"Error proses gambar: {e}")

    # Cadangan Teks
    url_msg = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    return requests.post(url_msg, data={
        "chat_id": CHAT_ID,
        "text": caption,
        "parse_mode": "Markdown",
        "reply_markup": keyboard
    }).json()

def run():
    print("Mengecek RSS...")
    feed = feedparser.parse(RSS_URL)
    if not feed.entries: return

    last_link = ""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            last_link = f.read().strip()

    for entry in feed.entries[:3][::-1]:
        if entry.link != last_link:
            print(f"Memproses: {entry.title}")
            
            description = entry.description or ""
            # Mencari src di deskripsi
            img_match = re.search(r'src="([^"]+)"', description)
            image_url = ""
            
            if img_match:
                image_url = img_match.group(1)
                # LOGIKA BARU: Jika link gambar mengandung media.cinema21.co.id
                # Kita pastikan mengarah ke server NEO ID seperti curl kamu
                if "media.cinema21.co.id" in image_url:
                    if image_url.startswith('//'):
                        image_url = "https:" + image_url
                    # Replace domain jika perlu agar sesuai curl
                    image_url = image_url.replace("https://media.cinema21.co.id", "https://nos.jkt-1.neo.id/media.cinema21.co.id")
                elif image_url.startswith('/'):
                    image_url = f"https://nos.jkt-1.neo.id/media.cinema21.co.id{image_url}"

            caption = f"🎬 **{entry.title}**"
            res = send_telegram(caption, image_url)
            
            if res.get("ok"):
                with open(DB_FILE, "w") as f:
                    f.write(entry.link)
                last_link = entry.link

if __name__ == "__main__":
    run()
