import requests
import re
import json
import os
import random
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from io import BytesIO

# --- KONFIGURASI AMAN ---
TOKEN = os.getenv("TWITTER_BOT_TOKEN")
TARGET_GROUPS = ["-1003760170878", "-1003951572012"]
DB_FILE = "sent_tweets.txt" 

TARGET_ACCOUNTS = [
    "nyaineneng", "FilmUpdates", "FILM_Indonesia", 
    "cinema21", "rofmeov", "sosmedkeras", "komedigelaap"
]

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
    # Hapus tanda kurung di awal judul sesuai permintaan
    cleaned = re.sub(r'^\[.*?\]\s*', '', text)
    cleaned = re.sub(r'http\S+', '', cleaned)
    return cleaned.strip()

def send_to_telegram(chat_id, text, media_url=None, is_video=False):
    if not TOKEN: return False
    session = get_safe_session()
    base_url = f"https://api.telegram.org/bot{TOKEN}"
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
    for group_id in TARGET_GROUPS:
        send_to_telegram(group_id, text, media_url, is_v)
        time.sleep(1.5) 

def run_monitor():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}
    session = get_safe_session()
    
    # Baca history
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            history = f.read().splitlines()
    else:
        history = []

    print(f"[*] Memulai Scan untuk {len(TARGET_ACCOUNTS)} akun...")

    for account in TARGET_ACCOUNTS:
        try:
            url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{account}"
            response = session.get(url, headers=headers, timeout=30)
            if response.status_code != 200: continue

            data_match = re.search(r'id="__NEXT_DATA__" type="application/json">(.*?)</script>', response.text)
            if not data_match: continue
            
            data = json.loads(data_match.group(1))
            entries = data['props']['pageProps']['timeline']['entries']
            
            if not entries: continue

            # Ambil hanya 1 tweet paling baru dari akun ini
            item = entries[0]['content']['tweet']
            tweet_id = str(item.get('id_str'))

            if tweet_id not in history:
                isi_bersih = clean_content(item.get('full_text', ''))
                m_url, is_v = None, False
                
                if 'extended_entities' in item:
                    m = item['extended_entities']['media'][0]
                    if m['type'] == 'photo':
                        m_url = m['media_url_https']
                    elif m['type'] in ['video', 'animated_gif']:
                        vars = m['video_info']['variants']
                        best = max([v for v in vars if 'bitrate' in v], key=lambda x: x['bitrate'])
                        m_url = best['url']
                        is_v = True
                
                print(f"    [NEW] Menemukan update dari @{account}")
                broadcast_to_groups(isi_bersih, m_url, is_v)
                
                with open(DB_FILE, "a") as f:
                    f.write(f"{tweet_id}\n")
                history.append(tweet_id)
            
            time.sleep(random.randint(3, 7)) # Jeda tiap akun
        except Exception as e:
            print(f"    [ERR] Gagal scan @{account}: {e}")
            continue

if __name__ == "__main__":
    run_monitor()
    print("\n📍 Sukses Terkirim")
