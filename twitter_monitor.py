import requests
import re
import json
import os
import random
import time

# --- KONFIGURASI ---
TOKEN = os.getenv("TWITTER_BOT_TOKEN")
TARGET_GROUPS = ["-1003760170878", "-1003951572012"]
DB_FILE = "sent_tweets.txt" 
TARGET_ACCOUNTS = ["nyaineneng", "cinema21", "sosmedkeras", "komedigelaap"]

# Daftar User-Agent agar tidak terdeteksi bot GitHub (Status 429)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
]

def clean_content(text):
    cleaned = re.sub(r'^\[.*?\]\s*', '', text)
    cleaned = re.sub(r'http\S+', '', cleaned)
    return cleaned.strip()

def send_telegram(chat_id, text, media_url=None, is_video=False):
    if not TOKEN: return False
    base_url = f"https://api.telegram.org/bot{TOKEN}"
    caption = f"<b>Update Baru:</b>\n\n<blockquote>{text}</blockquote>"
    
    try:
        if media_url:
            method = "sendVideo" if is_video else "sendPhoto"
            key = "video" if is_video else "photo"
            payload = {"chat_id": chat_id, key: media_url, "caption": caption, "parse_mode": "HTML"}
            r = requests.post(f"{base_url}/{method}", json=payload, timeout=30)
        else:
            payload = {"chat_id": chat_id, "text": caption, "parse_mode": "HTML"}
            r = requests.post(f"{base_url}/sendMessage", json=payload, timeout=30)
        return r.status_code == 200
    except: return False

def run_monitor():
    print("🚀 MEMULAI SCANNING (BYPASS MODE)...")
    
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            history = f.read().splitlines()
    else:
        history = []

    # Acak daftar akun agar tidak selalu mulai dari yang sama
    random.shuffle(TARGET_ACCOUNTS)

    for account in TARGET_ACCOUNTS:
        print(f"\n🔎 Memeriksa @{account}...")
        try:
            # Bypass Headers: Setiap akun pakai User-Agent beda
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://twitter.com/',
                'x-twitter-client-language': 'en',
                'x-twitter-active-user': 'yes'
            }

            url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{account}"
            
            # Gunakan jeda acak SEBELUM request agar tidak terbaca pola bot
            time.sleep(random.randint(5, 15))
            
            res = requests.get(url, headers=headers, timeout=30)
            
            if res.status_code == 429:
                print(f"⚠️ Kena Limit (429) lagi. Coba ganti strategi...")
                # Jika 429, kita coba sekali lagi dengan URL berbeda sedikit (tambah timestamp)
                res = requests.get(f"{url}?t={int(time.time())}", headers=headers, timeout=30)

            if res.status_code != 200:
                print(f"❌ Gagal akses @{account} (Status: {res.status_code})")
                continue
            
            data_match = re.search(r'id="__NEXT_DATA__" type="application/json">(.*?)</script>', res.text)
            if not data_match:
                print(f"⚠️ JSON @{account} tidak ditemukan.")
                continue
            
            data = json.loads(data_match.group(1))
            timeline = data.get('props', {}).get('pageProps', {}).get('timeline', {}).get('entries', [])
            
            if not timeline:
                print(f"ℹ️ Timeline @{account} kosong.")
                continue

            t = timeline[0].get('content', {}).get('tweet')
            if not t: continue
            
            tweet_id = str(t.get('id_str'))

            if tweet_id not in history:
                text = clean_content(t.get('full_text', ''))
                m_url, is_v = None, False
                
                if 'extended_entities' in t:
                    m = t['extended_entities']['media'][0]
                    if m['type'] == 'photo': m_url = m['media_url_https']
                    elif m['type'] in ['video', 'animated_gif']:
                        vars = m['video_info']['variants']
                        best = max([v for v in vars if 'bitrate' in v], key=lambda x: x['bitrate'])
                        m_url = best['url']
                        is_v = True
                
                print(f"✨ MENGIRIM TWEET DARI @{account}!")
                for g_id in TARGET_GROUPS:
                    send_telegram(g_id, text, m_url, is_v)
                
                with open(DB_FILE, "a") as f:
                    f.write(f"{tweet_id}\n")
                history.append(tweet_id)
            else:
                print(f"✅ @{account} sudah up-to-date.")
                
        except Exception as e:
            print(f"💥 Error @{account}: {e}")

if __name__ == "__main__":
    run_monitor()
    print("\n📍 Selesai.")
