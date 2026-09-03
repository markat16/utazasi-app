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
    
    # --- FIX HELYFOGLALÁS ---
    # Létrehozunk egy fix dobozt, ami alapból üres, így a térkép mindig ugyanott marad
    gomb_helye = st.container()
    
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
        
        # HTML Dizájn a buborékokhoz
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
            color, icon = "red", "lock"
            popup_html = f"""
            <div style='font-family: sans-serif; text-align: center; min-width: 160px;'>
                <h4>📍 {h_nev}</h4>
                <p style='color: green;'><b>Elég közel vagy!</b> (+{dist:.0f}m)</p>
                <p>Jutalom: {xp_reward} XP</p>
                <div style='background-color: #28a745; color: white; padding: 8px 16px; border-radius: 4px; font-weight: bold; display: inline-block;'>
                    🏁 Nyomd meg a fenti gombot!
                </div>
            </div>
            """
        else:
            color, icon = "red", "lock"
            popup_html = f"""
            <div style='font-family: sans-serif; text-align: center; color: #666; min-width: 160px;'>
                <h4>🔒 {h_nev}</h4>
                <p style='color: red;'>Túl messze vagy! ({dist/1000:.2f} km)</p>
                <div style='background-color: #ccc; color: #666; padding: 8px 16px; border-radius: 4px; font-weight: bold; display: inline-block;'>🏁 Zárolva</div>
            </div>
            """
            
        folium.Marker(
            location=[h_lat, h_lng], 
            popup=folium.Popup(popup_html, max_width=220), 
            icon=folium.Icon(color=color, icon=icon, prefix="fa")
        ).add_to(m)
        
    # Kirajzoljuk a térképet, és elmentjük a kattintási adatokat
    terkep_adat = st_folium(m, width=700, height=500, key="rpg_map_combined_v3")

    # 4. A TÉRKÉP FELETTI GOMB VEZÉRLÉSE
    if terkep_adat and terkep_adat.get("last_object_clicked"):
        klikkelt_lat = terkep_adat["last_object_clicked"]["lat"]
        klikkelt_lng = terkep_adat["last_object_clicked"]["lng"]
        
        # GOLYÓÁLLÓ KERESÉS: Megkeressük a sort, és a .to_dict('records')[0] segítségével azonnal tiszta Python szótárrá alakítjuk
        találatok = df[
            (abs(df['latitude'] - klikkelt_lat) < 0.0001) & 
            (abs(df['longitude'] - klikkelt_lng) < 0.0001)
        ].to_dict('records')
        
        if találatok:
            hely_adat = találatok[0]  # Kimásoljuk a legelső egyező helyet
            klikkelt_szoveg = hely_adat['name'].strip()
            xp_reward = hely_adat['xp_reward']
            
            dist = geodesic((user_lat, user_lng), (hely_adat['latitude'], hely_adat['longitude'])).meters
            
            # Beletesszük a gombot a térkép feletti üres dobozba
            with gomb_helye:
                st.write(f"### 📍 Kiválasztva: {klikkelt_szoveg}")
                
                if klikkelt_szoveg in st.session_state.completed_list:
                    st.success("Ezt a küldetést már teljesítetted! 🥇")
                elif dist > 150:
                    st.button(f"🔒 Küldetés lezárva (Még {dist/1000:.2f} km)", disabled=True)
                else:
                    if st.button(f"🏁 TELJESÍTEM A KÜLDETÉST: {klikkelt_szoveg} (+{xp_reward} XP)", type="primary"):
                        st.session_state.player_xp += xp_reward
                        st.session_state.completed_list.append(klikkelt_szoveg)
                        st.success(f"🎉 Sikeresen teljesítetted a helyszínt: {klikkelt_szoveg}!")
                        st.rerun()
        else:
            with gomb_helye:
                st.write(" ")
                st.write(" ")
    else:
        with gomb_helye:
            st.write(" ")
            st.write(" ")

except Exception as e:
    st.error(f"Hiba történt: {e}")
