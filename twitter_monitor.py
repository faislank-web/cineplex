import requests
import re
import json
import os
import random
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- KONFIGURASI AMAN ---
# Ambil token dari GitHub Secrets
TOKEN = os.getenv("TWITTER_BOT_TOKEN")

# Daftar ID Grup Anda
TARGET_GROUPS = ["-1003760170878", "-1003951572012"]
DB_FILE = "sent_tweets.txt" 

# Akun yang akan dipantau
TARGET_ACCOUNTS = [
    "nyaineneng", "FILM_Indonesia",
    "cinema21", "sosmedkeras", "komedigelaap"
]

# Pastikan database file ada
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        f.write("")

def get_safe_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    return session

def clean_content(text):
    # Sesuai instruksi: hapus tanda kurung di awal judul agar rapi
    cleaned = re.sub(r'^\[.*?\]\s*', '', text)
    # Menghapus link twitter yang ada di dalam teks
    cleaned = re.sub(r'http\S+', '', cleaned)
    return cleaned.strip()

def send_to_telegram(chat_id, text, media_url=None, is_video=False):
    if not TOKEN:
        print("❌ Error: Token tidak ditemukan!")
        return False
        
    session = get_safe_session()
    base_url = f"https://api.telegram.org/bot{TOKEN}"
    # Menggunakan blockquote agar teks terlihat bersih
    caption = f"<blockquote>{text}</blockquote>"
    
    try:
        if media_url:
            method = "sendVideo" if is_video else "sendPhoto"
            key = "video" if is_video else "photo"
            payload = {
                "chat_id": chat_id,
                key: media_url,
                "caption": caption,
                "parse_mode": "HTML"
            }
            r = session.post(f"{base_url}/{method}", json=payload, timeout=60)
        else:
            payload = {"chat_id": chat_id, "text": caption, "parse_mode": "HTML"}
            r = session.post(f"{base_url}/sendMessage", json=payload, timeout=60)
        return r.status_code == 200
    except:
        return False

def broadcast_to_groups(text, media_url, is_v):
    success_all = True
    for group_id in TARGET_GROUPS:
        if not send_to_telegram(group_id, text, media_url, is_v):
            success_all = False
        time.sleep(1) 
    return success_all

def run_monitor():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
    }
    
    print(f"[*] Memulai Scan Twitter...")
    session = get_safe_session()
    random.shuffle(TARGET_ACCOUNTS)
    
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            history = f.read().splitlines()
    else:
        history = []

    for account in TARGET_ACCOUNTS:
        url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{account}"
        try:
            response = session.get(url, headers=headers, timeout=30)
            if response.status_code != 200: continue

            data_match = re.search(r'id="__NEXT_DATA__" type="application/json">(.*?)</script>', response.text)
            if data_match:
                data = json.loads(data_match.group(1))
                timeline = data['props']['pageProps']['timeline']['entries']
                
                if timeline:
                    # Ambil tweet teratas
                    for entry in timeline[:1]:
                        t = entry['content']['tweet']
                        tweet_id = str(t.get('id_str'))
                        
                        if tweet_id not in history:
                            isi_bersih = clean_content(t.get('full_text', ''))
                            m_url = None
                            is_v = False
                            
                            if 'extended_entities' in t:
                                media = t['extended_entities']['media'][0]
                                if media['type'] == 'photo':
                                    m_url = media['media_url_https']
                                elif media['type'] in ['video', 'animated_gif']:
                                    variants = media['video_info']['variants']
                                    best_v = max([v for v in variants if 'bitrate' in v], key=lambda x: x['bitrate'])
                                    m_url = best_v['url']
                                    is_v = True
                            
                            if (isi_bersih or m_url) and broadcast_to_groups(isi_bersih, m_url, is_v):
                                with open(DB_FILE, "a") as f:
                                    f.write(f"{tweet_id}\n")
                                history.append(tweet_id)
                                print(f"    [OK] @{account} -> Terkirim.")
            
            time.sleep(random.randint(5, 10))
        except:
            continue

if __name__ == "__main__":
    run_monitor()
    # Sesuai instruksi: footer diganti
    print("\n📍 Sukses Terkirim")
