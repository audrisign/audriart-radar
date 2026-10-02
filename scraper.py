import os
import requests
import json

# Webhook URL dari GitHub Secrets
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# Daftar Kata Kunci Lengkap (Agensi + Proyek Spesifik + Komisi Kustom)
KEYWORDS = [
    # --- 1. PROYEK SPESIFIK & AGENSI/PENERBIT ---
    "hiring book cover artist",
    "looking for book cover illustrator",
    "splash art commission",
    "hiring splash artist",
    "looking for concept artist",
    "environment concept art",
    "hiring character illustrator",
    "character design commission",

    # --- 2. KOMISI KUSTOM, PERSONAL & OC (BARU) ---
    "looking for custom illustration",
    "need custom art",
    "want to commission an artist",
    "looking to commission",
    "looking for commission artist",
    "buying art commission",
    "commissioning an artist",
    "looking for OC illustration",
    "VTuber illustration commission",
    "looking for character sheet artist",
    "need artist for profile picture",

    # --- 3. KATA KUNCI UMUM & FREELANCE ---
    "open for illustration commission",
    "looking to hire an illustrator",
    "freelance illustrator wanted",
    "artist needed for project"
]

def fetch_reddit_jobs():
    """Memindai subreddit r/HungryArtists, r/ArtCommissions, r/forhire"""
    headers = {'User-Agent': 'AudriArtBot/1.0'}
    subreddits = ['HungryArtists', 'ArtCommissions', 'forhire']
    found_jobs = []

    for sub in subreddits:
        url = f"https://www.reddit.com/r/{sub}/new.json?limit=25"
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                posts = data['data']['children']
                for post in posts:
                    title = post['data']['title']
                    permalink = f"https://reddit.com{post['data']['permalink']}"
                    
                    # Filter postingan yang mengandung tag [Hiring]
                    if "[hiring]" in title.lower():
                        # Cek apakah judul cocok dengan salah satu kata kunci di daftar
                        if any(kw.lower() in title.lower() for kw in KEYWORDS):
                            found_jobs.append({
                                'title': title,
                                'url': permalink,
                                'source': f'Reddit (r/{sub})'
                            })
        except Exception as e:
            print(f"Error fetching Reddit ({sub}): {e}")
            
    return found_jobs

def send_to_discord(jobs):
    """Mengirim hasil pencarian ke Discord Webhook"""
    if not DISCORD_WEBHOOK_URL:
        print("Discord Webhook URL belum diatur!")
        return

    for job in jobs:
        payload = {
            "embeds": [{
                "title": "🎨 Lowongan / Komisi Baru Ditemukan!",
                "description": f"**{job['title']}**\n\n[Buka Lowongan / Pesanan]({job['url']})",
                "color": 8126445,  # Warna Ungu (#7C3AED)
                "footer": {
                    "text": f"Sumber: {job['source']} • AudriArt Radar"
                }
            }]
        }
        requests.post(DISCORD_WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    print("Memulai pemindaian internet...")
    jobs = fetch_reddit_jobs()
    print(f"Ditemukan {len(jobs)} lowongan/komisi baru.")
    if jobs:
        send_to_discord(jobs)
