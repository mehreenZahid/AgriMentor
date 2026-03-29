import os
import urllib.request
import shutil

base_path = r"c:\Users\zmehr\OneDrive\Documents\GitHub\AgriMentor\backend\static\images"

# Rename PNGs to JPGs
for folder in ["soil", "seasons"]:
    folder_path = os.path.join(base_path, folder)
    if os.path.exists(folder_path):
        for f in os.listdir(folder_path):
            if f.endswith(".png"):
                old_file = os.path.join(folder_path, f)
                new_file = os.path.join(folder_path, f.replace(".png", ".jpg"))
                shutil.move(old_file, new_file)

# Download missing images
downloads = {
    "seasons/winter.jpg": "https://picsum.photos/seed/winter/500/300",
    "water/low.jpg": "https://picsum.photos/seed/waterlow/500/300",
    "water/medium.jpg": "https://picsum.photos/seed/watermed/500/300",
    "water/high.jpg": "https://picsum.photos/seed/waterhi/500/300"
}

headers = {'User-Agent': 'Mozilla/5.0'}
for path, url in downloads.items():
    full_path = os.path.join(base_path, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response, open(full_path, 'wb') as out_file:
         out_file.write(response.read())
print("Done")
