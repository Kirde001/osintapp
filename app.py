import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import reverse_geocoder as rg
import pycountry
from flask import Flask, render_template, request, flash
from flickr_api import FlickrOSINT
from babel import Locale
from dotenv import load_dotenv
import os
app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv("FLASK_KEY")
if not app.secret_key:
    raise RuntimeError("Переменная окружения flask не установлена")
def get_statistics(location_data):
    if not location_data: return [], []
    coords = list(location_data.keys())
    results = rg.search(coords)
    country_stats, city_stats = {}, {}
    loc_ru = Locale('ru')
    for (coord, count), geo in zip(location_data.items(), results):
        cc = geo.get('cc', 'Unknown')
        city = geo.get('name', 'Unknown City')  
        if cc != 'Unknown':
            c_name_ru = loc_ru.territories.get(cc.upper())
            if not c_name_ru: 
                c_obj = pycountry.countries.get(alpha_2=cc)
                c_name_ru = c_obj.name if c_obj else cc
        else:
            c_name_ru = 'Неизвестная страна - ошибка библиотеки Babel'
        country_stats[c_name_ru] = country_stats.get(c_name_ru, 0) + count
        key = f"{city} ({c_name_ru})"
        city_stats[key] = city_stats.get(key, 0) + count
    return sorted(country_stats.items(), key=lambda x: x[1], reverse=True), \
           sorted(city_stats.items(), key=lambda x: x[1], reverse=True)
def generate_map(location_data, location_ids):
    if not location_data: return None
    data = []
    max_count = max(location_data.values()) if location_data else 1
    for (lat, lon), count in location_data.items():
        p_ids = location_ids.get((lat, lon), [])
        ids_text = ", ".join(p_ids[:3])
        if len(p_ids) > 3:
            ids_text += f" (+ еще {len(p_ids) - 3})"
        data.append({
            "lat": lat, 
            "lon": lon,
            "ID фото": ids_text,
            "Фото": count, 
            "size": min(4 + (count * 1.0), 20),
            "Действие": "Кликнуть для открытия панорамы"
        })
    df = pd.DataFrame(data)
    avg_lat = df["lat"].mean()
    avg_lon = df["lon"].mean()
    custom_colors = ["#ffeb3b", "#f44336", "#000000"]
    fig = px.scatter_mapbox(
        df, lat="lat", lon="lon", size="size", color="Фото",
        hover_data={"lat": True, "lon": True, "size": False, "ID фото": True, "Фото": True, "Действие": True},
        center={"lat": avg_lat, "lon": avg_lon},
        zoom=3,
        color_continuous_scale=custom_colors,
        size_max=15
    )
    df_black_text = df[df["Фото"] < (max_count * 0.4)]
    df_white_text = df[df["Фото"] >= (max_count * 0.4)]
    if not df_black_text.empty:
        fig.add_trace(go.Scattermapbox(
            lat=df_black_text["lat"],
            lon=df_black_text["lon"],
            mode='text',
            text=df_black_text["Фото"].astype(str),
            textfont=dict(color='black', size=13, family='Arial Black'),
            hoverinfo='skip',
            showlegend=False
        ))
    if not df_white_text.empty:
        fig.add_trace(go.Scattermapbox(
            lat=df_white_text["lat"],
            lon=df_white_text["lon"],
            mode='text',
            text=df_white_text["Фото"].astype(str),
            textfont=dict(color='white', size=13, family='Arial Black'),
            hoverinfo='skip',
            showlegend=False
        ))
    fig.update_layout(
        mapbox_style="carto-positron",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=600,
        coloraxis_showscale=False
    )
    return fig.to_html(full_html=False, include_plotlyjs='cdn', default_height='100%', default_width='100%', div_id='osint-map')
@app.route("/", methods=["GET", "POST"])
def index():
    data = {"map_html": None, "stats_countries": [], "stats_cities": [], "device_stats": [], "habit_days": {}, "habit_time": {}}
    fields = ["target_url", "max_photos", "start_date", "end_date"]
    for f in fields: data[f] = request.form.get(f, "")
    data["target_days"] = request.form.getlist("target_day")
    data["target_times"] = request.form.getlist("target_time")
    if request.method == "POST":
        try:
            client = FlickrOSINT()
            limit = int(data["max_photos"]) if data["max_photos"].isdigit() else None
            username, locs, coll, devs, d_stats, h_stats, loc_ids = client.get_user_heatmap_data(
                data["target_url"], limit=limit, start_date=data["start_date"], 
                end_date=data["end_date"], target_days=data["target_days"], target_times=data["target_times"]
            )
            if not locs:
                flash("Данных не найдено - стоит изменить фильтры/ профиль приватный", "warning")
            else:
                data["map_html"] = generate_map(locs, loc_ids)
                data["stats_countries"], data["stats_cities"] = get_statistics(locs)
                data["device_stats"] = devs
                d_map = {0: "Пн", 1: "Вт", 2: "Ср", 3: "Чт", 4: "Пт", 5: "Сб", 6: "Вс"}
                data["habit_days"] = {d_map[d]: c for d, c in sorted(d_stats.items(), key=lambda x: x[0])}
                t_groups = {"Утро (06-12)": 0, "День (12-18)": 0, "Вечер (18-00)": 0, "Ночь (00-06)": 0}
                for h, c in h_stats.items():
                    if 6 <= h < 12: t_groups["Утро (06-12)"] += c
                    elif 12 <= h < 18: t_groups["День (12-18)"] += c
                    elif 18 <= h <= 23: t_groups["Вечер (18-00)"] += c
                    else: t_groups["Ночь (00-06)"] += c
                data["habit_time"] = {k: v for k, v in t_groups.items() if v > 0}
                flash(f"Проанализировано {coll} фото профиля {username}", "success")
        except Exception as e:
            flash(f"ERR: {str(e)}", "danger")
    return render_template("index.html", **data)
if __name__ == "__main__":
    app.run(debug=True, port=5000)