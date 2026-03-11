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
    # Coba kirim sebagai Foto dulu
    url_photo = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    keyboard = json.dumps({
        "inline_keyboard": [
            [{"text": "🎬 Cek Disini", "url": "https://t.me/+w6XDg0Ap0yhlY2I9"}],
            [{"text": "📞 Hub. Admin", "url": "https://t.me/ksrfsj_bot"}]
        ]
    })
    
    payload = {
        "chat_id": CHAT_ID,
        "caption": caption,
        "parse_mode": "Markdown",
        "reply_markup": keyboard
    }

    try:
        # Jika ada image_url, coba kirim fotonya
        if image_url:
            r = requests.post(url_photo, data={**payload, "photo": image_url}, timeout=20)
            res = r.json()
            if res.get("ok"):
                return res
        
        # JIKA GAGAL kirim foto (atau link gambar rusak), kirim sebagai TEXT saja
        print("Gagal kirim foto atau gambar rusak, mencoba kirim teks saja...")
        url_msg = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        r_text = requests.post(url_msg, data={
            "chat_id": CHAT_ID,
            "text": caption,
            "parse_mode": "Markdown",
            "reply_markup": keyboard
        })
        return r_text.json()
        
    except Exception as e:
        print(f"Error: {e}")
        return None

def run():
    print("Mengecek koneksi RSS...")
    feed = feedparser.parse(RSS_URL)
    
    if not feed.entries:
        print("RSS Kosong.")
        return

    last_link = ""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            last_link = f.read().strip()

    latest_entry = feed.entries[0]
    
    if not last_link or latest_entry.link != last_link:
        print(f"Memproses postingan: {latest_entry.title}")
        
        # Ekstrak Gambar
        all_images = re.findall(r'src="([^"]+)"', latest_entry.description)
        image_url = ""
        for img in all_images:
            if not img.endswith('.svg'):
                image_url = img
                break
        
        if image_url and image_url.startswith('/'):
            image_url = f"https://m.21cineplex.com{image_url}"
        
        caption = f"🎬 **{latest_entry.title}**"
        
        res = send_telegram(caption, image_url)
        print(f"Respon Akhir Telegram: {res}")
        
        if res and res.get("ok"):
            with open(DB_FILE, "w") as f:
                f.write(latest_entry.link)
    else:
        print("Tidak ada update baru.")

if __name__ == "__main__":
    run()
