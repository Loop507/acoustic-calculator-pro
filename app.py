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
st.write(f"**Proporzioni (L/W)**: {ratio_lw:.2f} -> {ratio_quality}")

with st.expander("📈 Modi Assiali"):
    for axis, freq in modes.items():
        st.write(f"• {axis}: {freq:.1f} Hz")

# --- Raccomandazioni acustiche ---
st.header("🧠 Raccomandazioni")
if rt60 > 1.5:
    st.subheader("🟥 RT60 troppo alto - Ambiente riverberante")
    st.write("- Usa pannelli fonoassorbenti (20-30% delle superfici)")
    st.write("- Inserisci bass traps negli angoli")
    st.write("- Aggiungi tende pesanti o tappeti")
elif rt60 < 0.4:
    st.subheader("🟨 RT60 troppo basso - Ambiente troppo secco")
    st.write("- Aggiungi pannelli diffusivi")
    st.write("- Utilizza superfici riflettenti in alcune zone")

if any(freq < 200 for freq in modes.values()):
    st.subheader("🟥 Modi assiali problematici sotto 200 Hz")
    st.write("- Installa bass traps profondi (oltre 20 cm)")
    st.write("- Posiziona i diffusori lontano dalle pareti")

if use_type.lower() == "registrazione":
    st.subheader("🎙️ Setup consigliato per Registrazione")
    st.write("- Crea una zona morta dietro il microfono")
    st.write("- Isola lateralmente la postazione")

if use_type.lower() == "mixing":
    st.subheader("🎛️ Setup consigliato per Mixing")
    st.write("- Trattamento prime riflessioni (pareti e soffitto)")
    st.write("- Posizionamento dei monitor a triangolo equilatero")

# --- Input dettagli casse e amplificatore ---
st.header("🔊 Dettagli Casse e Amplificatore")

marca_cassa = st.text_input("Marca Cassa", value="JBL")
modello_cassa = st.text_input("Modello Cassa", value="EON615")

tipo_cassa = st.selectbox("Tipo Cassa", ["Bass Reflex", "Dipolo", "Pneumatica"])
tipo_diffusore = st.selectbox("Tipo Diffusore", ["Omnidirezionale", "A Tromba"])

impedenza = st.number_input("Impedenza (Ohm)", min_value=2, max_value=16, value=8)
risposta_freq = st.text_input("Risposta in frequenza (Hz)", value="50-20000")

sensibilita = st.number_input("Sensibilità (dB SPL @1W/1m)", min_value=70.0, max_value=130.0, value=90.0)
spl_nominale = st.number_input("SPL Nominale Cassa (dB SPL)", min_value=70.0, max_value=130.0, value=95.0)

potenza_massima = st.number_input("Potenza Massima Cassa (W)", min_value=50, max_value=5000, value=500)
potenza_nominale_cassa = st.number_input("Potenza Nominale Cassa (W)", min_value=10, max_value=5000, value=300)

modello_ampli = st.text_input("Modello Amplificatore", value="Yamaha RX-V6A")

# --- Calcolo amplificazione ---
st.header("🔊 Amplificazione e Numero di Casse")
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

st.metric("Potenza consigliata", f"{wattage} W")
st.metric("Numero di casse", f"{speakers} ({config})")

potenza_finale_ampli = potenza_nominale_cassa * speakers
st.metric("Potenza finale Amplificatore consigliata", f"{potenza_finale_ampli} W")

# --- Calcolo avanzato SPL ---
st.header("🔬 Calcolo SPL Avanzato")
with st.expander("Parametri Avanzati Casse Audio"):
    distanza_ascoltatore = st.number_input("Distanza dell'Ascoltatore (m)", min_value=0.1, value=4.0)
    num_woofer = st.number_input("Numero di Woofer", min_value=1, step=1, value=1)

    fattore_direttivita = 0 if tipo_diffusore == "Omnidirezionale" else 3
    spl_effettivo = spl_nominale + 10 * math.log10(potenza_massima) - 20 * math.log10(distanza_ascoltatore) + fattore_direttivita + (10 * math.log10(num_woofer))

    st.metric("SPL stimato all'ascoltatore", f"{spl_effettivo:.1f} dB")

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
st.write(f"RT60 ideale: {rt_range[0]}-{rt_range[1]}s | Attuale: {rt60:.2f}s -> {'✅' if rt_ok else '❌'}")
st.write(f"Volume ideale: {vol_range[0]}-{vol_range[1]}m³ | Attuale: {volume:.1f}m³ -> {'✅' if vol_ok else '❌'}")

# --- Esportazione PDF ---
if st.button("📥 Esporta in PDF"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(0, 10, "Calcolatore Acustico Pro - Report", ln=True)
    pdf.cell(0, 10, f"Dimensioni Ambiente: {length} x {width} x {height} m", ln=True)
    pdf.cell(0, 10, f"Volume: {volume:.1f} m³", ln=True)
    pdf.cell(0, 10, f"Superficie: {surface:.1f} m²", ln=True)
    pdf.cell(0, 10, f"RT60 stimato: {rt60:.2f} s", ln=True)
    pdf.cell(0, 10, f"Frequenza di Schroeder: {schroeder:.0f} Hz", ln=True)
    pdf.cell(0, 10, f"Proporzioni (L/W): {ratio_lw:.2f} -> {ratio_quality}", ln=True)
    pdf.cell(0, 10, f"Potenza consigliata: {wattage} W", ln=True)
    pdf.cell(0, 10, f"Numero casse: {speakers} ({config})", ln=True)
    pdf.cell(0, 10, f"Potenza finale Amplificatore consigliata: {potenza_finale_ampli} W", ln=True)
    pdf.cell(0, 10, f"SPL stimato all'ascoltatore: {spl_effettivo:.1f} dB", ln=True)

    pdf.cell(0, 10, f"Marca Cassa: {marca_cassa}", ln=True)
    pdf.cell(0, 10, f"Modello Cassa: {modello_cassa}", ln=True)
    pdf.cell(0, 10, f"Tipo Cassa: {tipo_cassa}", ln=True)
    pdf.cell(0, 10, f"Tipo Diffusore: {tipo_diffusore}", ln=True)
    pdf.cell(0, 10, f"Impedenza: {impedenza} Ohm", ln=True)
    pdf.cell(0, 10, f"Risposta in Frequenza: {risposta_freq} Hz", ln=True)
    pdf.cell(0, 10, f"Sensibilità: {sensibilita} dB SPL @1W/1m", ln=True)
    pdf.cell(0, 10, f"SPL Nominale: {spl_nominale} dB SPL", ln=True)
    pdf.cell(0, 10, f"Potenza Massima Cassa: {potenza_massima} W", ln=True)
    pdf.cell(0, 10, f"Potenza Nominale Cassa: {potenza_nominale_cassa} W", ln=True)
    pdf.cell(0, 10, f"Modello Amplificatore: {modello_ampli}", ln=True)

    pdf_output = pdf.output(dest='S').encode('latin1', 'replace')
    pdf_buffer = io.BytesIO(pdf_output)

    st.download_button(
        label="Download PDF",
        data=pdf_buffer,
        file_name="calcolatore_acustico_pro_report.pdf",
        mime="application/pdf"
    )
