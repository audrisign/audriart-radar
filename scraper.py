import os
import requests
import json

# Webhook URL dari GitHub Secrets
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# Kata Kunci Inti (Pendek & Fleksibel agar tidak melewatkan postingan)
KEYWORDS = [
    # Jenis Karya
    "book cover", "splash art", "concept art", "character design", 
    "character sheet", "vtuber", "background art", "environment art",
    
    # Komisi & Proyek
    "commission", "custom art", "custom illustration", "oc illustration",
    "illustrator", "2d artist", "looking for artist", "hiring artist"
]

def fetch_reddit_jobs():
    """Memindai Reddit dengan pencocokan kata kunci fleksibel"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AudriArtBot/1.0'}
    subreddits = ['HungryArtists', 'ArtCommissions', 'forhire', 'starvingartists']
    found_jobs = []

    for sub in subreddits:
        url = f"https://www.reddit.com/r/{sub}/new.json?limit=30"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                posts = data['data']['children']
                for post in posts:
                    title = post['data']['title']
                    permalink = f"https://reddit.com{post['data']['permalink']}"
                    title_lower = title.lower()
                    
                    # Cek apakah postingan mengandung indikasi lowongan [Hiring] / Hiring
                    is_hiring = "hiring" in title_lower or "[hiring]" in title_lower
                    
                    if is_hiring:
                        # Cek apakah judul mengandung salah satu kata kunci inti
                        for kw in KEYWORDS:
                            if kw in title_lower:
                                found_jobs.append({
                                    'title': title,
                                    'url': permalink,
                                    'source': f'Reddit (r/{sub})',
                                    'keyword': kw.title()
                                })
                                break # Hindari duplikat jika cocok dengan beberapa kata kunci
        except Exception as e:
            print(f"Error fetching Reddit (r/{sub}): {e}")
            
    return found_jobs

def save_jobs_to_json(jobs):
    """Menyimpan data lowongan ke file jobs.json untuk dibaca oleh website"""
    try:
        with open('jobs.json', 'w', encoding='utf-8') as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)
        print("Berhasil menyimpan data ke jobs.json")
    except Exception as e:
        print(f"Gagal menyimpan jobs.json: {e}")

def send_to_discord(jobs):
    """Mengirim hasil pencarian ke Discord Webhook"""
    if not DISCORD_WEBHOOK_URL:
        print("Discord Webhook URL belum diatur!")
        return

    # Kirim maksimal 5 notifikasi terbaru agar Discord tidak spamming
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
        requests.post(DISCORD_WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    print("Memulai pemindaian internet...")
    jobs = fetch_reddit_jobs()
    print(f"Ditemukan {len(jobs)} lowongan/komisi baru.")
    
    # Simpan ke JSON untuk website & kirim ke Discord
    save_jobs_to_json(jobs)
    if jobs:
        send_to_discord(jobs)
