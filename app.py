import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic

st.set_page_config(page_title="Utazási RPG", layout="centered")

st.title("🗺️ Utazási Küldetések & RPG")
st.write("Kattints a térképen egy helyszínre a részletekért!")

# 1. Játékos pozíció szimulátor (Teszteléshez)
st.sidebar.header("⚙️ Teszt Pozíció (GPS)")
user_lat = st.sidebar.number_input("Szélességi fok (Lat):", value=47.507500, format="%.6f")
user_lng = st.sidebar.number_input("Hosszúsági fok (Lng):", value=19.032500, format="%.6f")

# Játékos memóriájának betöltése
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
    st.metric(label="🏆 Megszerzett Pontszámod (XP)", value=f"{st.session_state.player_xp} XP")
    
    # 3. Térkép felépítése
    m = folium.Map(location=[user_lat, user_lng], zoom_start=14)
    
    # Te ikonod
    folium.Marker([user_lat, user_lng], popup="Te itt vagy!", icon=folium.Icon(color="blue", icon="user", prefix="fa")).add_to(m)
    
    # Küldetések ikonjai
    for index, row in df.iterrows():
        h_nev = row['name']
        h_lat, h_lng = row['latitude'], row['longitude']
        
        if h_nev in st.session_state.completed_list:
            color, icon = "green", "check"
        else:
            color, icon = "red", "lock"
            
        # FONTOS: A popup tartalma pontosan a helyszín neve kell legyen, mert a kód ebből azonosítja be!
        folium.Marker([h_lat, h_lng], popup=h_nev, icon=folium.Icon(color=color, icon=icon, prefix="fa")).add_to(m)
        
    # Kirajzoljuk a térképet és elmentjük a kattintásokat a 'terkep_adat' változóba
    terkep_adat = st_folium(m, width=700, height=450)
    
    # 4. DINAMIKUS KÜLDETÉS PANEL (Csak akkor jelenik meg, ha rákattintasz egy pontra)
    if terkep_adat and terkep_adat.get("last_object_clicked_popup"):
        # Megszerezzük a kattintott hely nevét és megtisztítjuk a felesleges szóközöktől
        kivalasztott_hely = terkep_adat["last_object_clicked_popup"].strip()
        
        # Megkeressük a hely adatait a táblázatban
        hely_adat = df[df['name'] == kivalasztott_hely]
        
        if not hely_adat.empty:
            hely_adat = hely_adat.iloc[0]
            q_lat, q_lng = hely_adat['latitude'], hely_adat['longitude']
            xp_reward = hely_adat['xp_reward']
            
            st.write("---")
            st.subheader(f"📍 Kiválasztott helyszín: {kivalasztott_hely}")
            st.write(f"**Kategória:** {hely_adat['category']} | **Jutalom:** {xp_reward} XP")
            
            # Kiszámoljuk a távolságot
            tavolsag = geodesic((user_lat, user_lng), (q_lat, q_lng)).meters
            
            # ELLENŐRZÉSEK:
            if kivalasztott_hely in st.session_state.completed_list:
                st.info(f"Ezt a küldetést már teljesítetted! ✓")
            
            # HA TÚL MESSZE VAN -> Szürke, lezárt gomb (disabled=True)
            elif tavolsag > 150:
                st.button(f"🔒 Küldetés zárolva (Még {tavolsag/1000:.2f} km-re vagy)", disabled=True)
                st.error("Nem vagy elég közel a helyszínhez! A teljesítéshez menj 150 méteren belülre.")
                
            # HA ELÉG KÖZEL VAN -> Aktív, kattintható gomb!
            else:
                if st.button(f"🏁 {kivalasztott_hely} Teljesítése!"):
                    st.session_state.player_xp += xp_reward
                    st.session_state.completed_list.append(kivalasztott_hely)
                    st.success(f"🎉 Gratulálunk! Megkaptad a(z) {xp_reward} XP-t!")
                    st.rerun()

except Exception as e:
    st.error(f"Hiba történt: {e}")
