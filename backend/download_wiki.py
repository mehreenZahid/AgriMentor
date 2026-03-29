import urllib.request
import urllib.parse
import json
import os

base_path = r'c:\Users\zmehr\OneDrive\Documents\GitHub\AgriMentor\backend\static\images'

def fetch_wiki_image(query, save_path):
    url = f"https://en.wikipedia.org/w/api.php?action=query&format=json&prop=pageimages&generator=search&gsrsearch={urllib.parse.quote(query)}&gsrlimit=1&pithumbsize=800"
    headers = {'User-Agent': 'AgriMentorBot/1.0 (contact@agrimentor.app)'}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            pages = data.get('query', {}).get('pages', {})
            if not pages:
                print(f"No results for {save_path}")
                return
            page = list(pages.values())[0]
            if 'thumbnail' not in page:
                print(f"No thumbnail for {save_path}")
                return
            img_url = page['thumbnail']['source']
            
            img_req = urllib.request.Request(img_url, headers=headers)
            with urllib.request.urlopen(img_req) as img_resp:
                full_path = os.path.join(base_path, save_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'wb') as f:
                    f.write(img_resp.read())
            print(f"Downloaded {save_path} from {img_url}")
    except Exception as e:
        print(f"Failed {save_path}: {e}")

fetch_wiki_image("Winter wheat snow field", "seasons/winter.jpg")
fetch_wiki_image("Drought cracked earth soil", "water/low.jpg")
fetch_wiki_image("Irrigation sprinkler field", "water/medium.jpg")
fetch_wiki_image("Rice paddy flooded field", "water/high.jpg")
