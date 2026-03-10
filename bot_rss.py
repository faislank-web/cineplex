import feedparser
import requests
import re
import os
import json

# ================= KONFIGURASI =================
RSS_URL = "https://politepaul.com/fd/KQAvZFImsXrT.xml"
TOKEN = "8479247479:AAE-9m6EniTIXfCIFssE294v04EulVgpg1M"
CHAT_ID = "-1003839747899"
DB_FILE = "last_link.txt"
# ===============================================

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
        r = requests.post(url, data=payload, timeout=20)
        return r.json()
    except Exception as e:
        print(f"Error Request: {e}")
        return None

def run():
    print("Mulai mengecek RSS...")
    feed = feedparser.parse(RSS_URL)
    
    if not feed.entries:
        print("RSS Kosong atau Gagal Diakses.")
        return

    # Baca link terakhir
    last_link = ""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            last_link = f.read().strip()
    else:
        # Jika file belum ada, buat file kosong agar git tidak error nanti
        with open(DB_FILE, "w") as f:
            f.write("")

    # Ambil postingan terbaru (paling atas di RSS)
    latest_entry = feed.entries[0]
    
    # JIKA LINK BARU != LINK TERAKHIR, MAKA KIRIM
    if latest_entry.link != last_link:
        print(f"Update ditemukan: {latest_entry.title}")
        
        # Logika Gambar (Cari yang bukan .svg)
        all_images = re.findall(r'src="([^"]+)"', latest_entry.description)
        image_url = ""
        for img in all_images:
            if not img.endswith('.svg'):
                image_url = img
                break
        
        # Lengkapi URL jika relatif
        if image_url and image_url.startswith('/'):
            image_url = f"https://m.21cineplex.com{image_url}"

        # Jika gambar tidak ketemu, pakai logo Cineplex sebagai cadangan
        if not image_url:
            image_url = "https://m.21cineplex.com/images/logo.png"

        caption = f"🎬 **{latest_entry.title}**"
        
        # Kirim ke Telegram
        res = send_telegram(caption, image_url)
        
        if res and res.get("ok"):
            print("Berhasil terkirim ke Telegram.")
            # Update file last_link.txt
            with open(DB_FILE, "w") as f:
                f.write(latest_entry.link)
        else:
            print(f"Gagal kirim: {res}")
    else:
        print("Tidak ada update baru. Link masih sama dengan sebelumnya.")

if __name__ == "__main__":
    run()
