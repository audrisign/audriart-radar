import os
import requests
import json
import xml.etree.ElementTree as ET

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

KEYWORDS = [
    "book cover", "splash art", "concept art", "character design", 
    "character sheet", "vtuber", "background art", "environment art",
    "commission", "custom art", "custom illustration", "oc illustration",
    "illustrator", "2d artist", "looking for artist", "hiring", "artist",
    "poster", "banner", "logo", "thumbnail", "overlay", "anime"
]

# Menambah target subreddit pencarian
SUBREDDITS = [
    'HungryArtists', 'ArtCommissions', 'forhire', 
    'starvingartists', 'AnimeSketch', 'DesignJobs'
]

def fetch_reddit_jobs():
    """Memindai RSS feed dari subreddit pilihan"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    found_jobs = []

    for sub in SUBREDDITS:
        url = f"https://www.reddit.com/r/{sub}/new.rss"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                entries = root.findall('atom:entry', ns)
                
                for entry in entries:
                    title_elem = entry.find('atom:title', ns)
                    link_elem = entry.find('atom:link', ns)
                    
                    if title_elem is not None and title_elem.text:
                        title = title_elem.text
                        title_lower = title.lower()
                        permalink = link_elem.attrib.get('href', f"https://reddit.com/r/{sub}") if link_elem is not None else ""
                        
                        if "hiring" in title_lower or "[hiring]" in title_lower:
                            matched_kw = next((kw for kw in KEYWORDS if kw in title_lower), "Lowongan")
                            found_jobs.append({
                                'title': title,
                                'url': permalink,
                                'source': f'Reddit (r/{sub})',
                                'keyword': matched_kw.title()
                            })
        except Exception as e:
            print(f"Gagal mengambil data dari r/{sub}: {e}")
            
    return found_jobs

def save_jobs_to_json(new_jobs):
    """Menggabungkan lowongan baru dengan lowongan lama (maksimal menyimpan 40 lowongan terbaru)"""
    existing_jobs = []
    
    # 1. Baca data lama yang sudah ada di jobs.json
    if os.path.exists('jobs.json'):
        try:
            with open('jobs.json', 'r', encoding='utf-8') as f:
                existing_jobs = json.load(f)
        except Exception:
            existing_jobs = []

    # 2. Gabungkan data baru di posisi paling atas
    all_jobs = new_jobs + existing_jobs

    # 3. Hapus duplikat berdasarkan URL postingan
    unique_jobs = []
    seen_urls = set()
    for job in all_jobs:
        if job['url'] not in seen_urls:
            unique_jobs.append(job)
            seen_urls.add(job['url'])

    # 4. Simpan maksimal 40 lowongan terbaru
    final_jobs = unique_jobs[:40]

    try:
        with open('jobs.json', 'w', encoding='utf-8') as f:
            json.dump(final_jobs, f, ensure_ascii=False, indent=2)
        print(f"Berhasil menyimpan total {len(final_jobs)} lowongan ke jobs.json")
    except Exception as e:
        print(f"Gagal menyimpan jobs.json: {e}")

def send_to_discord(jobs):
    if not DISCORD_WEBHOOK_URL:
        return

    for job in jobs[:3]:
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
            print(f"Error Discord: {e}")

if __name__ == "__main__":
    print("Memulai pemindaian RSS Reddit...")
    jobs = fetch_reddit_jobs()
    print(f"Lowongan baru ditemukan pada sesi ini: {len(jobs)}")
    
    save_jobs_to_json(jobs)
    if jobs:
        send_to_discord(jobs)
