# app.py

import streamlit as st
import math
from fpdf import FPDF
import io
import plotly.graph_objects as go

# --- Configurazione pagina ---
st.set_page_config(page_title="Calcolatore Acustico Pro", layout="centered")

# --- Sidebar: Input base e materiali ---
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

# --- Pagina principale ---
st.title("🎧 Calcolatore Acustico Pro")
st.markdown("""
Analisi acustica dell'ambiente per **registrazione**, **mixing**, **strumenti**, **podcast** e **amplificazione live**.
""")

st.header("📊 Risultati Acustici")
col1, col2, col3 = st.columns(3)
col1.metric("Volume", f"{volume:.1f} m³")
col2.metric("Superficie", f"{surface:.1f} m²")
col3.metric("RT60 stimato", f"{rt60:.2f} s")
st.metric("Frequenza di Schroeder", f"{schroeder:.0f} Hz")
st.write(f"**Proporzioni (L/W)**: {ratio_lw:.2f} → {ratio_quality}")

with st.expander("📈 Modi Assiali"):
    for axis, freq in modes.items():
        st.write(f"• {axis}: {freq:.1f} Hz")

st.header("🧠 Raccomandazioni")
if rt60 > 1.5:
    st.warning("RT60 troppo alto - Ambiente riverberante")
    st.write("- Usa pannelli fonoassorbenti (20-30% delle superfici)")
    st.write("- Inserisci bass traps negli angoli")
    st.write("- Aggiungi tende pesanti o tappeti")
elif rt60 < 0.4:
    st.info("RT60 troppo basso - Ambiente troppo secco")
    st.write("- Aggiungi pannelli diffusivi")
    st.write("- Utilizza superfici riflettenti in alcune zone")

if any(freq < 200 for freq in modes.values()):
    st.warning("Modi assiali problematici sotto 200 Hz")
    st.write("- Installa bass traps profondi (oltre 20 cm)")
    st.write("- Posiziona i diffusori lontano dalle pareti")

if use_type.lower() == "registrazione":
    st.subheader("🎤 Setup consigliato per Registrazione")
    st.write("- Crea una zona morta dietro il microfono")
    st.write("- Isola lateralmente la postazione")

if use_type.lower() == "mixing":
    st.subheader("🎧 Setup consigliato per Mixing")
    st.write("- Trattamento prime riflessioni (pareti e soffitto)")
    st.write("- Posizionamento dei monitor a triangolo equilatero")

# --- Sezione casse passive ---
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

# --- Sezione casse attive ---
st.header("🔊 Dettagli Casse Attive")
marca_cassa_attiva = st.text_input("Marca Cassa Attiva", value="QSC")
modello_cassa_attiva = st.text_input("Modello Cassa Attiva", value="K12.2")
potenza_nominale_attiva = st.number_input("Potenza Nominale Cassa Attiva (W)", min_value=10, max_value=5000, value=1000)
num_casse_attive = st.selectbox("Numero di Casse Attive", options=[0,1,2,4,8], index=0)
num_woofer_attivi = st.number_input("Numero di Woofer per Cassa Attiva", min_value=1, step=1, value=1)

# --- Sezione amplificazione e casse ---
st.header("🧲 Amplificazione e Numero di Casse")
speakers_passive = st.selectbox("Numero di Casse Passive", options=[1,2,4,8], index=1)
use_sub = st.checkbox("Vuoi includere Subwoofer?")
num_subwoofer = 0
potenza_nominale_sub = 0
if use_sub:
    num_subwoofer = st.number_input("Numero di Subwoofer", min_value=1, max_value=8, value=1)
    potenza_nominale_sub = st.number_input("Potenza Nominale Subwoofer (W)", min_value=50, max_value=2000, value=300)

distanza_ascoltatore = st.number_input("Distanza dell'ascoltatore dalle casse (m)", min_value=0.5, max_value=50.0, value=4.0)

# --- Calcolo SPL ---
fattore_direttività = 0 if tipo_diffusore == "Omnidirezionale" else 3
spl_effettivo = sensibilita + 10 * math.log10(potenza_massima) - 20 * math.log10(distanza_ascoltatore) + fattore_direttività + (10 * math.log10(num_woofer))

# SPL casse attive
if num_casse_attive > 0:
    spl_attive = 95 + 10 * math.log10(potenza_nominale_attiva) - 20 * math.log10(distanza_ascoltatore) + (10 * math.log10(num_woofer_attivi))
else:
    spl_attive = 0

# SPL subwoofer (semplice stima)
if use_sub and num_subwoofer > 0:
    spl_sub = 95 + 10 * math.log10(potenza_nominale_sub) - 20 * math.log10(distanza_ascoltatore)
else:
    spl_sub = 0

