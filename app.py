import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic

st.set_page_config(page_title="Utazási RPG", layout="centered")

st.title("🗺️ Utazási Küldetések & RPG")

# 1. Pozíció szimulátor (A képernyő szélén elrejthető)
st.sidebar.header("⚙️ Teszt Pozíció (GPS)")
user_lat = st.sidebar.number_input("Szélességi fok (Lat):", value=47.507500, format="%.6f")
user_lng = st.sidebar.number_input("Hosszúsági fok (Lng):", value=19.032500, format="%.6f")

# Játékos pontjainak kezelése
if 'player_xp' not in st.session_state:
    st.session_state.player_xp = 0
if 'completed_list' not in st.session_state:
    st.session_state.completed_list = []

# 2. Adatok beolvasása
@st.cache_data
def load_data():
    return pd.read_csv('kuldetesek.csv', sep=';', encoding='latin2')

try:
    df = load_data()
    
    # Pontszám kijelzése diszkréten a térkép felett
    st.metric(label="🏆 Megszerzett Pontszámod", value=f"{st.session_state.player_xp} XP")
    
    # 3. Térkép felépítése
    m = folium.Map(location=[user_lat, user_lng], zoom_start=15)
    
    # Felhasználó kék ikonja
    folium.Marker([user_lat, user_lng], popup="Te itt vagy!", icon=folium.Icon(color="blue", icon="user", prefix="fa")).add_to(m)
    
    # Küldetések ikonjainak generálása
    for index, row in df.iterrows():
        h_nev = row['name'].strip()
        h_lat, h_lng = row['latitude'], row['longitude']
        xp_reward = row['xp_reward']
        
        # Kiszámoljuk a távolságot az adott ponthoz
        dist = geodesic((user_lat, user_lng), (h_lat, h_lng)).meters
        
        # HTML Dizájn a gombokhoz a felugró ablakban
        if h_nev in st.session_state.completed_list:
            color, icon = "green", "check"
            popup_html = f"""
            <div style='font-family: sans-serif; text-align: center;'>
                <h4>✅ {h_nev}</h4>
                <p style='color: green;'><b>Küldetés teljesítve!</b></p>
                <p>Kapott jutalom: {xp_reward} XP</p>
            </div>
            """
        elif dist <= 150:
            # HA KÖZEL VAN: Aktív, kattintható stílusú gomb (A popup szövege lesz a kulcs)
            color, icon = "red", "lock"
            popup_html = f"""
            <div style='font-family: sans-serif; text-align: center; min-width: 150px;'>
                <h4>📍 {h_nev}</h4>
                <p style='color: green;'><b>Elég közel vagy!</b> (+{dist:.0f}m)</p>
                <p>Jutalom: {xp_reward} XP</p>
                <b style='background-color: #28a745; color: white; padding: 6px 12px; border-radius: 4px; display: inline-block; cursor: pointer;'>Kattints a térkép alatt a megerősítéshez!</b>
                <span style='display:none;'>{h_nev}</span>
            </div>
            """
        else:
            # HA TÚL MESSZE VAN: Szürke, inaktív gomb kinézet
            color, icon = "red", "lock"
            popup_html = f"""
            <div style='font-family: sans-serif; text-align: center; color: #666; min-width: 150px;'>
                <h4>🔒 {h_nev}</h4>
                <p style='color: red;'>Túl messze vagy! ({dist/1000:.2f} km)</p>
                <div style='background-color: #ccc; color: #666; padding: 6px 12px; border-radius: 4px; display: inline-block;'>🏁 Küldetés zárolva</div>
            </div>
            """
            
        folium.Marker(
            location=[h_lat, h_lng], 
            popup=folium.Popup(popup_html, max_width=200), 
            icon=folium.Icon(color=color, icon=icon, prefix="fa")
        ).add_to(m)
        
    # Kirajzoljuk a térképet
    terkep_adat = st_folium(m, width=700, height=500)
    
    # 4. Háttérben futó ellenőrzés a kattintásra
    if terkep_adat and terkep_adat.get("last_object_clicked_popup"):
        raw_popup = terkep_adat["last_object_clicked_popup"]
        
        # Megkeressük a rejtett helynevet a HTML kódból
        for index, row in df.iterrows():
            h_nev = row['name'].strip()
            if h_nev in raw_popup and h_nev not in st.session_state.completed_list:
                dist = geodesic((user_lat, user_lng), (row['latitude'], row['longitude'])).meters
                if dist <= 150:
                    st.session_state.player_xp += row['xp_reward']
                    st.session_state.completed_list.append(h_nev)
                    st.success(f"🎉 Sikeresen teljesítetted a helyszínt: {h_nev}! (+{row['xp_reward']} XP)")
                    st.rerun()

except Exception as e:
    st.error(f"Hiba történt: {e}")
