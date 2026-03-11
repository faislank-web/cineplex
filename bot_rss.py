import requests
import feedparser
from bs4 import BeautifulSoup
import os
import json
from io import BytesIO

# ================= KONFIGURASI =================
# 1. Sumber RSS (PolitePol)
RSS_NOW_PLAYING = "https://politepol.com/fd/KQAvZFImsXrT.xml"

# 2. Sumber Direct Link (Coming Soon)
URL_UPCOMING = "https://m.21cineplex.com/gui.coming_soon.php?order=2"

TOKEN = "8479247479:AAE-9m6EniTIXfCIFssE294v04EulVgpg1M"
CHAT_ID = "-1003839747899"
DB_FILE = "last_link.txt"
TMDB_KEY = "61e2290429798c561450eb56b26de19b"
# ===============================================

def get_tmdb_data(title):
    try:
        clean_title = title.split(' (')[0].split(' - ')[0].replace('PRE-SALE', '').strip()
        search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_KEY}&query={clean_title}&language=id-ID"
        res = requests.get(search_url).json()
        if res.get('results'):
            movie = res['results'][0]
            movie_id = movie['id']
            detail_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_KEY}&language=id-ID&append_to_response=videos"
            details = requests.get(detail_url).json()
            
            genres = ", ".join([g['name'] for g in details.get('genres', [])])
            rating = movie.get('vote_average', '0')
            overview = movie.get('overview', 'Sinopsis belum tersedia.')
            
            trailer_url = ""
            videos = details.get('videos', {}).get('results', [])
            for v in videos:
                if v['type'] == 'Trailer' and v['site'] == 'YouTube':
                    trailer_url = f"https://www.youtube.com/watch?v={v['key']}"
                    break
            
            return {
                "rating": f"{rating:.1f}" if isinstance(rating, float) else rating,
                "genre": genres or "Movie",
                "synopsis": overview if overview else "Sinopsis segera hadir.",
                "trailer": trailer_url
            }
    except: pass
    return None

def send_telegram(caption, image_url):
    keyboard = json.dumps({
        "inline_keyboard": [
            [{"text": "🎬 Cek Disini", "url": "https://t.me/+w6XDg0Ap0yhlY2I9"}],
            [{"text": "📞 Hub. Admin", "url": "https://t.me/ksrfsj_bot"}]
        ]
    })
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        if image_url:
            img_res = requests.get(image_url, headers=headers, timeout=30)
            if img_res.status_code == 200:
                photo = BytesIO(img_res.content)
                photo.name = 'poster.jpg'
                return requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", files={'photo': photo}, data={
                    "chat_id": CHAT_ID, "caption": caption, "parse_mode": "Markdown", "reply_markup": keyboard
                }).json()
    except: pass
    return requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={
        "chat_id": CHAT_ID, "text": caption, "parse_mode": "Markdown", "reply_markup": keyboard
    }).json()

def run():
    print("Memulai pengecekan Multi-Link...")
    history = []
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            history = f.read().splitlines()

    new_entries = []

    # --- PROSES NOW PLAYING (RSS) ---
    print("Mengecek Now Playing...")
    feed = feedparser.parse(RSS_NOW_PLAYING)
    for entry in feed.entries[:5][::-1]:
        if entry.link not in history:
            img = entry.enclosures[0].get('url', '') if 'enclosures' in entry else ""
            tmdb = get_tmdb_data(entry.title)
            caption = f"🔥 **NOW PLAYING UPDATE**\n\n🎬 **{entry.title.upper()}**\n"
            if tmdb:
                caption += f"⭐️ **Rating:** {tmdb['rating']}/10\n🎭 **Genre:** {tmdb['genre']}\n\n📖 **Sinopsis:**\n_{tmdb['synopsis'][:250]}..._\n"
                if tmdb['trailer']: caption += f"\n📺 **Trailer:** [Klik Disini]({tmdb['trailer']})"
            else: caption += "\n🍿 _Detail lengkap segera diperbarui!_"
            caption += "\n\n➖➖➖➖➖➖➖➖➖➖\n📢 @SheJua"
            if send_telegram(caption, img).get("ok"):
                history.append(entry.link)
                new_entries.append(entry.link)

    # --- PROSES UPCOMING (SCRAPING) ---
    print("Mengecek Upcoming...")
    res = requests.get(URL_UPCOMING, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(res.text, 'html.parser')
    for item in soup.find_all('div', class_='grid_movie'):
        title_tag = item.find('div', class_='title')
        link_tag = item.find('a')
        img_tag = item.find('img')
        
        if title_tag and link_tag:
            title = title_tag.text.strip()
            link = "https://m.21cineplex.com/" + link_tag.get('href')
            img_url = img_tag.get('src') if img_tag else ""
            
            if link not in history:
                tmdb = get_tmdb_data(title)
                caption = f"🔥 **UPCOMING UPDATE**\n\n🎬 **{title.upper()}**\n"
                if tmdb:
                    caption += f"⭐️ **Rating:** {tmdb['rating']}/10\n🎭 **Genre:** {tmdb['genre']}\n\n📖 **Sinopsis:**\n_{tmdb['synopsis'][:250]}..._\n"
                    if tmdb['trailer']: caption += f"\n📺 **Trailer:** [Klik Disini]({tmdb['trailer']})"
                else: caption += "\n🍿 _Segera hadir di bioskop!_"
                caption += "\n\n➖➖➖➖➖➖➖➖➖➖\n📢 @SheJua"
                if send_telegram(caption, img_url).get("ok"):
                    history.append(link)
                    new_entries.append(link)

    # Simpan History agar tidak dobel post
    if new_entries:
        with open(DB_FILE, "w") as f:
            f.write("\n".join(history))
        print(f"Berhasil update {len(new_entries)} film baru.")
    else:
        print("Tidak ada update baru.")

if __name__ == "__main__":
    run()
