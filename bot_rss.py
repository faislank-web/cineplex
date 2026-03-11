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
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
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
                print(f"Detail Error Telegram: {r.json()}")
        except Exception as e:
            print(f"Gagal memproses gambar: {e}")

    # Kirim Teks jika gambar gagal/tidak ada
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
    if not feed.entries:
        print("RSS kosong atau tidak bisa diakses.")
        return

    last_link = ""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            last_link = f.read().strip()

    # Kita cek 3 entri terbaru
    for entry in feed.entries[:3][::-1]:
        # Jika link belum pernah dikirim atau kamu ingin paksa kirim ulang (hapus last_link.txt)
        if entry.link != last_link:
            print(f"Mengirim: {entry.title}")
            
            # LOGIKA PINTAR MENCARI GAMBAR (Mencari semua tag src)
            image_url = ""
            # Mencari semua link gambar di deskripsi
            img_links = re.findall(r'src="([^"]+)"', entry.description)
            
            for link in img_links:
                # Ambil gambar pertama yang bukan .svg
                if not link.endswith('.svg'):
                    image_url = link
                    break
            
            # Jika URL relatif, tambahkan domain
            if image_url and image_url.startswith('/'):
                image_url = f"https://m.21cineplex.com{image_url}"

            caption = f"🎬 **{entry.title}**"
            res = send_telegram(caption, image_url)
            
            if res.get("ok"):
                with open(DB_FILE, "w") as f:
                    f.write(entry.link)
                last_link = entry.link
            else:
                print(f"Gagal: {res}")

if __name__ == "__main__":
    run()
