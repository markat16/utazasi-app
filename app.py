import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic

st.set_page_config(page_title="Utazási RPG", layout="centered")

st.title("🗺️ Utazási Küldetések & RPG")

# 1. Pozíció szimulátor (Oldalsávban elrejthető)
st.sidebar.header("⚙️ Teszt Pozíció (GPS)")
user_lat = st.sidebar.number_input("Szélességi fok (Lat):", value=47.507500, format="%.6f")
user_lng = st.sidebar.number_input("Hosszúsági fok (Lng):", value=19.032500, format="%.6f")

# Játékos mentett állása a memóriában
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
    
    # Előkészítjük a térképváltozót a memóriában
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
            # BIZTONSÁGOS JAVÍTÁS: Külső gomb helyett egy olyan űrlapot használunk, amit a Streamlit belső proxyja átenged
            color, icon = "red", "lock"
            popup_html = f"""
            <div style='font-family: sans-serif; text-align: center; min-width: 160px;'>
                <h4>📍 {h_nev}</h4>
                <p style='color: green;'><b>Elég közel vagy!</b> (+{dist:.0f}m)</p>
                <p>Jutalom: {xp_reward} XP</p>
                <form action="" method="get" target="_parent">
                    <input type="hidden" name="complete_quest" value="{h_nev}">
                    <button type="submit" style='background-color: #28a745; color: white; padding: 8px 16px; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; display: inline-block;'>
                        🏁 Teljesítés!
                    </button>
                </form>
            </div>
            """
        else:
            # HA TÚL MESSZE VAN: Szürke, inaktív gomb kinézet
            color, icon = "red", "lock"
            popup_html = f"""
            <div style='font-family: sans-serif; text-align: center; color: #666; min-width: 160px;'>
                <h4>🔒 {h_nev}</h4>
                <p style='color: red;'>Túl messze vagy! ({dist/1000:.2f} km)</p>
                <button disabled style='background-color: #ccc; color: #666; padding: 8px 16px; border: none; border-radius: 4px; font-weight: bold;'>
                    🏁 Zárolva
                </button>
            </div>
            """
            
        folium.Marker(
            location=[h_lat, h_lng], 
            popup=folium.Popup(popup_html, max_width=220), 
            icon=folium.Icon(color=color, icon=icon, prefix="fa")
        ).add_to(m)
        
    # Kirajzoljuk a térképet
    terkep_adat = st_folium(m, width=700, height=500, key="rpg_map_final_proxy")

    # 4. VALÓDI GOMBNYOMÁS ELLENŐRZÉSE (A proxy-n átengedett belső parancs alapján)
    query_params = st.query_params
    if "complete_quest" in query_params:
        target_quest = query_params["complete_quest"].strip()
        
        if target_quest not in st.session_state.completed_list:
            hely_adat = df[df['name'] == target_quest]
            if not hely_adat.empty:
                hely_adat = hely_adat.iloc
                
                # Szerver oldali távolság ellenőrzés
                dist = geodesic((user_lat, user_lng), (hely_adat['latitude'], hely_adat['longitude'])).meters
                if dist <= 150:
                    st.session_state.player_xp += hely_adat['xp_reward']
                    st.session_state.completed_list.append(target_quest)
                    
                    st.query_params.clear()
                    st.success(f"🎉 Sikeresen teljesítetted a helyszínt: {target_quest}!")
                    st.rerun()

except Exception as e:
    st.error(f"Hiba történt: {e}")
