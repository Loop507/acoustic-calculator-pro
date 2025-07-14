import streamlit as st
import math

st.set_page_config(page_title="Calcolatore Acustico Pro", layout="centered")

st.title("🎧 Calcolatore Acustico Pro - Versione Avanzata")
st.markdown("""
Analisi acustica dettagliata per ambienti di registrazione, mixing, performance e amplificazione.
""")

# Input dimensioni ambiente
st.header("📐 Dimensioni Ambiente")
col1, col2, col3 = st.columns(3)
with col1:
    length = st.number_input("Lunghezza (m)", min_value=1.0, value=10.0, step=0.1)
with col2:
    width = st.number_input("Larghezza (m)", min_value=1.0, value=8.0, step=0.1)
with col3:
    height = st.number_input("Altezza (m)", min_value=2.0, value=3.0, step=0.1)

# Coefficienti di assorbimento superficiale
st.header("🎛️ Assorbimento Superfici (valori da 0 a 1)")
col1, col2, col3 = st.columns(3)
with col1:
    alpha_walls = st.slider("Pareti", 0.0, 1.0, 0.2, 0.01)
with col2:
    alpha_floor = st.slider("Pavimento", 0.0, 1.0, 0.1, 0.01)
with col3:
    alpha_ceiling = st.slider("Soffitto", 0.0, 1.0, 0.15, 0.01)

# Tipo d'uso e strumento
room_type = st.selectbox("Tipo di ambiente", ["Studio", "Home studio", "Sala prove", "Sala concerti", "Auditorium"])
use_type = st.selectbox("Uso principale", ["Registrazione", "Mixing", "Rehearsal", "Performance", "Podcast"])
instrument = st.selectbox("Strumento/Ensemble", [
    "Voce/Podcast", "Pianoforte", "Batteria", "Chitarra acustica",
    "Orchestra", "Sezione Archi", "Ottoni", "Coro", "DJ Set"
])

# Configurazione casse
st.header("🔊 Configurazione Impianto")
speaker_num = st.selectbox("Numero casse", [2, 4])
subwoofer = st.checkbox("Includi Subwoofer")

# Calcoli base
volume = length * width * height
surface_area = 2 * (length*width + length*height + width*height)

# Calcolo tempo di riverberazione RT60 per bande di frequenza (Sabine modificato)
def rt60_sabine(volume, surface_area, alpha):
    if alpha == 0:
        return 10.0  # infinito virtuale se assorbimento zero
    return 0.161 * volume / (alpha * surface_area)

# Media ponderata assorbimento
average_alpha = (alpha_walls * (2*(length*height + width*height)) + alpha_floor * (length*width) + alpha_ceiling * (length*width)) / surface_area

# RT60 a banda larga (media)
rt60 = rt60_sabine(volume, surface_area, average_alpha)
rt60 = max(0.2, min(rt60, 3.0))

# RT60 per frequenze standard - approssimazione semplice con variazione di coefficente alpha
freq_bands = [125, 250, 500, 1000, 2000]
alpha_freq = {
    125: average_alpha * 0.8,
    250: average_alpha * 0.85,
    500: average_alpha * 0.9,
    1000: average_alpha,
    2000: average_alpha * 1.1,
}

rt60_bands = {f: rt60_sabine(volume, surface_area, max(alpha_freq[f],0.01)) for f in freq_bands}

# Modi assiali base (Hz)
modes = {
    'Lunghezza': 340 / (2 * length),
    'Larghezza': 340 / (2 * width),
    'Altezza': 340 / (2 * height)
}

# Proporzione stanza
ratio_lw = length / width
ratio_quality = "Ottima" if abs(ratio_lw - 1.618) < 0.3 else "Buona" if abs(ratio_lw - 1.618) < 0.6 else "Da migliorare"

# Output risultati
st.header("📊 Risultati Acustici")
st.metric("Volume", f"{volume:.1f} m³")
st.metric("Superficie Totale", f"{surface_area:.1f} m²")
st.metric("RT60 (media)", f"{rt60:.2f} s")

st.write("**RT60 per frequenze (s):**")
cols = st.columns(len(freq_bands))
for i, f in enumerate(freq_bands):
    cols[i].metric(f"{f} Hz", f"{rt60_bands[f]:.2f}")

st.write(f"**Proporzioni stanza (L/W)**: {ratio_lw:.2f} → {ratio_quality}")

st.subheader("Modi assiali (Hz)")
for axis, freq in modes.items():
    st.write(f"- {axis}: {freq:.1f} Hz")

# Raccomandazioni
st.header("🧠 Raccomandazioni")

if rt60 > 1.8:
    st.warning("🟥 RT60 troppo alto → Ambiente riverberante. Consigli: pannelli fonoassorbenti, bass traps, tende/pavimenti morbidi.")
elif rt60 < 0.3:
    st.warning("🟨 RT60 troppo basso → Ambiente troppo secco. Consigli: superfici riflettenti, pannelli diffusivi.")

if any(freq < 200 for freq in modes.values()):
    st.warning("🟥 Modi assiali problematici < 200 Hz → Consiglio bass traps profondi (> 20cm) e posizionamento casse strategico.")

if use_type.lower() == "registrazione":
    st.info("🎙️ Setup consigliato per Registrazione: zona morta dietro microfono e isolamento laterale.")
elif use_type.lower() == "mixing":
    st.info("🎛️ Setup consigliato per Mixing: trattamento prime riflessioni e posizionamento monitor a triangolo equilatero.")

# Calcolo potenza amplificazione
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

# Override configurazione casse con input utente
speakers = speaker_num
config = f"{speakers}-channel"
if subwoofer:
    config += " + Subwoofer"

st.header("🎚️ Configurazione Impianto")
st.write(f"**Numero casse:** {speakers}")
st.write(f"**Configurazione:** {config}")
st.write(f"**Potenza consigliata totale:** {wattage} W")

# Adattabilità per strumento selezionato
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
st.write(f"RT60 ideale: {rt_range[0]}–{rt_range[1]} s | Attuale: {rt60:.2f} s → {'✅' if rt_ok else '❌'}")
st.write(f"Volume ideale: {vol_range[0]}–{vol_range[1]} m³ | Attuale: {volume:.1f} m³ → {'✅' if vol_ok else '❌'}")
