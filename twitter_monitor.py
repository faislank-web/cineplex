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
            requests.post(f"{base_url}/{method}", json=payload, timeout=30)
        else:
            payload = {"chat_id": chat_id, "text": caption, "parse_mode": "HTML"}
            requests.post(f"{base_url}/sendMessage", json=payload, timeout=30)
        return True
    except: return False

def run_monitor():
    print("🚀 BYPASS MODE ACTIVATED...")
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: history = f.read().splitlines()
    else: history = []

    random.shuffle(TARGET_ACCOUNTS)

    for account in TARGET_ACCOUNTS:
        print(f"🔎 Checking @{account}...")
        try:
            # Trik Bypass: Pakai sub-domain berbeda dan parameter acak
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
                'Accept': 'application/json',
                'Referer': 'https://google.com'
            }
            # Tambahkan token acak agar Twitter tidak mendeteksi request yang sama
            rand_token = random.randint(1000, 9999)
            url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{account}?dummy={rand_token}"
            
            time.sleep(random.randint(10, 20)) # Jeda lebih lama agar tidak kena 429
            res = requests.get(url, headers=headers, timeout=30)
            
            if res.status_code == 429:
                print(f"⚠️ Masih kena 429. Twitter sedang ketat. Skip dulu...")
                continue

            data_match = re.search(r'id="__NEXT_DATA__" type="application/json">(.*?)</script>', res.text)
            if not data_match: continue
            
            data = json.loads(data_match.group(1))
            entries = data.get('props', {}).get('pageProps', {}).get('timeline', {}).get('entries', [])
            
            if not entries: continue

            item = entries[0].get('content', {}).get('tweet')
            if not item: continue
            
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
                
                print(f"✨ Sending update from @{account}...")
                for g_id in TARGET_GROUPS: send_telegram(g_id, text, m_url, is_v)
                
                with open(DB_FILE, "a") as f: f.write(f"{tweet_id}\n")
                history.append(tweet_id)
            else:
                print(f"✅ No new tweet for @{account}")
                
        except Exception as e: print(f"💥 Error: {e}")

if __name__ == "__main__":
    run_monitor()
