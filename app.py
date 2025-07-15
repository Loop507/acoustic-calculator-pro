# app.py

import streamlit as st
import math
from fpdf import FPDF
import io
import plotly.graph_objects as go

# --- Configurazione pagina ---
st.set_page_config(page_title="Calcolatore Acustico Pro", layout="centered")

# --- Titolo ---
st.title("🎧 Calcolatore Acustico Pro")
st.markdown("""
Analisi acustica dell'ambiente per **registrazione**, **mixing**, **strumenti**, **podcast** e **amplificazione live**.
""")

# --- Input dimensioni ---
st.header("📀 Dimensioni Ambiente")
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

# --- Dettagli Casse Passive ---
st.header("🔊 Dettagli Casse Passive")
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
num_woofer = st.number_input("Numero di Woofer per Cassa", min_value=1, step=1, value=1)

# --- Dettagli Casse Attive ---
st.header("🔊 Dettagli Casse Attive")
marca_cassa_attiva = st.text_input("Marca Cassa Attiva", value="Mackie")
modello_cassa_attiva = st.text_input("Modello Cassa Attiva", value="THUMP15A")
sensibilita_attiva = st.number_input("Sensibilità Cassa Attiva (dB SPL @1W/1m)", min_value=70.0, max_value=130.0, value=92.0)
potenza_massima_attiva = st.number_input("Potenza Massima Cassa Attiva (W)", min_value=50, max_value=5000, value=600)
num_woofer_attiva = st.number_input("Numero di Woofer per Cassa Attiva", min_value=1, step=1, value=1)

# --- Dettagli Amplificatore ---
st.header("🎚 Dettagli Amplificatore")
modello_ampli = st.text_input("Modello Amplificatore", value="Yamaha RX-V6A")

# --- Amplificazione e Numero di Casse ---
st.header("🧲 Amplificazione e Numero di Casse")
speakers = st.selectbox("Numero di Casse Passive", options=[1, 2, 4, 8], index=1)
use_sub = st.checkbox("Vuoi includere Subwoofer?")
num_subwoofer = 0
potenza_nominale_sub = 0
if use_sub:
    num_subwoofer = st.number_input("Numero di Subwoofer", min_value=1, max_value=8, value=1)
    potenza_nominale_sub = st.number_input("Potenza Nominale Subwoofer (W)", min_value=50, max_value=2000, value=300)

distanza_ascoltatore = st.number_input("Distanza dell'ascoltatore dalle casse (m)", min_value=0.5, max_value=50.0, value=4.0)

# Calcolo SPL stimato considerando casse passive
fattore_direttività = 0 if tipo_diffusore == "Omnidirezionale" else 3
spl_effettivo_passive = sensibilita + 10 * math.log10(potenza_massima) - 20 * math.log10(distanza_ascoltatore) + fattore_direttività + (10 * math.log10(num_woofer))

# Calcolo SPL stimato per casse attive
spl_effettivo_attive = sensibilita_attiva + 10 * math.log10(potenza_massima_attiva) - 20 * math.log10(distanza_ascoltatore) + fattore_direttività + (10 * math.log10(num_woofer_attiva))

base_watt = math.ceil(volume * 2)
rt_factor = 0.7 if rt60 > 1.0 else 1.3
wattage = math.ceil(base_watt * rt_factor)
potenza_finale_ampli = potenza_nominale_cassa * speakers + potenza_nominale_sub * num_subwoofer

st.metric("Potenza consigliata", f"{wattage} W")
st.metric("Numero di casse passive", f"{speakers}")
st.metric("Numero di subwoofer", f"{num_subwoofer}")
st.metric("Potenza totale consigliata per Amplificatore", f"{potenza_finale_ampli} W")
st.metric("SPL stimato all'ascoltatore (casse passive)", f"{spl_effettivo_passive:.1f} dB")
st.metric("SPL stimato all'ascoltatore (casse attive)", f"{spl_effettivo_attive:.1f} dB")

