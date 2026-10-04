import os
import requests
import json

# Webhook URL dari GitHub Secrets
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# Kata Kunci Fleksibel & Inti
KEYWORDS = [
    "book cover", "splash art", "concept art", "character design", 
    "character sheet", "vtuber", "background art", "environment art",
    "commission", "custom art", "custom illustration", "oc illustration",
    "illustrator", "2d artist", "looking for artist", "hiring artist"
]

def fetch_reddit_jobs():
    """Memindai Reddit dengan User-Agent browser asli"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    subreddits = ['HungryArtists', 'ArtCommissions', 'forhire', 'starvingartists']
    found_jobs = []

    for sub in subreddits:
        url = f"https://www.reddit.com/r/{sub}/new.json?limit=25"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                posts = data['data']['children']
                for post in posts:
                    title = post['data']['title']
                    permalink = f"https://reddit.com{post['data']['permalink']}"
                    title_lower = title.lower()
                    
                    if "hiring" in title_lower or "[hiring]" in title_lower:
                        for kw in KEYWORDS:
                            if kw in title_lower:
                                found_jobs.append({
                                    'title': title,
                                    'url': permalink,
                                    'source': f'Reddit (r/{sub})',
                                    'keyword': kw.title()
                                })
                                break
            else:
                print(f"Reddit r/{sub} merespons dengan status: {response.status_code}")
        except Exception as e:
            print(f"Error fetching Reddit (r/{sub}): {e}")
            
    return found_jobs

def save_jobs_to_json(jobs):
    """Menyimpan data lowongan ke file jobs.json"""
    try:
        with open('jobs.json', 'w', encoding='utf-8') as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)
        print("Berhasil memperbarui jobs.json!")
    except Exception as e:
        print(f"Gagal menyimpan jobs.json: {e}")

def send_to_discord(jobs):
    """Mengirim hasil ke Discord Webhook"""
    if not DISCORD_WEBHOOK_URL:
        print("Discord Webhook URL belum diatur.")
        return

    for job in jobs[:5]:
        payload = {
            "embeds": [{
                "title": f"🎨 [{job['keyword']}] Lowongan / Komisi Baru!",
                "description": f"**{job['title']}**\n\n[Buka Lowongan / Pesanan ↗]({job['url']})",
                "color": 8126445,
                "footer": {
                    "text": f"Sumber: {job['source']} • AudriArt Radar"
                }
            }]
        }
        try:
            requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
        except Exception as e:
            print(f"Error mengirim ke Discord: {e}")

if __name__ == "__main__":
    print("Memulai pemindaian internet...")
    jobs = fetch_reddit_jobs()
    print(f"Ditemukan {len(jobs)} lowongan/komisi baru.")
    
    save_jobs_to_json(jobs)
    if jobs:
        send_to_discord(jobs)
