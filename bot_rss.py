import requests
import feedparser
from bs4 import BeautifulSoup
import os
import json
from io import BytesIO

# ================= KONFIGURASI AMAN =================
# Mengambil Token & API Key dari GitHub Secrets
TOKEN = os.getenv("TELEGRAM_TOKEN")
TMDB_KEY = os.getenv("TMDB_KEY")

RSS_NOW_PLAYING = "https://politepol.com/fd/KQAvZFImsXrT.xml"
URL_UPCOMING = "https://m.21cineplex.com/gui.coming_soon.php?order=2"
DB_FILE = "last_link.txt"

# --- PENGATURAN KHUSUS TIAP GRUP ---
GRUP_CONFIG = {
    "-1003839747899": {
        "footer": "@SheJua",
        "buttons": [
            [{"text": "🎬 Cek Disini", "url": "https://t.me/+w6XDg0Ap0yhlY2I9"}],
            [{"text": "📞 Hub. Admin", "url": "https://t.me/ksrfsj_bot"}]
        ]
    },
    "-1002981455085": {
        "footer": "@nontonbarengFM",
        "buttons": [
            [{"text": "🎬 Cek Disini", "url": "https://t.me/+EAx1zAJZL9IzZDdl"}]
        ]
    }
}
# ===============================================

def get_tmdb_data(title):
    try:
        if not TMDB_KEY: return None
        clean_title = title.split(' (')[0].split(' - ')[0].replace('PRE-SALE', '').strip()
        search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_KEY}&query={clean_title}&language=id-ID"
        res = requests.get(search_url).json()
        if res.get('results'):
            movie = res['results'][0]
            movie_id = movie['id']
            detail_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_KEY}&language=id-ID&append_to_response=videos"
            details = requests.get(detail_url).json()
            
            return {
                "rating": f"{details.get('vote_average', 0):.1f}",
                "genre": ", ".join([g['name'] for g in details.get('genres', [])]) or "Movie",
                "synopsis": details.get('overview', 'Sinopsis belum tersedia.'),
                "trailer": next((f"https://www.youtube.com/watch?v={v['key']}" for v in details.get('videos', {}).get('results', []) if v['type'] == 'Trailer'), "")
            }
    except: pass
    return None

def send_telegram(template_caption, image_url):
    if not TOKEN:
        print("❌ Error: TELEGRAM_TOKEN tidak ditemukan di Environment!")
        return {"ok": False}
        
    headers = {"User-Agent": "Mozilla/5.0"}
    status_ok = False
    
    photo_data = None
    if image_url:
        try:
            img_res = requests.get(image_url, headers=headers, timeout=30)
            if img_res.status_code == 200:
                photo_data = img_res.content
        except: pass

    for chat_id, config in GRUP_CONFIG.items():
        caption = template_caption + f"\n\n➖➖➖➖➖➖➖➖➖➖\n📢 {config['footer']}"
        keyboard = json.dumps({"inline_keyboard": config['buttons']})
        
        try:
            if photo_data:
                photo = BytesIO(photo_data)
                photo.name = 'poster.jpg'
                res = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", 
                                    files={'photo': photo}, 
                                    data={"chat_id": chat_id, "caption": caption, "parse_mode": "Markdown", "reply_markup": keyboard}).json()
            else:
                res = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                                    data={"chat_id": chat_id, "text": caption, "parse_mode": "Markdown", "reply_markup": keyboard}).json()
            if res.get("ok"): status_ok = True
        except: pass
            
    return {"ok": status_ok}

def run():
    print("🚀 Memulai pengecekan film baru...")
    history = []
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            history = f.read().splitlines()

    new_entries = []

    # --- NOW PLAYING ---
    feed = feedparser.parse(RSS_NOW_PLAYING)
    for entry in feed.entries[:5][::-1]:
        if entry.link not in history:
            tmdb = get_tmdb_data(entry.title)
            cap = f"🔥 **NOW PLAYING UPDATE**\n\n🎬 **{entry.title.upper()}**\n"
            if tmdb:
                cap += f"⭐️ **Rating:** {tmdb['rating']}/10\n🎭 **Genre:** {tmdb['genre']}\n\n📖 **Sinopsis:**\n_{tmdb['synopsis'][:250]}..._\n"
                if tmdb['trailer']: cap += f"\n📺 **Trailer:** [Klik Disini]({tmdb['trailer']})"
            
            img = entry.enclosures[0].get('url', '') if 'enclosures' in entry else ""
            if send_telegram(cap, img).get("ok"):
                history.append(entry.link)
                new_entries.append(entry.link)

    # --- UPCOMING ---
    try:
        res = requests.get(URL_UPCOMING, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, 'html.parser')
        for item in soup.find_all('div', class_='grid_movie'):
            title_tag = item.find('div', class_='title')
            link_tag = item.find('a')
            if title_tag and link_tag:
                title = title_tag.text.strip()
                link = "https://m.21cineplex.com/" + link_tag.get('href')
                if link not in history:
                    tmdb = get_tmdb_data(title)
                    cap = f"🔥 **UPCOMING UPDATE**\n\n🎬 **{title.upper()}**\n"
                    if tmdb:
                        cap += f"⭐️ **Rating:** {tmdb['rating']}/10\n🎭 **Genre:** {tmdb['genre']}\n\n📖 **Sinopsis:**\n_{tmdb['synopsis'][:250]}..._\n"
                    
                    img_tag = item.find('img')
                    img_url = img_tag.get('src') if img_tag else ""
                    if send_telegram(cap, img_url).get("ok"):
                        history.append(link)
                        new_entries.append(link)
    except: pass

    if new_entries:
        with open(DB_FILE, "w") as f:
            f.write("\n".join(history))
        print(f"✅ Selesai! Berhasil update {len(new_entries)} film baru.")
    else:
        print("ℹ️ Tidak ada film baru saat ini.")

if __name__ == "__main__":
    run()
