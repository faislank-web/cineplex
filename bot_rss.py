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
        print(f"Mencoba mengirim gambar: {image_url}")
        try:
            # Gunakan Header agar tidak dianggap bot oleh Cineplex
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://m.21cineplex.com/"
            }
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
                resp = r.json()
                if resp.get("ok"):
                    return resp
                else:
                    print(f"Telegram menolak foto: {resp}")
            else:
                print(f"Gagal download gambar dari Cineplex. Status code: {img_res.status_code}")
        except Exception as e:
            print(f"Error proses gambar: {e}")

    # Cadangan: Kirim Teks jika gambar gagal (seperti hasil yang kamu dapat tadi)
    print("Mengirim pesan teks sebagai cadangan...")
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

    # Cek 3 entri terbaru (proses dari yang terlama ke terbaru)
    for entry in feed.entries[:3][::-1]:
        if entry.link != last_link:
            print(f"Memproses judul: {entry.title}")
            
            # 1. Logika Pipedream: Ambil semua src="xxx"
            description = entry.description or ""
            # regex /src="([^"]+)"/g di Node.js
            all_images = re.findall(r'src="([^"]+)"', description)
            
            image_url = ""
            if all_images:
                # 2. Cari yang bukan .svg
                for img in all_images:
                    if not img.lower().endswith('.svg'):
                        image_url = img
                        break
            
            # 3. Pastikan domain lengkap
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
