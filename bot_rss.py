import feedparser
import requests
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
            # Sesuai data XML kamu, ini link Direct Neo ID
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://m.21cineplex.com/"
            }
            
            print(f"Mengunduh gambar dari enclosure: {image_url}")
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
                print(f"Telegram menolak: {r.json()}")
        except Exception as e:
            print(f"Error download gambar: {e}")

    # Cadangan pesan teks
    url_msg = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    return requests.post(url_msg, data={
        "chat_id": CHAT_ID,
        "text": caption,
        "parse_mode": "Markdown",
        "reply_markup": keyboard
    }).json()

def run():
    print("Membaca RSS PolitePol...")
    # Paksa feedparser untuk membaca semua tag termasuk enclosure
    feed = feedparser.parse(RSS_URL)
    if not feed.entries:
        print("RSS Kosong.")
        return

    last_link = ""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            last_link = f.read().strip()

    # Proses dari entri lama ke baru (max 5 terbaru)
    for entry in feed.entries[:5][::-1]:
        if entry.link != last_link:
            print(f"Memproses film: {entry.title}")
            
            # AMBIL GAMBAR DARI TAG ENCLOSURE (Ini kunci suksesnya!)
            image_url = ""
            if 'enclosures' in entry and len(entry.enclosures) > 0:
                # Mengambil atribut 'url' dari tag <enclosure>
                image_url = entry.enclosures[0].get('url', '')
            
            # Jika enclosure kosong, baru cari alternatif (tapi di XML kamu ini pasti ada)
            if not image_url and 'links' in entry:
                for link in entry.links:
                    if link.get('rel') == 'enclosure':
                        image_url = link.get('href', '')

            caption = f"🎬 **{entry.title}**"
            res = send_telegram(caption, image_url)
            
            if res.get("ok"):
                with open(DB_FILE, "w") as f:
                    f.write(entry.link)
                last_link = entry.link
                print(f"Berhasil mengirim {entry.title}")

if __name__ == "__main__":
    run()
