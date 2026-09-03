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
    
    # Pontszám kijelzése
    st.metric(label="🏆 Megszerzett Pontszámod", value=f"{st.session_state.player_xp} XP")
    
    # Előkészítjük a térképváltozót a memóriában
    m = folium.Map(location=[user_lat, user_lng], zoom_start=15)
    
    # Felhasználó kék ikonja
    folium.Marker([user_lat, user_lng], popup="Te itt vagy!", icon=folium.Icon(color="blue", icon="user", prefix="fa")).add_to(m)
    
    # Küldetések ikonjainak feltétele a térképre
    for index, row in df.iterrows():
        h_nev = row['name'].strip()
        h_lat, h_lng = row['latitude'], row['longitude']
        
        # Ha már teljesítette, zöld pipa, különben piros lakat
        if h_nev in st.session_state.completed_list:
            color, icon = "green", "check"
            popup_text = f"<b>{h_nev}</b><br>✓ Teljesítve!"
        else:
            color, icon = "red", "lock"
            popup_text = f"<b>{h_nev}</b><br>🔒 Kattints a térkép feletti gombra a pontért!"
            
        folium.Marker(
            location=[h_lat, h_lng],
            popup=popup_text,
            icon=folium.Icon(color=color, icon=icon, prefix="fa")
        ).add_to(m)
        
    # --- 3. DINAMIKUS AKCIÓGOMB A TÉRKÉP FELETT ---
    # Létrehozunk egy üres helyet (konténert) a gombnak a térkép FELETT
    gomb_helye = st.container()
    
    # Kirajzoljuk a térképet, és figyeljük, hova kattint a felhasználó
    terkep_adat = st_folium(m, width=700, height=480, key="rpg_map_v2")
    
    # Megnézzük, hogy rákattintott-e egy pontra a térképen
    if terkep_adat and terkep_adat.get("last_object_clicked_popup"):
        # Megszerezzük a kiválasztott hely nevét a felugró ablakból (kitakarítva a HTML-t ha van)
        klikkelt_szoveg = terkep_adat["last_object_clicked_popup"].split("<br>")[0].replace("<b>", "").replace("</b>", "").strip()
        
        # Megkeressük ezt a helyet a táblázatban
        hely_adat = df[df['name'] == klikkelt_szoveg]
        
        if not hely_adat.empty:
            hely_adat = hely_adat.iloc
            q_lat, q_lng = hely_adat['latitude'], hely_adat['longitude']
            xp_reward = hely_adat['xp_reward']
            
            # Kiszámoljuk a távolságot a gomb kirajzolása előtt
            dist = geodesic((user_lat, user_lng), (q_lat, q_lng)).meters
            
            # Beletesszük a megfelelő gombot a térkép feletti üres helyre
            with gomb_helye:
                st.info(f"📍 Kiválasztott helyszín: **{klikkelt_szoveg}** ({row['category']})")
                
                if klikkelt_szoveg in st.session_state.completed_list:
                    st.success("Ezt a küldetést már sikeresen teljesítetted! 🥇")
                    
                elif dist > 150:
                    # HA MESSZE VAN: Szürke, lezárt gomb
                    st.button(f"🔒 Küldetés lezárva (Még {dist/1000:.2f} km-re vagy)", disabled=True)
                    st.error("Menj közelebb a helyszínhez (150 méteren belülre), hogy feloldd a küldetést!")
                    
                else:
                    # HA KÖZEL VAN: Aktív, nagy zöld gomb!
                    if st.button(f"🏁 TELJESÍTEM A KÜLDETÉST: {klikkelt_szoveg} (+{xp_reward} XP)"):
                        st.session_state.player_xp += xp_reward
                        st.session_state.completed_list.append(klikkelt_szoveg)
                        st.success(f"🎉 Gratulálunk! Jóváírva: {xp_reward} XP!")
                        st.rerun()

except Exception as e:
    st.error(f"Hiba történt a rendszerben: {e}")
