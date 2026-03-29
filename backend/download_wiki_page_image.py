import urllib.request
import json
import os

def get_wiki_page_image(page_title, save_path):
    url = f"https://en.wikipedia.org/w/api.php?action=query&titles={urllib.parse.quote(page_title)}&prop=pageimages&pithumbsize=800&format=json"
    headers = {'User-Agent': 'AgriMentorBot/1.0 (contact@agrimentor.app)'}
    req = urllib.request.Request(url, headers=headers)
    try:
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read().decode())
        pages = data.get('query', {}).get('pages', {})
        page = list(pages.values())[0]
        img_url = page['thumbnail']['source']
        
        img_req = urllib.request.Request(img_url, headers=headers)
        with urllib.request.urlopen(img_req) as img_resp, open(save_path, 'wb') as f:
            f.write(img_resp.read())
            
        print(f"Downloaded {save_path} from {img_url}")

    except Exception as e:
        print(f"Failed {save_path}: {e}")

base = r'c:\Users\zmehr\OneDrive\Documents\GitHub\AgriMentor\backend\static\images'
os.makedirs(os.path.join(base, "seasons"), exist_ok=True)
os.makedirs(os.path.join(base, "water"), exist_ok=True)

get_wiki_page_image("Winter_wheat", os.path.join(base, "seasons/winter.jpg"))
get_wiki_page_image("Drought", os.path.join(base, "water/low.jpg"))
get_wiki_page_image("Irrigation", os.path.join(base, "water/medium.jpg"))
get_wiki_page_image("Paddy_field", os.path.join(base, "water/high.jpg"))
