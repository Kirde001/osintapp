import os
import requests
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
class FlickrOSINT:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        self.api_key = os.getenv("FLICKR_SITE_KEY")
        if not self.api_key:
            raise ValueError("API-ключ не найден")
    def _get_user_id(self, profile_url):
        url = "https://www.flickr.com/services/rest/"
        params = {
            "method": "flickr.urls.lookupUser",
            "api_key": self.api_key,
            "url": profile_url,
            "format": "json",
            "nojsoncallback": 1
        }
        res = self.session.get(url, params=params).json()
        if res.get("stat") == "ok":
            return res["user"]["id"], res["user"]["username"]["_content"]
        raise ValueError(f"ERR: {res.get('message', 'пользователь не найден')}")
    def _get_photo_exif(self, photo_id):
        url = "https://www.flickr.com/services/rest/"
        params = {
            "method": "flickr.photos.getExif",
            "api_key": self.api_key,
            "photo_id": photo_id,
            "format": "json",
            "nojsoncallback": 1
        }
        try:
            res = self.session.get(url, params=params).json()
            if res.get("stat") == "ok":
                cam = {"make": "Unknown", "model": "Unknown"}
                for tag in res["photo"]["exif"]:
                    if tag["tag"] == "Make": cam["make"] = tag["raw"]["_content"]
                    if tag["tag"] == "Model": cam["model"] = tag["raw"]["_content"]
                result = f"{cam['make']} {cam['model']}".strip()
                return "Неизвестное устройство - нет метаданных" if result == "Unknown Unknown" else result
        except Exception:
            pass
        return "Unknown Device"
    def get_user_heatmap_data(self, profile_url, limit=None, start_date=None, end_date=None, target_days=None, target_times=None):
        user_id, username = self._get_user_id(profile_url)
        url = "https://www.flickr.com/services/rest/"
        location_counts = defaultdict(int)
        location_ids = defaultdict(list)
        device_history = defaultdict(list)
        day_stats = defaultdict(int)
        hour_stats = defaultdict(int)
        photo_ids = []
        page = 1
        collected = 0
        while True:
            params = {
                "method": "flickr.photos.search",
                "api_key": self.api_key,
                "user_id": user_id,
                "has_geo": 1,
                "extras": "geo,date_taken",
                "per_page": 500,
                "page": page,
                "format": "json",
                "nojsoncallback": 1
            }
            if start_date: params["min_taken_date"] = start_date
            if end_date: params["max_taken_date"] = end_date
            res = self.session.get(url, params=params).json()
            if res.get("stat") != "ok": break
            photos = res["photos"]["photo"]
            if not photos: break
            for p in photos:
                try:
                    dt = datetime.strptime(p["datetaken"], "%Y-%m-%d %H:%M:%S")
                    p_day, p_hour = dt.weekday(), dt.hour
                except:
                    p_day, p_hour = None, None
                if target_days and str(p_day) not in target_days:
                    continue
                if target_times and p_hour is not None:
                    time_cat = None
                    if 6 <= p_hour < 12: time_cat = "morning"
                    elif 12 <= p_hour < 18: time_cat = "day"
                    elif 18 <= p_hour <= 23: time_cat = "evening"
                    else: time_cat = "night"
                    if time_cat not in target_times:
                        continue
                lat, lon = float(p["latitude"]), float(p["longitude"])
                if lat != 0 or lon != 0:
                    loc_key = (round(lat, 4), round(lon, 4))
                    location_counts[loc_key] += 1
                    location_ids[loc_key].append(p["id"]) 
                    photo_ids.append((p["id"], p["datetaken"]))
                    collected += 1
                    if p_day is not None: day_stats[p_day] += 1
                    if p_hour is not None: hour_stats[p_hour] += 1
                if limit and collected >= limit: break
            total_pages = res.get("photos", {}).get("pages", 1)
            if (limit and collected >= limit) or page >= total_pages: break
            page += 1
        with ThreadPoolExecutor(max_workers=10) as ex:
            futures = {ex.submit(self._get_photo_exif, pid): date for pid, date in photo_ids}
            for f in futures:
                date = futures[f]
                device_history[f.result()].append(date)
        dev_stats = []
        for d, dates in device_history.items():
            s = sorted(dates)
            dev_stats.append({"name": d, "first": s[0], "last": s[-1], "count": len(dates)})
        return username, location_counts, collected, dev_stats, day_stats, hour_stats, location_ids