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
Analisi acustica completa dell'ambiente per **registrazione**, **mixing**, **strumenti**, **podcast** e **amplificazione live**.
""")

# --- Input dimensioni ---
st.header("📐 Dimensioni Ambiente")
col1, col2, col3 = st.columns(3)
with col1:
    length = st.number_input("Lunghezza (m)", min_value=1.0, value=10.0, step=0.1)
with col2:
    width = st.number_input("Larghezza (m)", min_value=1.0, value=8.0, step=0.1)
with col3:
    height = st.number_input("Altezza (m)", min_value=2.0, value=3.0, step=0.1)

room_type = st.selectbox("Tipo di ambiente", ["Studio", "Home studio", "Sala prove", "Sala concerti", "Auditorium"])
use_type = st.selectbox("Uso principale", ["Registrazione", "Mixing", "Rehearsal", "Performance", "Podcast"])
instrument = st.selectbox("Strumento/Ensemble", [
    "Voce/Podcast", "Pianoforte", "Batteria", "Chitarra acustica",
    "Orchestra", "Sezione Archi", "Ottoni", "Coro", "DJ Set"
])
speakers_choice = st.radio("Numero di casse", [2, 4])
include_sub = st.checkbox("Includi subwoofer")

# --- Calcoli ---
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

# --- Output ---
st.header("📊 Risultati Acustici")
st.metric("Volume", f"{volume:.1f} m³")
st.metric("Superficie", f"{surface:.1f} m²")
st.metric("RT60 stimato", f"{rt60:.2f} s")
st.metric("Frequenza di Schroeder", f"{schroeder:.0f} Hz")
st.write(f"**Proporzioni (L/W)**: {ratio_lw:.2f} → {ratio_quality}")

with st.expander("📈 Modi Assiali"):
    for axis, freq in modes.items():
        st.write(f"• {axis}: {freq:.1f} Hz")

# --- Raccomandazioni acustiche ---
st.header("🧠 Raccomandazioni")
if rt60 > 1.5:
    st.subheader("🟥 RT60 troppo alto → Ambiente riverberante")
    st.write("- Pannelli fonoassorbenti (20–30%)")
    st.write("- Bass traps negli angoli")
    st.write("- Tende pesanti o tappeti")
elif rt60 < 0.4:
    st.subheader("🟨 RT60 troppo basso → Ambiente troppo secco")
    st.write("- Aggiungi pannelli diffusivi")
    st.write("- Superfici riflettenti")

if any(freq < 200 for freq in modes.values()):
    st.subheader("🟥 Modi assiali problematici < 200 Hz")
    st.write("- Bass traps profondi (> 20cm)")
    st.write("- Posizionamento casse lontano dalle pareti")

if use_type.lower() == "registrazione":
    st.subheader("🎙️ Setup per Registrazione")
    st.write("- Zona morta dietro microfono")
    st.write("- Isolamento laterale")

if use_type.lower() == "mixing":
    st.subheader("🎛️ Setup per Mixing")
    st.write("- Trattamento prime riflessioni")
    st.write("- Posizionamento monitor a triangolo")

# --- Calcolo amplificazione ---
st.header("🔊 Amplificazione")
base_watt = math.ceil(volume * 2)
rt_factor = 0.7 if rt60 > 1.0 else 1.3
wattage = math.ceil(base_watt * rt_factor)

config = f"{speakers_choice} casse"
if include_sub:
    config += " + Subwoofer"

st.metric("Potenza consigliata", f"{wattage} W")
st.metric("Configurazione", config)

# --- Adattabilità per strumento selezionato ---
st.header("🎼 Adattabilità per Strumento")
instrument_data = {
    "Voce/Podcast": ([0.3, 0.6], [20, 80]),
    "Pianoforte": ([0.6, 1.2], [50, 200]),
    "Batteria": ([0.4, 0.8], [30, 150]),
    "Chitarra acustica": ([0.5, 1.0], [25, 100]),
    "Orchestra": ([1.0, 2.0], [200, 1000]),
    "Sezione Archi": ([0.8, 1.5], [100, 300]),
    "Ottoni": ([0.6, 1.2], [80, 250]),
    "Coro": ([1.0, 1.8], [150, 500]),
    "DJ Set": ([0.3, 0.7], [50, 300]),
}
rt_range, vol_range = instrument_data[instrument]
rt_ok = rt_range[0] <= rt60 <= rt_range[1]
vol_ok = vol_range[0] <= volume <= vol_range[1]
suitability = "Eccellente" if rt_ok and vol_ok else "Buona" if rt_ok or vol_ok else "Limitata"

st.write(f"**Adattabilità per {instrument}**: {suitability}")
st.write(f"RT60 ideale: {rt_range[0]}–{rt_range[1]}s | Attuale: {rt60:.2f}s → {'✅' if rt_ok else '❌'}")
st.write(f"Volume ideale: {vol_range[0]}–{vol_range[1]}m³ | Attuale: {volume:.1f}m³ → {'✅' if vol_ok else '❌'}")

# --- PDF export ---
st.header("📄 Esporta i risultati")
if st.button("⬇️ Scarica PDF"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Calcolatore Acustico Pro", ln=True, align='C')
    pdf.ln(5)
    pdf.cell(200, 10, txt=f"Ambiente: {length}m x {width}m x {height}m", ln=True)
    pdf.cell(200, 10, txt=f"Volume: {volume:.1f} m³ | Superficie: {surface:.1f} m²", ln=True)
    pdf.cell(200, 10, txt=f"RT60 stimato: {rt60:.2f} s | Schroeder: {schroeder:.0f} Hz", ln=True)
    pdf.cell(200, 10, txt=f"Casse: {speakers_choice} + Sub: {'Sì' if include_sub else 'No'}", ln=True)
    pdf.cell(200, 10, txt=f"Potenza consigliata: {wattage} W", ln=True)
    pdf.cell(200, 10, txt=f"Adattabilità per {instrument}: {suitability}", ln=True)

    pdf_buffer = io.BytesIO()
    pdf.output(pdf_buffer)
    st.download_button("📥 Scarica PDF", data=pdf_buffer.getvalue(), file_name="acustica_output.pdf", mime="application/pdf")
