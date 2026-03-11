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
            # Gunakan header lengkap agar diizinkan download oleh server Neo ID
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://m.21cineplex.com/"
            }
            
            print(f"Mencoba download gambar unik: {image_url}")
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
        except Exception as e:
            print(f"Error: {e}")

    # Cadangan pesan teks
    url_msg = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    return requests.post(url_msg, data={
        "chat_id": CHAT_ID,
        "text": caption,
        "parse_mode": "Markdown",
        "reply_markup": keyboard
    }).json()

def run():
    feed = feedparser.parse(RSS_URL)
    if not feed.entries: return

    last_link = ""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            last_link = f.read().strip()

    # Cek entri dari yang paling lama ke baru
    for entry in feed.entries[:5][::-1]:
        if entry.link != last_link:
            print(f"Memproses judul: {entry.title}")
            
            # 1. AMBIL URL GAMBAR DARI DESKRIPSI (Sesuai Pola Judul)
            description = entry.description or ""
            # Mencari src=".../movie-images/XXXX.jpg"
            all_images = re.findall(r'src="([^"]+)"', description)
            
            image_url = ""
            if all_images:
                # Cari gambar pertama yang bukan .svg
                for img in all_images:
                    if not img.lower().endswith('.svg'):
                        image_url = img
                        break
            
            # 2. UBAH DOMAIN KE NEO ID (Agar tidak diblokir)
            if image_url:
                # Ambil hanya bagian path setelah domain atau pastikan domainnya benar
                # Jika link mengandung cinema21 atau dimulai dengan /, kita arahkan ke Neo ID
                if "media.cinema21.co.id" in image_url:
                    path = image_url.split("media.cinema21.co.id")[-1]
                    image_url = f"https://nos.jkt-1.neo.id/media.cinema21.co.id{path}"
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
