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
            # TEKNIK KHUSUS: Download dulu gambarnya ke server GitHub
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://m.21cineplex.com/"
            }
            img_data = requests.get(image_url, headers=headers, timeout=30)
            
            if img_data.status_code == 200:
                # Bungkus gambar jadi file virtual
                photo = BytesIO(img_data.content)
                photo.name = 'poster.jpg'
                
                # Kirim ke Telegram sebagai FILE (bukan link)
                url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
                files = {'photo': photo}
                data = {
                    "chat_id": CHAT_ID,
                    "caption": caption,
                    "parse_mode": "Markdown",
                    "reply_markup": keyboard
                }
                r = requests.post(url, files=files, data=data)
                res = r.json()
                if res.get("ok"):
                    return res
        except Exception as e:
            print(f"Gagal proses gambar: {e}")

    # CADANGAN: Jika gambar gagal total, kirim teks saja agar bot tidak mati
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

    # Kita cek 3 entri terbaru (seperti Event di Pipedream)
    for entry in feed.entries[:3][::-1]:
        if entry.link != last_link:
            print(f"Memproses: {entry.title}")
            
            # Cari gambar (Logika Pipedream: Cari src yang bukan .svg)
            all_images = re.findall(r'src="([^"]+)"', entry.description or "")
            image_url = ""
            for img in all_images:
                if not img.lower().endswith('.svg'):
                    image_url = img
                    break
            
            if image_url and image_url.startswith('/'):
                image_url = f"https://m.21cineplex.com{image_url}"

            caption = f"🎬 **{entry.title}**"
            res = send_telegram(caption, image_url)
            
            if res.get("ok"):
                with open(DB_FILE, "w") as f:
                    f.write(entry.link)
                last_link = entry.link

if __name__ == "__main__":
    run()
