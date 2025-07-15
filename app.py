# app.py

import streamlit as st
import math
from fpdf import FPDF
import io

# --- Configurazione pagina ---
st.set_page_config(page_title="Calcolatore Acustico Pro", layout="centered")

# --- Titolo ---
st.title("🎧 Calcolatore Acustico Pro")
st.markdown("""
Analisi acustica dell'ambiente per **registrazione**, **mixing**, **strumenti**, **podcast** e **amplificazione live**.
""")

# --- Input dimensioni ---
st.sidebar.header("📐 Dimensioni Ambiente")
length = st.sidebar.number_input("Lunghezza (m)", min_value=1.0, value=10.0, step=0.1)
width = st.sidebar.number_input("Larghezza (m)", min_value=1.0, value=8.0, step=0.1)
height = st.sidebar.number_input("Altezza (m)", min_value=2.0, value=3.0, step=0.1)

room_type = st.sidebar.selectbox("Tipo di ambiente", ["Studio", "Home studio", "Sala prove", "Sala concerti", "Auditorium"])
use_type = st.sidebar.selectbox("Uso principale", ["Registrazione", "Mixing", "Rehearsal", "Performance", "Podcast"])
instrument = st.sidebar.selectbox("Strumento/Ensemble", [
    "Voce/Podcast", "Pianoforte", "Batteria", "Chitarra acustica",
    "Orchestra", "Sezione Archi", "Ottoni", "Coro", "DJ Set"
])

# --- Materiali delle superfici ---
st.sidebar.header("🛋️ Materiali delle Superfici")
materiali = {}
materiali["Pareti"] = st.sidebar.selectbox("Pareti", ["Cemento", "Cartongesso", "Legno", "Vetro"])
materiali["Pavimento"] = st.sidebar.selectbox("Pavimento", ["Parquet", "Moquette", "Piastrelle", "Cemento"])
materiali["Soffitto"] = st.sidebar.selectbox("Soffitto", ["Cartongesso", "Cemento", "Legno", "Travi a vista"])

# --- Calcoli base ---
volume = length * width * height
surface = 2 * (length * width + length * height + width * height)
rt60_base = 0.161 * volume / (0.25 * surface)
rt60 = max(0.3, min(2.5, rt60_base))
schroeder = math.sqrt(rt60 * 340 * 340 / (1.316 * volume))
modes = {
    'Lunghezza': 340 / (2 * length),
    'Larghezza': 340 / (2 * width),
    'Altezza': 340 / (2 * height)
}
ratio_lw = length / width
ratio_quality = "Ottima" if abs(ratio_lw - 1.618) < 0.3 else "Buona" if abs(ratio_lw - 1.618) < 0.6 else "Da migliorare"

# --- Risultati Acustici ---
st.header("📊 Risultati Acustici")
st.metric("Volume", f"{volume:.1f} m³")
st.metric("Superficie", f"{surface:.1f} m²")
st.metric("RT60 stimato", f"{rt60:.2f} s")
st.metric("Frequenza di Schroeder", f"{schroeder:.0f} Hz")
st.write(f"**Proporzioni (L/W)**: {ratio_lw:.2f} -> {ratio_quality}")

with st.expander("📈 Modi Assiali"):
    for axis, freq in modes.items():
        st.write(f"• {axis}: {freq:.1f} Hz")

# --- Simulazione Trattamento Acustico ---
with st.expander("🎯 Simulazione del Trattamento Acustico"):
    trattamento = st.multiselect("Tipologie di trattamento da considerare", [
        "Pannelli fonoassorbenti",
        "Bass traps",
        "Diffusori acustici",
        "Tende pesanti",
        "Tappeti"
    ])
    if trattamento:
        st.success(f"Trattamenti selezionati: {', '.join(trattamento)}")
    else:
        st.info("Seleziona uno o più trattamenti da simulare.")

# --- Raccomandazioni ---
st.header("🧠 Raccomandazioni")
if rt60 > 1.5:
    st.subheader("🔷 RT60 troppo alto - Ambiente riverberante")
    st.write("- Usa pannelli fonoassorbenti (20-30% delle superfici)")
    st.write("- Inserisci bass traps negli angoli")
    st.write("- Aggiungi tende pesanti o tappeti")
elif rt60 < 0.4:
    st.subheader("🔹 RT60 troppo basso - Ambiente troppo secco")
    st.write("- Aggiungi pannelli diffusivi")
    st.write("- Utilizza superfici riflettenti in alcune zone")

if any(freq < 200 for freq in modes.values()):
    st.subheader("🔷 Modi assiali problematici sotto 200 Hz")
    st.write("- Installa bass traps profondi (oltre 20 cm)")
    st.write("- Posiziona i diffusori lontano dalle pareti")

# --- Setup consigliato ---
if use_type.lower() == "registrazione":
    st.subheader("🎤 Setup consigliato per Registrazione")
    st.write("- Crea una zona morta dietro il microfono")
    st.write("- Isola lateralmente la postazione")

if use_type.lower() == "mixing":
    st.subheader("🎧 Setup consigliato per Mixing")
    st.write("- Trattamento prime riflessioni (pareti e soffitto)")
    st.write("- Posizionamento dei monitor a triangolo equilatero")

# --- Verifica Setup Elettrico/Audio ---
with st.expander("🔌 Verifica setup elettrico/audio"):
    st.checkbox("Uso di cavi bilanciati (XLR/TRS)?")
    st.checkbox("Lunghezza cavi audio sotto i 10m?")
    st.checkbox("Assenza di ronzii o ground loop?")
    st.checkbox("Collegamenti corretti tra ampli e casse?")
    st.checkbox("Impedanze compatibili ampli ↔ casse?")
    st.checkbox("Alimentazione stabile e filtrata?")

# (Il resto del codice rimane invariato)
