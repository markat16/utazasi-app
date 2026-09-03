import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic

st.set_page_config(page_title="Utazási RPG", layout="centered")

st.title("🗺️ Utazási Küldetések & RPG")
st.write("Érj oda a helyszínre, és kattints a teljesítés gombra!")

# 1. Pozíció szimulátor a teszteléshez
st.sidebar.header("⚙️ Teszt Pozíció (GPS)")
user_lat = st.sidebar.number_input("Szélességi fok (Lat):", value=47.507500, format="%.6f")
user_lng = st.sidebar.number_input("Hosszúsági fok (Lng):", value=19.032500, format="%.6f")

# Játékos pontjainak tárolása a munkamenetben (hogy ne vesszen el gombnyomáskor)
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
    
    # Pontszám kijelzése a lap tetején
    st.metric(label="🏆 Megszerzett Pontszámod (XP)", value=f"{st.session_state.player_xp} XP")
    
    # 3. INTERAKTÍV KÜLDETÉSI PANEL
    st.subheader("⚔️ Elérhető Küldetések")
    
    # Kiválasztható legördülő lista a küldetésekről
    valasztott_hely = st.selectbox("Melyik küldetést szeretnéd teljesíteni?", df['name'].tolist())
    
    # Megkeressük a kiválasztott hely adatait a táblázatban
    hely_adat = df[df['name'] == valasztott_hely].iloc[0]
    q_lat, q_lng = hely_adat['latitude'], hely_adat['longitude']
    xp_reward = hely_adat['xp_reward']
    
    # A NAGY "KÜLDETÉS TELJESÍTÉSE" GOMB
    if st.button(f"🏁 {valasztott_hely} Teljesítése!"):
        # Ellenőrizzük, hogy már teljesítette-e
        if valasztott_hely in st.session_state.completed_list:
            st.warning(f"Ezt a küldetést ({valasztott_hely}) már korábban teljesítetted!")
        else:
            # Kiszámoljuk a távolságot a gomb megnyomásának pillanatában
            tavolsag = geodesic((user_lat, user_lng), (q_lat, q_lng)).meters
            
            # HA ELÉG KÖZEL VAN (150 méter)
            if tavolsag <= 150:
                st.success(f"🎉 SIKER! Teljesítetted a(z) {valasztott_hely} küldetést! Jutalom: +{xp_reward} XP!")
                st.session_state.player_xp += xp_reward
                st.session_state.completed_list.append(valasztott_hely)
                st.rerun()
            # HA TÚL MESSZE VAN
            else:
                st.error(f"❌ Még nem vagy elég közel! {tavolsag/1000:.2f} km-re vagy a helyszíntől. Menj közelebb!")

    # 4. Térkép kirajzolása
    m = folium.Map(location=[user_lat, user_lng], zoom_start=14)
    
    # Te helyzeted
    folium.Marker([user_lat, user_lng], popup="Te itt vagy!", icon=folium.Icon(color="blue", icon="user", prefix="fa")).add_to(m)
    
    # Küldetések kirajzolása
    for index, row in df.iterrows():
        h_nev = row['name']
        h_lat, h_lng = row['latitude'], row['longitude']
        
        # A térképen a szín aszerint változik, hogy a játékos már RÉGEBBEN megszerezte-e a pontot
        if h_nev in st.session_state.completed_list:
            color, icon = "green", "check"
            popup_txt = f"<b>{h_nev}</b><br>✓ TELJESÍTVE!"
        else:
            color, icon = "red", "lock"
            popup_txt = f"<b>{h_nev}</b><br>🔒 ZÁRT KÜLDETÉS"
            
        folium.Marker([h_lat, h_lng], popup=popup_txt, icon=folium.Icon(color=color, icon=icon, prefix="fa")).add_to(m)
        
    st_folium(m, width=700, height=450)
    
    # Teljesített küldetések listája alul
    if st.session_state.completed_list:
        st.write("---")
        st.subheader("🥇 Eddigi trófeáid ezen az utazáson:")
        for teljesitett in st.session_state.completed_list:
            st.write(f"• {teljesitett} (Teljesítve)")

except Exception as e:
    st.error(f"Hiba történt: {e}")
