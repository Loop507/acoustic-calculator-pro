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

# --- Output risultati acustici ---
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
    st.write("- Usa pannelli fonoassorbenti (20–30% delle superfici)")
    st.write("- Inserisci bass traps negli angoli")
    st.write("- Aggiungi tende pesanti o tappeti")
elif rt60 < 0.4:
    st.subheader("🟨 RT60 troppo basso → Ambiente troppo secco")
    st.write("- Aggiungi pannelli diffusivi")
    st.write("- Utilizza superfici riflettenti in alcune zone")

if any(freq < 200 for freq in modes.values()):
    st.subheader("🟥 Modi assiali problematici < 200 Hz")
    st.write("- Installa bass traps profondi (> 20cm)")
    st.write("- Posiziona i diffusori lontano dalle pareti")

if use_type.lower() == "registrazione":
    st.subheader("🎙️ Setup consigliato per Registrazione")
    st.write("- Crea una zona morta dietro il microfono")
    st.write("- Isola lateralmente la postazione")

if use_type.lower() == "mixing":
    st.subheader("🎛️ Setup consigliato per Mixing")
    st.write("- Trattamento prime riflessioni (pareti e soffitto)")
    st.write("- Posizionamento dei monitor a triangolo equilatero")

# --- Calcolo amplificazione ---
st.header("🔊 Amplificazione e Posizionamento Casse")
base_watt = math.ceil(volume * 2)
rt_factor = 0.7 if rt60 > 1.0 else 1.3
wattage = math.ceil(base_watt * rt_factor)

max_dim = max(length, width)
if max_dim > 15:
    speakers = 4
    config = "Stereo + Fill"
elif max_dim > 8:
    speakers = 2
    config = "Stereo"
else:
    speakers = 1
    config = "Mono"

# Nuova selezione: numero casse e subwoofer
st.subheader("Configurazione Casse")
num_speakers = st.selectbox("Numero di casse", [1, 2, 4])
has_sub = st.checkbox("Includi Subwoofer")

st.metric("Potenza consigliata", f"{wattage} W")
st.metric("Configurazione casse", f"{num_speakers} casse {'con subwoofer' if has_sub else 'senza subwoofer'} ({config})")

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

# --- Esporta report in PDF ---
if st.button("Genera e scarica PDF report"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Calcolatore Acustico Pro - Report", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Dimensioni ambiente: {length}m x {width}m x {height}m", ln=True)
    pdf.cell(0, 10, f"Tipo ambiente: {room_type}", ln=True)
    pdf.cell(0, 10, f"Uso principale: {use_type}", ln=True)
    pdf.cell(0, 10, f"Strumento/Ensemble: {instrument}", ln=True)
    pdf.ln(5)

    pdf.cell(0, 10, f"Volume: {volume:.1f} m³", ln=True)
    pdf.cell(0, 10, f"Superficie: {surface:.1f} m²", ln=True)
    pdf.cell(0, 10, f"RT60 stimato: {rt60:.2f} s", ln=True)
    pdf.cell(0, 10, f"Frequenza di Schroeder: {schroeder:.0f} Hz", ln=True)
    pdf.cell(0, 10, f"Proporzioni (L/W): {ratio_lw:.2f} → {ratio_quality}", ln=True)
    pdf.ln(5)

    pdf.cell(0, 10, "Modi assiali:", ln=True)
    for axis, freq in modes.items():
        pdf.cell(0, 10, f"  • {axis}: {freq:.1f} Hz", ln=True)
    pdf.ln(5)

    pdf.cell(0, 10, "Raccomandazioni:", ln=True)
    if rt60 > 1.5:
        pdf.cell(0, 10, " - RT60 troppo alto → Usa pannelli fonoassorbenti e bass traps", ln=True)
    elif rt60 < 0.4:
        pdf.cell(0, 10, " - RT60 troppo basso → Usa pannelli diffusivi e superfici riflettenti", ln=True)
    else:
        pdf.cell(0, 10, " - RT60 nei parametri consigliati", ln=True)
    pdf.ln(5)

    pdf.cell(0, 10, f"Potenza consigliata: {wattage} W", ln=True)
    pdf.cell(0, 10, f"Configurazione casse: {num_speakers} casse {'con subwoofer' if has_sub else 'senza subwoofer'} ({config})", ln=True)
    pdf.ln(10)

    pdf.cell(0, 10, f"Adattabilità per {instrument}: {suitability}", ln=True)
    pdf.cell(0, 10, f"RT60 ideale: {rt_range[0]}–{rt_range[1]}s | Attuale: {rt60:.2f}s", ln=True)
    pdf.cell(0, 10, f"Volume ideale: {vol_range[0]}–{vol_range[1]}m³ | Attuale: {volume:.1f}m³", ln=True)

    # Genera PDF in memoria
    pdf_bytes = pdf.output(dest='S').encode('latin1')

    st.download_button(
        label="Scarica PDF",
        data=pdf_bytes,
        file_name="acoustic_report.pdf",
        mime="application/pdf"
    )
