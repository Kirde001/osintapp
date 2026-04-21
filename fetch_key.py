import requests
import re
import os

def fetch_flickr_key_advanced():
    url = "https://www.flickr.com/explore" 
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    try:
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        patterns = [
            r'site_key["\']?\s*[:=]\s*["\']([a-f0-9]{32})["\']',
            r'["\']api["\']\s*:\s*{\s*["\']site_key["\']\s*:\s*["\']([a-f0-9]{32})["\']'
        ]
        
        new_key = None
        for pattern in patterns:
            match = re.search(pattern, response.text)
            if match:
                new_key = match.group(1)
                break
        
        if new_key:
            print(f"Ключ найден: {new_key}")
            
            env_path = os.path.join(os.path.dirname(__file__), '.env')
            with open(env_path, "w") as f:
                f.write(f"FLICKR_SITE_KEY={new_key}\n")
            
            print(f"Файл {env_path} обновлен.")
            return True
        else:
            print("ERR - ключ не найден в HTML")
            with open("debug.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            return False

    except Exception as e:
        print(f"Критическая неудача: {e}")
        return False

if __name__ == "__main__":
    fetch_flickr_key_advanced()