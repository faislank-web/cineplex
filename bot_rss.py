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
TMDB_KEY = "61e2290429798c561450eb56b26de19b"
# ===============================================

def get_tmdb_data(title):
    try:
        clean_title = title.split(' (')[0].split(' - ')[0]
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
    except Exception as e:
        print(f"TMDB Error: {e}")
    return None

def send_telegram(caption, image_url):
    keyboard = json.dumps({
        "inline_keyboard": [
            [{"text": "🎬 Cek Disini", "url": "https://t.me/+w6XDg0Ap0yhlY2I9"}],
            [{"text": "📞 Hub. Admin", "url": "https://t.me/ksrfsj_bot"}]
        ]
    })

    if image_url:
        try:
            headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://m.21cineplex.com/"}
            img_res = requests.get(image_url, headers=headers, timeout=30)
            if img_res.status_code == 200:
                photo = BytesIO(img_res.content)
                photo.name = 'poster.jpg'
                url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
                return requests.post(url, files={'photo': photo}, data={
                    "chat_id": CHAT_ID, "caption": caption, 
                    "parse_mode": "Markdown", "reply_markup": keyboard
                }).json()
        except: pass

    return requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={
        "chat_id": CHAT_ID, "text": caption, "parse_mode": "Markdown", "reply_markup": keyboard
    }).json()

def run():
    print("Memulai pengecekan RSS...")
    feed = feedparser.parse(RSS_URL)
    if not feed.entries: return
    
    last_link = ""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            last_link = f.read().strip()

    for entry in feed.entries[:3][::-1]:
        if entry.link != last_link:
            title = entry.title
            image_url = entry.enclosures[0].get('url', '') if entry.get('enclosures') else ""
            
            tmdb = get_tmdb_data(title)
            
            # SUSUN CAPTION
            caption = f"🔥 **NEW MOVIE UPDATE**\n\n"
            caption += f"🎬 **{title.upper()}**\n"
            
            if tmdb:
                caption += f"⭐️ **Rating:** {tmdb['rating']}/10\n"
                caption += f"🎭 **Genre:** {tmdb['genre']}\n\n"
                caption += f"📖 **Sinopsis:**\n_{tmdb['synopsis'][:250]}..._\n\n"
                if tmdb['trailer']:
                    caption += f"📺 **Trailer:** [Klik Disini]({tmdb['trailer']})\n"
            else:
                caption += "\n🍿 _Detail lengkap segera diperbarui!_\n"
            
            caption += "\n➖➖➖➖➖➖➖➖➖➖\n"
            caption += "📢 @SheJua" # Hashcineplex sudah dihapus

            res = send_telegram(caption, image_url)
            if res.get("ok"):
                with open(DB_FILE, "w") as f:
                    f.write(entry.link)
                last_link = entry.link
                print(f"Berhasil memposting: {title}")

if __name__ == "__main__":
    run()