base_watt = math.ceil(volume * 2)
rt_factor = 0.7 if rt60 > 1.0 else 1.3
wattage = math.ceil(base_watt * rt_factor)
potenza_finale_ampli = potenza_nominale_cassa * speakers_passive + potenza_nominale_sub * num_subwoofer + potenza_nominale_attiva * num_casse_attive

tot_casse = speakers_passive + num_casse_attive + num_subwoofer

st.metric("Potenza consigliata", f"{wattage} W")
st.metric("Numero totale casse", f"{tot_casse} (Passive: {speakers_passive}, Attive: {num_casse_attive}, Subwoofer: {num_subwoofer})")
st.metric("Potenza totale consigliata per Amplificatore", f"{potenza_finale_ampli} W")
st.metric("SPL stimato all'ascoltatore (Passive)", f"{spl_effettivo:.1f} dB")
if num_casse_attive > 0:
    st.metric("SPL stimato all'ascoltatore (Attive)", f"{spl_attive:.1f} dB")
if use_sub and num_subwoofer > 0:
    st.metric("SPL stimato all'ascoltatore (Subwoofer)", f"{spl_sub:.1f} dB")

# --- Grafico SPL a tendina ---
with st.expander("📊 Visualizza Grafico SPL stimato"):
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Casse Passive', x=["Passive"], y=[spl_effettivo]))
    if num_casse_attive > 0:
        fig.add_trace(go.Bar(name='Casse Attive', x=["Attive"], y=[spl_attive]))
    if use_sub and num_subwoofer > 0:
        fig.add_trace(go.Bar(name='Subwoofer', x=["Subwoofer"], y=[spl_sub]))
    fig.update_layout(yaxis_title="dB SPL", barmode='group')
    st.plotly_chart(fig, use_container_width=True)

# --- Adattabilità per Strumento ---
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

    pdf.cell(0, 10, f"Materiali Pareti: {materiali['Pareti']}", ln=True)
    pdf.cell(0, 10, f"Materiali Pavimento: {materiali['Pavimento']}", ln=True)
    pdf.cell(0, 10, f"Materiali Soffitto: {materiali['Soffitto']}", ln=True)

    pdf.cell(0, 10, f"Marca Cassa: {marca_cassa}", ln=True)
    pdf.cell(0, 10, f"Modello Cassa: {modello_cassa}", ln=True)
    pdf.cell(0, 10, f"Tipo Cassa: {tipo_cassa}", ln=True)
    pdf.cell(0, 10, f"Tipo Diffusore: {tipo_diffusore}", ln=True)
    pdf.cell(0, 10, f"Sensibilità: {sensibilita} dB SPL @1W/1m", ln=True)
    pdf.cell(0, 10, f"Numero Woofer per Cassa: {num_woofer}", ln=True)
    pdf.cell(0, 10, f"Potenza Nominale Cassa: {potenza_nominale_cassa} W", ln=True)

    pdf.cell(0, 10, f"Marca Cassa Attiva: {marca_cassa_attiva}", ln=True)
    pdf.cell(0, 10, f"Modello Cassa Attiva: {modello_cassa_attiva}", ln=True)
    pdf.cell(0, 10, f"Potenza Nominale Cassa Attiva: {potenza_nominale_attiva} W", ln=True)
    pdf.cell(0, 10, f"Numero Casse Attive: {num_casse_attive}", ln=True)
    pdf.cell(0, 10, f"Numero Woofer per Cassa Attiva: {num_woofer_attivi}", ln=True)

    pdf.cell(0, 10, f"Numero Casse Passive: {speakers_passive}", ln=True)
    pdf.cell(0, 10, f"Numero Subwoofer: {num_subwoofer}", ln=True)
    if use_sub:
        pdf.cell(0, 10, f"Potenza Nominale Subwoofer: {potenza_nominale_sub} W", ln=True)

    pdf.cell(0, 10, f"Potenza Totale Richiesta Amplificatore: {potenza_finale_ampli} W", ln=True)
    pdf.cell(0, 10, f"SPL stimato Casse Passive: {spl_effettivo:.1f} dB", ln=True)
    if num_casse_attive > 0:
        pdf.cell(0, 10, f"SPL stimato Casse Attive: {spl_attive:.1f} dB", ln=True)
    if use_sub and num_subwoofer > 0:
        pdf.cell(0, 10, f"SPL stimato Subwoofer: {spl_sub:.1f} dB", ln=True)
    pdf.cell(0, 10, f"Distanza ascoltatore: {distanza_ascoltatore} m", ln=True)

    pdf_output = pdf.output(dest='S').encode('latin1', 'replace')
    pdf_buffer = io.BytesIO(pdf_output)

    st.download_button(
        label="Download PDF",
        data=pdf_buffer,
        file_name="calcolatore_acustico_pro_report.pdf",
        mime="application/pdf"
    )
