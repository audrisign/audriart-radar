import os
import requests
import json
import xml.etree.ElementTree as ET

# Webhook URL dari GitHub Secrets
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# Kata Kunci Inti & Fleksibel
KEYWORDS = [
    "book cover", "splash art", "concept art", "character design", 
    "character sheet", "vtuber", "background art", "environment art",
    "commission", "custom art", "custom illustration", "oc illustration",
    "illustrator", "2d artist", "looking for artist", "hiring", "artist"
]

SUBREDDITS = ['HungryArtists', 'ArtCommissions', 'forhire', 'starvingartists']

def fetch_reddit_jobs():
    """Memindai Reddit menggunakan Atom/RSS Feed yang tahan blokir IP"""
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
                        
                        # Filter postingan yang berindikasi lowongan / komisi
                        if "hiring" in title_lower or "[hiring]" in title_lower:
                            # Cari kata kunci yang cocok
                            matched_kw = next((kw for kw in KEYWORDS if kw in title_lower), "Lowongan")
                            found_jobs.append({
                                'title': title,
                                'url': permalink,
                                'source': f'Reddit (r/{sub})',
                                'keyword': matched_kw.title()
                            })
            else:
                print(f"Subreddit r/{sub} merespons dengan status HTTP: {response.status_code}")
        except Exception as e:
            print(f"Gagal mengambil data dari r/{sub}: {e}")
            
    return found_jobs

def save_jobs_to_json(jobs):
    """Menyimpan data lowongan ke file jobs.json"""
    try:
        with open('jobs.json', 'w', encoding='utf-8') as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)
        print(f"Berhasil menyimpan {len(jobs)} lowongan ke jobs.json")
    except Exception as e:
        print(f"Gagal menyimpan jobs.json: {e}")

def send_to_discord(jobs):
    """Mengirim hasil ke Discord Webhook"""
    if not DISCORD_WEBHOOK_URL:
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
            print(f"Error Discord: {e}")

if __name__ == "__main__":
    print("Memulai pemindaian RSS Reddit...")
    jobs = fetch_reddit_jobs()
    print(f"Total lowongan ditemukan: {len(jobs)}")
    
    save_jobs_to_json(jobs)
    if jobs:
        send_to_discord(jobs)