# --- Grafico SPL stimato ---
with st.expander("📊 Visualizza Grafico SPL stimato"):
    distanze = [i/2 for i in range(1, 21)]  # da 0.5 a 10 m
    spl_vals_passive = [
        sensibilita + 10*math.log10(potenza_massima) - 20*math.log10(d) + fattore_direttività + (10*math.log10(num_woofer))
        for d in distanze
    ]
    spl_vals_attive = [
        sensibilita_attiva + 10*math.log10(potenza_massima_attiva) - 20*math.log10(d) + fattore_direttività + (10*math.log10(num_woofer_attiva))
        for d in distanze
    ]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=distanze, y=spl_vals_passive, mode='lines+markers', name='SPL Casse Passive (dB)'))
    fig.add_trace(go.Scatter(x=distanze, y=spl_vals_attive, mode='lines+markers', name='SPL Casse Attive (dB)'))
    fig.update_layout(
        xaxis_title='Distanza ascoltatore (m)',
        yaxis_title='SPL stimato (dB)',
        yaxis=dict(range=[min(min(spl_vals_passive), min(spl_vals_attive))-5, max(max(spl_vals_passive), max(spl_vals_attive))+5]),
        template='plotly_white'
    )
    st.plotly_chart(fig, use_container_width=True)

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

    pdf.cell(0, 10, f"Materiali Pareti: {materiali['Pareti']}", ln=True)
    pdf.cell(0, 10, f"Materiali Pavimento: {materiali['Pavimento']}", ln=True)
    pdf.cell(0, 10, f"Materiali Soffitto: {materiali['Soffitto']}", ln=True)

    pdf.cell(0, 10, f"Marca Cassa Passive: {marca_cassa}", ln=True)
    pdf.cell(0, 10, f"Modello Cassa Passive: {modello_cassa}", ln=True)
    pdf.cell(0, 10, f"Tipo Cassa Passive: {tipo_cassa}", ln=True)
    pdf.cell(0, 10, f"Tipo Diffusore Passive: {tipo_diffusore}", ln=True)
    pdf.cell(0, 10, f"Sensibilità Passive: {sensibilita} dB SPL @1W/1m", ln=True)
    pdf.cell(0, 10, f"Numero Woofer Passive: {num_woofer}", ln=True)
    pdf.cell(0, 10, f"Potenza Nominale Cassa Passive: {potenza_nominale_cassa} W", ln=True)

    pdf.cell(0, 10, f"Marca Cassa Attive: {marca_cassa_attiva}", ln=True)
    pdf.cell(0, 10, f"Modello Cassa Attive: {modello_cassa_attiva}", ln=True)
    pdf.cell(0, 10, f"Sensibilità Attive: {sensibilita_attiva} dB SPL @1W/1m", ln=True)
    pdf.cell(0, 10, f"Potenza Massima Cassa Attiva: {potenza_massima_attiva} W", ln=True)
    pdf.cell(0, 10, f"Numero Woofer Attive: {num_woofer_attiva}", ln=True)

    pdf.cell(0, 10, f"Modello Amplificatore: {modello_ampli}", ln=True)
    pdf.cell(0, 10, f"Numero Casse Passive: {speakers}", ln=True)
    pdf.cell(0, 10, f"Numero Subwoofer: {num_subwoofer}", ln=True)
    if use_sub:
        pdf.cell(0, 10, f"Potenza Nominale Subwoofer: {potenza_nominale_sub} W", ln=True)
    pdf.cell(0, 10, f"Potenza Totale Richiesta Amplificatore: {potenza_finale_ampli} W", ln=True)
    pdf.cell(0, 10, f"SPL stimato (Passive): {spl_effettivo_passive:.1f} dB", ln=True)
    pdf.cell(0, 10, f"SPL stimato (Active): {spl_effettivo_attive:.1f} dB", ln=True)
    pdf.cell(0, 10, f"Distanza ascoltatore: {distanza_ascoltatore} m", ln=True)

    pdf_output = pdf.output(dest='S').encode('latin1', 'replace')
    pdf_buffer = io.BytesIO(pdf_output)

    st.download_button(
        label="Download PDF",
        data=pdf_buffer,
        file_name="calcolatore_acustico_pro_report.pdf",
        mime="application/pdf"
    )
