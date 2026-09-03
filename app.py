import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic

# 1. Oldal beállítása mobilbarát nézethez
st.set_page_config(page_title="Utazási RPG", layout="centered")

st.title("🗺️ Utazási Küldetések & RPG")
st.write("Teljesíts küldetéseket a valóságban és gyűjts XP-t!")

# Pozíció szimulátor a teszteléshez (mivel a böngésző GPS-hez extra engedély kell)
st.sidebar.header("⚙️ Teszt Pozíció (GPS)")
user_lat = st.sidebar.number_input("Szélességi fok (Lat):", value=47.507500, format="%.6f")
user_lng = st.sidebar.number_input("Hosszúsági fok (Lng):", value=19.032500, format="%.6f")

# 2. CSV Beolvasása (az adatbázisod)
@st.cache_data
def load_data():
    # Feltételezzük, hogy a kuldetesek.csv is ebben a mappában lesz
    return pd.read_csv('kuldetesek.csv', sep=';', encoding='latin2')

try:
    df = load_data()
    
    # 3. Pontszámítás és logika
    total_xp = 0
    completed_quests = []
    
    for index, row in df.iterrows():
        dist = geodesic((user_lat, user_lng), (row['latitude'], row['longitude'])).meters
        if dist <= 150:
            total_xp += row['xp_reward']
            completed_quests.append(row['name'])
            
    # Pontszám kijelzése
    st.metric(label="🏆 Összesített Pontszámod (XP)", value=f"{total_xp} XP")
    
    # 4. Térkép kirajzolása
    m = folium.Map(location=[user_lat, user_lng], zoom_start=14)
    
    # Felhasználó ikonja
    folium.Marker([user_lat, user_lng], popup="Te itt vagy!", icon=folium.Icon(color="blue", icon="user", prefix="fa")).add_to(m)
    
    # Küldetések ikonjai
    for index, row in df.iterrows():
        q_lat, q_lng = row['latitude'], row['longitude']
        dist = geodesic((user_lat, user_lng), (q_lat, q_lng)).meters
        
        if dist <= 150:
            color, icon = "green", "check"
            status = "TELJESÍTVE!"
        else:
            color, icon = "red", "lock"
            status = f"ZÁRT ({dist/1000:.2f} km-re vagy)"
            
        popup_text = f"<b>{row['name']}</b><br>{status}<br>Jutalom: {row['xp_reward']} XP"
        folium.Marker([q_lat, q_lng], popup=popup_text, icon=folium.Icon(color=color, icon=icon, prefix="fa")).add_to(m)
        
    # Térkép megjelenítése a Streamlitben
    st_folium(m, width=700, height=450)
    
except Exception as e:
    st.error(f"Hiba történt az adatok beolvasásakor. Kérlek győződj meg róla, hogy feltöltötted a 'kuldetesek.csv' fájlt is! Részletek: {e}")
