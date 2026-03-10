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
    print("Mengecek koneksi RSS...")
    feed = feedparser.parse(RSS_URL)
    
    if not feed.entries:
        print("RSS Kosong. Mencoba kirim pesan tes ke Telegram...")
        send_telegram("⚠️ Bot Berhasil Jalan tapi RSS Kosong!", "https://m.21cineplex.com/images/logo.png")
        return

    # Baca link terakhir
    last_link = ""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            last_link = f.read().strip()

    # Ambil entri terbaru
    latest_entry = feed.entries[0]
    
    # PAKSA KIRIM jika last_link kosong (biar ketahuan botnya jalan)
    if not last_link or latest_entry.link != last_link:
        print(f"Mengirim postingan terbaru: {latest_entry.title}")
        
        # Ekstrak Gambar
        all_images = re.findall(r'src="([^"]+)"', latest_entry.description)
        image_url = ""
        for img in all_images:
            if not img.endswith('.svg'):
                image_url = img
                break
        
        if image_url and image_url.startswith('/'):
            image_url = f"https://m.21cineplex.com{image_url}"
        
        if not image_url:
            image_url = "https://m.21cineplex.com/images/logo.png"

        caption = f"🎬 **{latest_entry.title}**"
        
        res = send_telegram(caption, image_url)
        print(f"Respon Telegram: {res}")
        
        if res and res.get("ok"):
            with open(DB_FILE, "w") as f:
                f.write(latest_entry.link)
        else:
            print("Gagal mengirim! Cek apakah Bot sudah jadi ADMIN di channel.")
    else:
        print("Sudah update (link sama). Tidak ada yang dikirim.")

if __name__ == "__main__":
    run()
