import urllib.request
import urllib.parse
import json
import os

base_path = r'c:\Users\zmehr\OneDrive\Documents\GitHub\AgriMentor\backend\static\images'

def fetch_wiki_file(filename, save_path):
    url = f"https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=imageinfo&iiprop=url&titles=File:{urllib.parse.quote(filename)}"
    headers = {'User-Agent': 'AgriMentorBot/1.0 (contact@agrimentor.app)'}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            pages = data.get('query', {}).get('pages', {})
            if not pages:
                print(f"No pages for {save_path}")
                return
            page = list(pages.values())[0]
            if 'imageinfo' not in page:
                print(f"No imageinfo for {save_path} (URL: {url})")
                return
            img_url = page['imageinfo'][0]['url']
            
            img_req = urllib.request.Request(img_url, headers=headers)
            with urllib.request.urlopen(img_req) as img_resp:
                full_path = os.path.join(base_path, save_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'wb') as f:
                    f.write(img_resp.read())
            print(f"Downloaded {save_path} from {img_url}")
    except Exception as e:
        print(f"Failed {save_path}: {e}")

fetch_wiki_file("Winter_wheat_covered_by_hoarfrost.jpg", "seasons/winter.jpg")
fetch_wiki_file("Drought-cracked_earth.jpg", "water/low.jpg")
fetch_wiki_file("Sprinkler_irrigation.jpg", "water/medium.jpg")
fetch_wiki_file("Rice_paddy_in_Madagascar.jpg", "water/high.jpg")
