import requests
import re
import json
import os
import random
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- KONFIGURASI AMAN ---
TOKEN = os.getenv("TWITTER_BOT_TOKEN")
TARGET_GROUPS = ["-1003760170878", "-1003951572012"]
DB_FILE = "sent_tweets.txt" 

# Target yang sudah dirampingkan sesuai permintaan
TARGET_ACCOUNTS = ["nyaineneng", "cinema21", "sosmedkeras", "komedigelaap"]

def get_safe_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=5,
        backoff_factor=3,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    return session

def clean_content(text):
    # Menghapus tanda kurung di awal judul agar rapi sesuai instruksi
    cleaned = re.sub(r'^\[.*?\]\s*', '', text)
    cleaned = re.sub(r'http\S+', '', cleaned)
    return cleaned.strip()

def send_to_telegram(chat_id, text, media_url=None, is_video=False):
    if not TOKEN: return False
    session = get_safe_session()
    base_url = f"https://api.telegram.org/bot{TOKEN}"
    
    # Format caption elegan dengan HTML
    caption = f"<b>Update Terbaru:</b>\n\n<blockquote>{text}</blockquote>"
    
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
    except Exception as e:
        print(f"Error Telegram: {e}")
        return False

def run_monitor():
    # Menggunakan User-Agent yang lebih stabil
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': '*/*',
    }
    session = get_safe_session()
    
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            history = f.read().splitlines()
    else:
        history = []

    print(f"[*] Memulai Scan untuk {len(TARGET_ACCOUNTS)} akun terpilih...")

    for account in TARGET_ACCOUNTS:
        try:
            url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{account}"
            response = session.get(url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                print(f"    [!] Gagal akses @{account}: {response.status_code}")
                continue

            data_match = re.search(r'id="__NEXT_DATA__" type="application/json">(.*?)</script>', response.text)
            if not data_match:
                print(f"    [!] Data @{account} tidak ditemukan.")
                continue
            
            data = json.loads(data_match.group(1))
            timeline = data.get('props', {}).get('pageProps', {}).get('timeline', {}).get('entries', [])
            
            if not timeline:
                print(f"    [?] @{account} tidak ada tweet.")
                continue

            # Ambil 1 tweet paling baru
            t_data = timeline[0].get('content', {}).get('tweet')
            if not t_data: continue
            
            tweet_id = str(t_data.get('id_str'))

            if tweet_id not in history:
                isi_bersih = clean_content(t_data.get('full_text', ''))
                m_url, is_v = None, False
                
                # Deteksi Media
                if 'extended_entities' in t_data:
                    m = t_data['extended_entities']['media'][0]
                    if m['type'] == 'photo':
                        m_url = m['media_url_https']
                    elif m['type'] in ['video', 'animated_gif']:
                        vars = m['video_info']['variants']
                        best = max([v for v in vars if 'bitrate' in v], key=lambda x: x['bitrate'])
                        m_url = best['url']
                        is_v = True
                
                print(f"    [NEW] @{account} -> Tweet ID {tweet_id}")
                
                for group_id in TARGET_GROUPS:
                    send_to_telegram(group_id, isi_bersih, m_url, is_v)
                    time.sleep(2)
                
                with open(DB_FILE, "a") as f:
                    f.write(f"{tweet_id}\n")
                history.append(tweet_id)
            else:
                print(f"    [.] @{account} sudah up-to-date.")
            
            time.sleep(random.randint(5, 10))
        except Exception as e:
            print(f"    [ERR] Error pada @{account}: {e}")
            continue

if __name__ == "__main__":
    run_monitor()
    print("\n📍 Selesai.")
