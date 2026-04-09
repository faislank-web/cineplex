import requests
import re
import json
import os
import random
import time

# --- AMBIL DARI SECRETS ---
TOKEN = os.getenv("TWITTER_BOT_TOKEN")
TARGET_GROUPS = ["-1003760170878", "-1003951572012"]
DB_FILE = "sent_tweets.txt" 
TARGET_ACCOUNTS = ["nyaineneng", "cinema21", "sosmedkeras", "komedigelaap"]

def clean_content(text):
    cleaned = re.sub(r'^\[.*?\]\s*', '', text)
    cleaned = re.sub(r'http\S+', '', cleaned)
    return cleaned.strip()

def send_telegram(chat_id, text, media_url=None, is_video=False):
    if not TOKEN:
        print("❌ ERROR: Token kosong! Cek GitHub Secrets.")
        return False
    
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
        
        print(f"[*] Kirim ke {chat_id}: Status {r.status_code}")
        return r.status_code == 200
    except Exception as e:
        print(f"❌ Gagal kirim ke Telegram: {e}")
        return False

def run_monitor():
    print("🚀 MEMULAI SCANNING...")
    
    # Header lebih lengkap agar dikira manusia
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            history = f.read().splitlines()
    else:
        history = []

    for account in TARGET_ACCOUNTS:
        print(f"\n🔎 Memeriksa @{account}...")
        try:
            url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{account}"
            res = requests.get(url, headers=headers, timeout=30)
            
            if res.status_code != 200:
                print(f"⚠️ Twitter menolak akses (Status: {res.status_code})")
                continue
            
            data_match = re.search(r'id="__NEXT_DATA__" type="application/json">(.*?)</script>', res.text)
            if not data_match:
                print(f"⚠️ JSON tidak ditemukan di halaman @{account}")
                continue
            
            data = json.loads(data_match.group(1))
            timeline = data.get('props', {}).get('pageProps', {}).get('timeline', {}).get('entries', [])
            
            if not timeline:
                print(f"ℹ️ Timeline @{account} kosong.")
                continue

            t = timeline[0].get('content', {}).get('tweet')
            if not t: continue
            
            tweet_id = str(t.get('id_str'))
            print(f"🆔 Tweet ID: {tweet_id}")

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
                
                print(f"✨ MENGIRIM TWEET BARU DARI @{account}...")
                for g_id in TARGET_GROUPS:
                    send_telegram(g_id, text, m_url, is_v)
                
                with open(DB_FILE, "a") as f:
                    f.write(f"{tweet_id}\n")
                history.append(tweet_id)
            else:
                print(f"✅ @{account} sudah up-to-date.")
            
            time.sleep(random.randint(5, 10))
        except Exception as e:
            print(f"💥 ERROR pada @{account}: {e}")

if __name__ == "__main__":
    run_monitor()
    print("\n📍 Selesai.")
