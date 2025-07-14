import streamlit as st
import sqlite3
import math
import io
from datetime import datetime
import matplotlib.pyplot as plt
from fpdf import FPDF

# Configurazione pagina
st.set_page_config(
    page_title="Calcolatore Acustico Pro Avanzato",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def init_database():
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    
    # Tabella casse
    cursor.execute('''
        CREATE TABLE speakers (
            id INTEGER PRIMARY KEY,
            brand TEXT,
            model TEXT,
            type TEXT,
            impedance INTEGER,
            sensitivity REAL,
            max_power INTEGER,
            freq_response_low INTEGER,
            freq_response_high INTEGER,
            directivity TEXT,
            price_range TEXT
        )
    ''')
    speakers_data = [
        ('JBL', 'EON615', 'Attiva', 8, 90, 1000, 39, 20000, 'A Tromba', 'Media'),
        ('Yamaha', 'DXR12', 'Attiva', 8, 96, 1100, 42, 20000, 'A Tromba', 'Media'),
        ('QSC', 'K12.2', 'Attiva', 8, 98, 2000, 45, 20000, 'A Tromba', 'Alta'),
        ('Mackie', 'Thump15A', 'Attiva', 8, 95, 1400, 40, 20000, 'A Tromba', 'Bassa'),
        ('RCF', 'ART 732-A', 'Attiva', 8, 94, 600, 52, 20000, 'A Tromba', 'Media')
    ]
    cursor.executemany('INSERT INTO speakers (brand, model, type, impedance, sensitivity, max_power, freq_response_low, freq_response_high, directivity, price_range) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', speakers_data)
    
    # Tabella materiali
    cursor.execute('''
        CREATE TABLE materials (
            id INTEGER PRIMARY KEY,
            name TEXT,
            absorption_125 REAL,
            absorption_250 REAL,
            absorption_500 REAL,
            absorption_1000 REAL,
            absorption_2000 REAL,
            absorption_4000 REAL
        )
    ''')
    materials_data = [
        ('Muro intonacato', 0.14, 0.10, 0.06, 0.07, 0.09, 0.06),
        ('Cemento nudo', 0.02, 0.02, 0.02, 0.02, 0.02, 0.02),
        ('Legno', 0.15, 0.11, 0.10, 0.07, 0.06, 0.07),
        ('Tappeto leggero', 0.02, 0.06, 0.14, 0.37, 0.60, 0.65),
        ('Tappeto pesante', 0.08, 0.24, 0.57, 0.69, 0.71, 0.73),
        ('Pannelli fonoassorbenti', 0.60, 0.80, 0.90, 0.90, 0.90, 0.90),
        ('Vetro', 0.35, 0.25, 0.18, 0.12, 0.07, 0.04),
        ('Moquette', 0.04, 0.10, 0.35, 0.60, 0.70, 0.70),
        ('Cartongesso', 0.29, 0.10, 0.05, 0.04, 0.07, 0.04)
    ]
    cursor.executemany('INSERT INTO materials (name, absorption_125, absorption_250, absorption_500, absorption_1000, absorption_2000, absorption_4000) VALUES (?, ?, ?, ?, ?, ?, ?)', materials_data)
    
    conn.commit()
    return conn

def calculate_rt60_per_band(volume, surface_materials, materials_db_rows):
    frequencies = [125, 250, 500, 1000, 2000, 4000]
    rt60_values = []
    
    materials_dict = {row[1]: {
        125: row[2], 250: row[3], 500: row[4], 1000: row[5], 2000: row[6], 4000: row[7]
    } for row in materials_db_rows}
    
    for freq in frequencies:
        total_absorption = 0
        for material_name, area in surface_materials.items():
            absorption_coeff = materials_dict.get(material_name, {}).get(freq, 0.25)
            total_absorption += area * absorption_coeff
        
        if total_absorption > 0:
            rt60 = 0.161 * volume / total_absorption
            rt60 = max(0.1, min(5.0, rt60))
            rt60_values.append(rt60)
        else:
            rt60_values.append(1.0)
    
    return frequencies, rt60_values

def calculate_room_modes(length, width, height, max_frequency=300):
    modes = []
    n_max = int(max_frequency * 2 * length / 343) + 1  # approssimazione
    
    for nx in range(n_max):
        for ny in range(n_max):
            for nz in range(n_max):
                if nx == 0 and ny == 0 and nz == 0:
                    continue
                f = (343 / 2) * math.sqrt((nx / length) ** 2 + (ny / width) ** 2 + (nz / height) ** 2)
                if f > max_frequency:
                    continue
                if (nx == 0 and ny == 0) or (ny == 0 and nz == 0) or (nx == 0 and nz == 0):
                    mode_type = "Assiale"
                elif nx == 0 or ny == 0 or nz == 0:
                    mode_type = "Tangenziale"
                else:
                    mode_type = "Obliquo"
                modes.append({'frequency': round(f, 2), 'type': mode_type})
    modes.sort(key=lambda x: x['frequency'])
    return modes

def calculate_spl_coverage(speaker_x, speaker_y, room_length, room_width, sensitivity, power):
    x_points = [room_length * i / 19 for i in range(20)]
    y_points = [room_width * i / 14 for i in range(15)]
    spl_map = []
    for y in y_points:
        row = []
        for x in x_points:
            dx = x - speaker_x
            dy = y - speaker_y
            distance = math.sqrt(dx*dx + dy*dy)
            distance = max(distance, 0.5)
            spl = sensitivity + 10 * math.log10(power) - 20 * math.log10(distance)
            angle = math.degrees(math.atan2(dy, dx))
            directivity_factor = (math.cos(math.radians(angle)*2))**2
            spl *= directivity_factor
            row.append(spl)
        spl_map.append(row)
    return x_points, y_points, spl_map

def plot_rt60(frequencies, rt60_values):
    fig, ax = plt.subplots(figsize=(8,4))
    ax.plot(frequencies, rt60_values, marker='o', color='blue', linewidth=2)
    ax.set_xscale('log')
    ax.set_xlabel('Frequenza (Hz)')
    ax.set_ylabel('RT60 (secondi)')
    ax.set_title('RT60 per Banda di Frequenza')
    ax.grid(True, which="both", ls="--", linewidth=0.5)
    ax.axhspan(0.3, 0.5, color='green', alpha=0.2, label='Zona Ideale Mixing')
    ax.axhspan(0.2, 0.4, color='blue', alpha=0.2, label='Zona Ideale Registrazione')
    ax.legend()
    st.pyplot(fig)

def plot_room_modes(modes):
    fig, ax = plt.subplots(figsize=(8,4))
    freq = [m['frequency'] for m in modes]
    types = [m['type'] for m in modes]
    color_map = {'Assiale': 'red', 'Tangenziale': 'orange', 'Obliquo': 'green'}
    colors = [color_map.get(t, 'black') for t in types]
    y = [1 if t == 'Assiale' else 2 if t == 'Tangenziale' else 3 for t in types]
    ax.scatter(freq, y, c=colors)
    ax.set_yticks([1,2,3])
    ax.set_yticklabels(['Assiale', 'Tangenziale', 'Obliquo'])
    ax.set_xlabel('Frequenza (Hz)')
    ax.set_title('Modi della Stanza sotto 300 Hz')
    ax.grid(True)
    st.pyplot(fig)

def plot_spl_coverage(x_points, y_points, spl_map):
    fig, ax = plt.subplots(figsize=(8,5))
    im = ax.imshow(spl_map, extent=[min(x_points), max(x_points), min(y_points), max(y_points)], origin='lower', cmap='viridis', aspect='auto')
    ax.set_xlabel('Lunghezza (m)')
    ax.set_ylabel('Larghezza (m)')
    ax.set_title('Mappa di Copertura SPL')
    fig.colorbar(im, ax=ax, label='SPL (dB)')
    st.pyplot(fig)

def generate_pdf_report(volume, rt60_frequencies, rt60_values):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Report Calcolo Acustico", 0, 1, 'C')
    
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Volume stanza: {volume:.2f} m^3", 0, 1)
    
    pdf.cell(0, 10, "RT60 per bande di frequenza:", 0, 1)
    for f, val in zip(rt60_frequencies, rt60_values):
        pdf.cell(0, 10, f"  {f} Hz: {val:.2f} s", 0, 1)
    
    # Salva PDF in buffer
    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

def main():
    st.title("Calcolatore Acustico Pro Avanzato")
    
    conn = init_database()
    cursor = conn.cursor()
    
    # Sidebar input dimensioni stanza
    st.sidebar.header("Dimensioni Stanza (m)")
    length = st.sidebar.number_input("Lunghezza", min_value=1.0, max_value=100.0, value=10.0)
    width = st.sidebar.number_input("Larghezza", min_value=1.0, max_value=100.0, value=8.0)
    height = st.sidebar.number_input("Altezza", min_value=1.0, max_value=20.0, value=3.0)
    
    volume = length * width * height
    
    # Selezione casse dal db
    st.sidebar.header("Seleziona Cassa")
    cursor.execute("SELECT id, brand, model FROM speakers")
    speakers = cursor.fetchall()
    speaker_options = [f"{b} {m}" for _, b, m in speakers]
    selected_speaker = st.sidebar.selectbox("Cassa", speaker_options)
    selected_speaker_id = speakers[speaker_options.index(selected_speaker)][0]
    
    cursor.execute("SELECT * FROM speakers WHERE id = ?", (selected_speaker_id,))
    speaker_data = cursor.fetchone()
    
    # Posizione cassa
    st.sidebar.header("Posizione Cassa")
    speaker_x = st.sidebar.number_input("Posizione X (m)", min_value=0.0, max_value=length, value=length/2)
    speaker_y = st.sidebar.number_input("Posizione Y (m)", min_value=0.0, max_value=width, value=width/2)
    
    # Superfici e materiali
    st.sidebar.header("Materiali Superfici (aree in m²)")
    cursor.execute("SELECT * FROM materials")
    materials_db_rows = cursor.fetchall()
    
    surface_materials = {}
    for row in materials_db_rows:
        mat_name = row[1]
        default_area = 0.0
        surface_materials[mat_name] = st.sidebar.number_input(f"Area {mat_name}", min_value=0.0, max_value=length*width*10, value=default_area)
    
    # Calcoli RT60
    frequencies, rt60_values = calculate_rt60_per_band(volume, surface_materials, materials_db_rows)
    
    st.header("Risultati RT60")
    plot_rt60(frequencies, rt60_values)
    
    # Modi stanza
    modes = calculate_room_modes(length, width, height)
    st.header("Modi della Stanza (fino a 300 Hz)")
    plot_room_modes(modes)
    
    # Mappa SPL
    sensitivity = speaker_data[5]
    max_power = speaker_data[6]
    x_points, y_points, spl_map = calculate_spl_coverage(speaker_x, speaker_y, length, width, sensitivity, max_power)
    st.header("Copertura SPL nella stanza")
    plot_spl_coverage(x_points, y_points, spl_map)
    
    # Genera PDF
    if st.button("Genera Report PDF"):
        pdf_buffer = generate_pdf_report(volume, frequencies, rt60_values)
        st.download_button(label="Scarica Report PDF", data=pdf_buffer, file_name="report_acustico.pdf", mime="application/pdf")
    
if __name__ == "__main__":
    main()
