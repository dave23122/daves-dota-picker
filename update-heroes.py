import os
import requests
import json

# Constants
OPENDOTA_API = "https://api.opendota.com/api/heroes"
CDN_BASE_URL = "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes"
IMAGE_DIR = "hero_data/hero_images"
JSON_FILE = "hero_data/heroes.json"

def fetch_heroes():
    response = requests.get(OPENDOTA_API)
    response.raise_for_status()
    return response.json()

def download_image(hero_name, dest_folder):
    url = f"{CDN_BASE_URL}/{hero_name}.png"
    response = requests.get(url)
    response.raise_for_status()
    
    filepath = os.path.join(dest_folder, f"{hero_name}.png")
    with open(filepath, "wb") as f:
        f.write(response.content)
    return filepath

def main():
    # Create images directory if it doesn't exist
    os.makedirs(IMAGE_DIR, exist_ok=True)

    print("Fetching heroes from OpenDota...")
    heroes = fetch_heroes()

    heroes_json = []
    print("Downloading hero images...")
    for hero in heroes:
        # hero['name'] example: "npc_dota_hero_axe"
        # The CDN uses just the hero name part (e.g. "axe")
        hero_key = hero["name"].replace("npc_dota_hero_", "")
        localized_name = hero["localized_name"]
        hero_id = hero["id"]

        try:
            image_path = download_image(hero_key, IMAGE_DIR)
            # Save relative path
            relative_path = os.path.relpath(image_path)
            heroes_json.append({
                "hero_id": hero_id,
                "name": localized_name,
                "image": relative_path
            })
            print(f"Downloaded {localized_name}")
        except Exception as e:
            print(f"Failed to download image for {localized_name}: {e}")

    # Write JSON file
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump({"heroes": heroes_json}, f, indent=2, ensure_ascii=False)

    print(f"\nDone! Hero data JSON saved to {JSON_FILE}")

if __name__ == "__main__":
    main()