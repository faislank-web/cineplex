import requests
import re
import json
import os
import random
import time

TOKEN = os.getenv("TWITTER_BOT_TOKEN")
TARGET_GROUPS = ["-1003760170878", "-1003951572012"]
DB_FILE = "sent_tweets.txt" 
TARGET_ACCOUNTS = ["nyaineneng", "cinema21", "sosmedkeras", "komedigelaap"]

def get_guest_token():
    """Mengambil Guest Token resmi Twitter agar tidak kena 429"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    try:
        # Mengambil token dari halaman utama syndication
        res = requests.post("https://api.twitter.com/1.1/guest/activate.json", 
                           headers={'Authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA'}, 
                           timeout=20)
        return res.json().get('guest_token')
    except:
        return None

def clean_content(text):
    cleaned = re.sub(r'^\[.*?\]\s*', '', text)
    cleaned = re.sub(r'http\S+', '', cleaned)
    return cleaned.strip()

def send_telegram(chat_id, text, media_url=None, is_video=False):
    base_url = f"https://api.telegram.org/bot{TOKEN}"
    caption = f"<b>Update Terbaru:</b>\n\n<blockquote>{text}</blockquote>"
    try:
        if media_url:
            method = "sendVideo" if is_video else "sendPhoto"
            key = "video" if is_video else "photo"
            payload = {"chat_id": chat_id, key: media_url, "caption": caption, "parse_mode": "HTML"}
            requests.post(f"{base_url}/{method}", json=payload, timeout=30)
        else:
            payload = {"chat_id": chat_id, "text": caption, "parse_mode": "HTML"}
            requests.post(f"{base_url}/sendMessage", json=payload, timeout=30)
        return True
    except: return False

def run_monitor():
    print("🔓 ATTEMPTING TO BREAK 429 LIMIT...")
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: history = f.read().splitlines()
    else: history = []

    # AMBIL GUEST TOKEN
    guest_token = get_guest_token()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
        'Authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
        'x-guest-token': guest_token,
        'Accept': 'application/json'
    }

    random.shuffle(TARGET_ACCOUNTS)

    for account in TARGET_ACCOUNTS:
        print(f"🔎 Scanning @{account}...")
        try:
            # Menggunakan URL Syndication dengan Guest Token
            url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{account}"
            
            # Jika punya guest_token, Twitter lebih melunak
            res = requests.get(url, headers=headers, timeout=30)
            
            if res.status_code == 429:
                print(f"❌ Tetap 429. IP GitHub ini sedang di-block berat.")
                continue

            data_match = re.search(r'id="__NEXT_DATA__" type="application/json">(.*?)</script>', res.text)
            if not data_match: continue
            
            data = json.loads(data_match.group(1))
            entries = data.get('props', {}).get('pageProps', {}).get('timeline', {}).get('entries', [])
            
            if not entries: continue
            item = entries[0].get('content', {}).get('tweet')
            tweet_id = str(item.get('id_str'))

            if tweet_id not in history:
                text = clean_content(item.get('full_text', ''))
                m_url, is_v = None, False
                if 'extended_entities' in item:
                    m = item['extended_entities']['media'][0]
                    if m['type'] == 'photo': m_url = m['media_url_https']
                    elif m['type'] in ['video', 'animated_gif']:
                        v = m['video_info']['variants']
                        best = max([x for x in v if 'bitrate' in x], key=lambda x: x['bitrate'])
                        m_url = best['url']
                        is_v = True
                
                print(f"✨ SUCCESS! Sending @{account}")
                for g_id in TARGET_GROUPS: send_telegram(g_id, text, m_url, is_v)
                
                with open(DB_FILE, "a") as f: f.write(f"{tweet_id}\n")
                history.append(tweet_id)
            else:
                print(f"✅ No new update.")
                
            time.sleep(random.randint(10, 20)) # Jeda krusial
        except Exception as e: print(f"💥 Error: {e}")

if __name__ == "__main__":
    run_monitor()
