# app.py - Calcolatore Acustico Pro Avanzato

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import sqlite3
import json
import math
from fpdf import FPDF
import io
from datetime import datetime

# Configurazione pagina
st.set_page_config(
    page_title="Calcolatore Acustico Pro Avanzato",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== DATABASE SETUP =====
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
    
    # Dati casse popolari
    speakers_data = [
        ('JBL', 'EON615', 'Attiva', 8, 90, 1000, 39, 20000, 'A Tromba', 'Media'),
        ('Yamaha', 'DXR12', 'Attiva', 8, 96, 1100, 42, 20000, 'A Tromba', 'Media'),
        ('QSC', 'K12.2', 'Attiva', 8, 98, 2000, 45, 20000, 'A Tromba', 'Alta'),
        ('Mackie', 'Thump15A', 'Attiva', 8, 95, 1400, 40, 20000, 'A Tromba', 'Bassa'),
        ('RCF', 'ART 732-A', 'Attiva', 8, 99, 1400, 45, 20000, 'A Tromba', 'Alta'),
        ('Behringer', 'B212XL', 'Passiva', 8, 95, 800, 50, 20000, 'A Tromba', 'Bassa'),
        ('Electro-Voice', 'ELX200-12P', 'Attiva', 8, 94, 1200, 43, 20000, 'A Tromba', 'Media'),
        ('dBTechnologies', 'B-Hype 12', 'Attiva', 8, 96, 600, 55, 20000, 'A Tromba', 'Media'),
        ('Turbosound', 'iQ12', 'Attiva', 8, 95, 2500, 58, 18000, 'A Tromba', 'Alta'),
        ('L-Acoustics', 'X8', 'Passiva', 8, 91, 250, 90, 20000, 'A Tromba', 'Molto Alta'),
    ]
    
    cursor.executemany('''
        INSERT INTO speakers (brand, model, type, impedance, sensitivity, max_power,
                             freq_response_low, freq_response_high, directivity, price_range)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', speakers_data)
    
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
        ('Cemento nudo', 0.01, 0.01, 0.02, 0.02, 0.02, 0.02),
        ('Muro intonacato', 0.02, 0.02, 0.03, 0.04, 0.04, 0.03),
        ('Pannelli fonoassorbenti', 0.15, 0.40, 0.85, 0.95, 0.90, 0.85),
        ('Tappeto pesante', 0.10, 0.15, 0.25, 0.35, 0.45, 0.50),
        ('Tende pesanti', 0.05, 0.12, 0.35, 0.48, 0.38, 0.36),
        ('Vetro', 0.03, 0.03, 0.03, 0.03, 0.02, 0.02),
        ('Legno', 0.10, 0.11, 0.10, 0.08, 0.08, 0.11),
        ('Pubblico (persone)', 0.25, 0.40, 0.50, 0.58, 0.67, 0.75),
        ('Sedie imbottite', 0.19, 0.37, 0.56, 0.67, 0.61, 0.59),
        ('Bass trap (angolo)', 0.28, 0.78, 0.97, 0.93, 0.87, 0.83),
    ]
    
    cursor.executemany('''
        INSERT INTO materials (name, absorption_125, absorption_250, absorption_500,
                              absorption_1000, absorption_2000, absorption_4000)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', materials_data)
    
    conn.commit()
    return conn

# ===== FUNZIONI CALCOLO AVANZATE =====
def calculate_rt60_per_band(volume, surface_materials):
    """Calcola RT60 per banda di frequenza usando materiali reali"""
    frequencies = [125, 250, 500, 1000, 2000, 4000]
    rt60_values = []
    
    for i, freq in enumerate(frequencies):
        total_absorption = 0
        for material, area in surface_materials.items():
            # Qui useresti i coefficienti dal database
            absorption_coeff = 0.25  # Semplificato per ora
            total_absorption += area * absorption_coeff
        
        if total_absorption > 0:
            rt60 = 0.161 * volume / total_absorption
            rt60_values.append(max(0.1, min(5.0, rt60)))
        else:
            rt60_values.append(1.0)
    
    return frequencies, rt60_values

def calculate_room_modes(length, width, height, max_freq=300):
    """Calcola tutti i modi della stanza fino a max_freq"""
    modes = []
    for nx in range(0, 10):
        for ny in range(0, 10):
            for nz in range(0, 10):
                if nx + ny + nz == 0:
                    continue
                freq = 340/2 * math.sqrt((nx/length)**2 + (ny/width)**2 + (nz/height)**2)
                if freq <= max_freq:
                    mode_type = "Assiale" if [nx, ny, nz].count(0) == 2 else "Tangenziale" if [nx, ny, nz].count(0) == 1 else "Obliquo"
                    modes.append({
                        'frequency': freq,
                        'nx': nx, 'ny': ny, 'nz': nz,
                        'type': mode_type
                    })
    return sorted(modes, key=lambda x: x['frequency'])

def calculate_spl_coverage(speaker_x, speaker_y, room_length, room_width,
                          sensitivity, power, directivity_angle=90):
    """Calcola la copertura SPL nella stanza"""
    x_points = np.linspace(0, room_length, 20)
    y_points = np.linspace(0, room_width, 15)
    X, Y = np.meshgrid(x_points, y_points)
    
    # Calcolo semplificato della copertura SPL
    distances = np.sqrt((X - speaker_x)**2 + (Y - speaker_y)**2)
    distances = np.maximum(distances, 0.5)  # Minimo 0.5m
    
    # SPL = Sensibilità + 10*log10(Power) - 20*log10(distance)
    spl_map = sensitivity + 10 * np.log10(power) - 20 * np.log10(distances)
    
    # Applicazione pattern direttivo semplificato
    angles = np.arctan2(Y - speaker_y, X - speaker_x) * 180 / np.pi
    directivity_factor = np.cos(np.radians(angles) * 2) ** 2
    spl_map *= directivity_factor
    
    return X, Y, spl_map

# ===== INTERFACCIA PRINCIPALE =====
def main():
    # Inizializza database PRIMA di tutto
    conn = init_database()
    
    # Sidebar per navigazione
    st.sidebar.title("🔊 Calcolatore Acustico Pro")
    page = st.sidebar.radio("Sezioni", [
        "🏠 Configurazione Base",
        "📊 Analisi Avanzata",
        "🔊️ Sistema Audio",
        "📈 Visualizzazioni",
        "💾 Progetti Salvati",
        "📋 Report Completo"
    ])
    
    # Inizializza session state
    if 'current_project' not in st.session_state:
        st.session_state.current_project = {
            'name': f'Progetto_{datetime.now().strftime("%Y%m%d_%H%M")}',
            'room_dimensions': {'length': 10.0, 'width': 8.0, 'height': 3.0},
            'speakers': [],
            'materials': {}
        }
    
    # ===== CONFIGURAZIONE BASE =====
    if page == "🏠 Configurazione Base":
        st.title("🏠 Configurazione Base dell'Ambiente")
        
        # Nome progetto
        project_name = st.text_input("Nome Progetto", 
                                   value=st.session_state.current_project['name'])
        st.session_state.current_project['name'] = project_name
        
        # Dimensioni ambiente
        st.subheader("Dimensioni Ambiente")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            length = st.number_input("Lunghezza (m)", min_value=1.0, max_value=100.0,
                                   value=st.session_state.current_project['room_dimensions']['length'], step=0.1)
        with col2:
            width = st.number_input("Larghezza (m)", min_value=1.0, max_value=100.0,
                                  value=st.session_state.current_project['room_dimensions']['width'], step=0.1)
        with col3:
            height = st.number_input("Altezza (m)", min_value=2.0, max_value=20.0,
                                   value=st.session_state.current_project['room_dimensions']['height'], step=0.1)
        
        # Aggiorna session state
        st.session_state.current_project['room_dimensions'].update({
            'length': length, 'width': width, 'height': height
        })
        
        # Calcoli base
        volume = length * width * height
        surface = 2 * (length * width + length * height + width * height)
        
        # Metriche base
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Volume", f"{volume:.1f} m³")
        with col2:
            st.metric("Superficie", f"{surface:.1f} m²")
        with col3:
            st.metric("Rapporto L/W", f"{length/width:.2f}")
        with col4:
            golden_ratio = abs(length/width - 1.618)
            quality = "Ottima" if golden_ratio < 0.1 else "Buona" if golden_ratio < 0.3 else "Migliorabile"
            st.metric("Proporzioni", quality)
        
        # Tipo ambiente e uso
        st.subheader("Caratteristiche d'Uso")
        col1, col2 = st.columns(2)
        
        with col1:
            room_type = st.selectbox("Tipo di ambiente", [
                "Home Studio", "Studio Professionale", "Sala Prove",
                "Auditorium", "Teatro", "Chiesa", "Sala Conferenze", "Podcast Studio"
            ])
        
        with col2:
            use_type = st.selectbox("Uso principale", [
                "Registrazione Voce", "Registrazione Strumenti", "Mixing",
                "Mastering", "Live Performance", "Rehearsal", "Podcast", "Conferenze"
            ])
        
        # Materiali ambiente
        st.subheader("Materiali Ambiente")
        
        # Ottieni materiali dal database
        materials_df = pd.read_sql_query("SELECT * FROM materials", conn)
        material_names = materials_df['name'].tolist()
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Pareti**")
            wall_material = st.selectbox("Materiale pareti", material_names)
            wall_coverage = st.slider("Copertura pareti (%)", 0, 100, 80)
            
            st.write("**Soffitto**")
            ceiling_material = st.selectbox("Materiale soffitto", material_names)
            ceiling_coverage = st.slider("Copertura soffitto (%)", 0, 100, 100)
        
        with col2:
            st.write("**Pavimento**")
            floor_material = st.selectbox("Materiale pavimento", material_names)
            floor_coverage = st.slider("Copertura pavimento (%)", 0, 100, 100)
            
            st.write("**Trattamento aggiuntivo**")
            treatment_material = st.selectbox("Trattamento acustico", material_names)
            treatment_coverage = st.slider("Copertura trattamento (%)", 0, 100, 20)
        
        # Salva materiali in session state
        st.session_state.current_project['materials'] = {
            'walls': (wall_material, wall_coverage),
            'ceiling': (ceiling_material, ceiling_coverage),
            'floor': (floor_material, floor_coverage),
            'treatment': (treatment_material, treatment_coverage)
        }
    
    # ===== ANALISI AVANZATA =====
    elif page == "📊 Analisi Avanzata":
        st.title("📊 Analisi Acustica Avanzata")
        
        # Recupera dati dal session state
        dims = st.session_state.current_project['room_dimensions']
        length, width, height = dims['length'], dims['width'], dims['height']
        volume = length * width * height
        
        # RT60 per banda
        st.subheader("RT60 per Banda di Frequenza")
        
        # Calcolo RT60 avanzato
        surface_materials = {
            'walls': 2 * (length * height + width * height) * 0.8,
            'ceiling': length * width,
            'floor': length * width * 0.8,
            'treatment': (2 * (length * height + width * height)) * 0.2
        }
        
        frequencies, rt60_values = calculate_rt60_per_band(volume, surface_materials)
        
        # Grafico RT60
        fig_rt60 = go.Figure()
        fig_rt60.add_trace(go.Scatter(
            x=frequencies,
            y=rt60_values,
            mode='lines+markers',
            name='RT60',
            line=dict(color='blue', width=3)
        ))
        
        # Zone ideali per diversi usi
        fig_rt60.add_hrect(y0=0.3, y1=0.5, fillcolor="green", opacity=0.2,
                          annotation_text="Zona Ideale Mixing")
        fig_rt60.add_hrect(y0=0.2, y1=0.4, fillcolor="blue", opacity=0.2,
                          annotation_text="Zona Ideale Registrazione")
        
        fig_rt60.update_layout(
            title="RT60 per Banda di Frequenza",
            xaxis_title="Frequenza (Hz)",
            yaxis_title="RT60 (secondi)",
            xaxis_type="log",
            height=400
        )
        
        st.plotly_chart(fig_rt60, use_container_width=True)
        
        # Analisi modi della stanza
        st.subheader("Analisi Modi della Stanza")
        
        modes = calculate_room_modes(length, width, height)
        modes_df = pd.DataFrame(modes)
        
        # Grafico modi
        fig_modes = px.scatter(modes_df, x='frequency', y='type',
                              color='type', size_max=15,
                              title="Modi della Stanza sotto 300 Hz")
        fig_modes.update_layout(height=400)
        st.plotly_chart(fig_modes, use_container_width=True)
        
        # Tabella modi problematici
        problematic_modes = modes_df[modes_df['frequency'] < 200]
        if not problematic_modes.empty:
            st.warning(f"⚠️ Trovati {len(problematic_modes)} modi problematici sotto 200 Hz")
            st.dataframe(problematic_modes[['frequency', 'type', 'nx', 'ny', 'nz']].round(1))
        
        # Raccomandazioni intelligenti
        st.subheader("💡 Raccomandazioni Intelligenti")
        
        avg_rt60 = np.mean(rt60_values)
        recommendations = []
        
        if avg_rt60 > 1.5:
            recommendations.append("🔇 Ambiente troppo riverberante - Aggiungere materiali fonoassorbenti")
        elif avg_rt60 < 0.3:
            recommendations.append("🔊 Ambiente troppo secco - Aggiungere superfici riflettenti")
        
        if len(problematic_modes) > 5:
            recommendations.append("🎯 Troppi modi problematici - Installare bass trap negli angoli")
        
        if abs(length/width - 1.618) > 0.5:
            recommendations.append("📐 Proporzioni non ottimali - Considerare trattamento asimmetrico")
        
        for rec in recommendations:
            st.write(f"• {rec}")
    
    # ===== SISTEMA AUDIO =====
    elif page == "🔊️ Sistema Audio":
        st.title("🔊️ Configurazione Sistema Audio")
        
        # Database casse
        speakers_df = pd.read_sql_query("SELECT * FROM speakers", conn)
        
        # Selezione casse
        st.subheader("Selezione Casse")
        
        col1, col2 = st.columns(2)
        with col1:
            selected_speaker = st.selectbox("Modello Cassa",
                                          speakers_df['brand'] + ' ' + speakers_df['model'])
            
            # Ottieni dati cassa selezionata
            speaker_data = speakers_df[speakers_df['brand'] + ' ' + speakers_df['model'] == selected_speaker].iloc[0]
            
            st.write(f"**Tipo**: {speaker_data['type']}")
            st.write(f"**Impedenza**: {speaker_data['impedance']} Ω")
            st.write(f"**Sensibilità**: {speaker_data['sensitivity']} dB")
            st.write(f"**Potenza Max**: {speaker_data['max_power']} W")
            st.write(f"**Risposta**: {speaker_data['freq_response_low']}-{speaker_data['freq_response_high']} Hz")
        
        with col2:
            num_speakers = st.number_input("Numero di Casse", min_value=1, max_value=8, value=2)
            listening_distance = st.number_input("Distanza d'ascolto (m)", min_value=1.0, max_value=20.0, value=4.0)
            target_spl = st.number_input("SPL Target (dB)", min_value=80, max_value=130, value=95)
        
        # Calcoli sistema
        st.subheader("Calcoli Sistema")
        
        dims = st.session_state.current_project['room_dimensions']
        length, width, height = dims['length'], dims['width'], dims['height']
        volume = length * width * height
        
        # Calcolo potenza richiesta
        distance_loss = 20 * math.log10(listening_distance)
        required_sensitivity = target_spl + distance_loss
        power_needed = 10 ** ((required_sensitivity - speaker_data['sensitivity']) / 10)
        
        # Fattore ambiente
        rt60_estimate = 0.161 * volume / (0.25 * 2 * (length * width + length * height + width * height))
        room_factor = 1.5 if rt60_estimate > 1.0 else 1.0
        power_needed *= room_factor
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Potenza Richiesta", f"{power_needed:.0f} W")
        with col2:
            headroom = speaker_data['max_power'] / power_needed if power_needed > 0 else float('inf')
            st.metric("Headroom", f"{headroom:.1f}x")
        with col3:
            adequacy = "Ottima" if headroom > 3 else "Buona" if headroom > 1.5 else "Insufficiente"
            st.metric("Adeguatezza", adequacy)
        
        # Posizionamento ottimale
        st.subheader("Posizionamento Ottimale")
        
        # Suggerimenti basati sulle dimensioni
        if num_speakers == 2:
            speaker_distance = width * 0.6
            st.write(f"**Configurazione Stereo:**")
            st.write(f"• Distanza tra casse: {speaker_distance:.1f} m")
            st.write(f"• Distanza dalla parete posteriore: {length * 0.3:.1f} m")
            st.write(f"• Altezza: {height * 0.6:.1f} m")
            st.write(f"• Angolo toe-in: 15-30°")
        
        # Configurazione sistema
        st.subheader("Configurazione Sistema")
        
        config_type = st.selectbox("Tipo Configurazione", [
            "Stereo", "Mono", "2.1 (con sub)", "Quadrifonico", "Sistema Distribuito"
        ])
        
        if config_type == "2.1 (con sub)":
            st.write("**Subwoofer consigliato:**")
            st.write("• Frequenza di crossover: 80-120 Hz")
            st.write("• Posizionamento: Angolo della stanza")
            st.write("• Potenza: 150-300% della potenza main")
    
    # ===== VISUALIZZAZIONI =====
    elif page == "📈 Visualizzazioni":
        st.title("📈 Visualizzazioni Avanzate")
        
        dims = st.session_state.current_project['room_dimensions']
        length, width, height = dims['length'], dims['width'], dims['height']
        
        # Selettore visualizzazione
        viz_type = st.selectbox("Tipo Visualizzazione", [
            "Mappa Copertura SPL", "Risposta in Frequenza 3D",
            "Simulazione Riflessioni", "Analisi Posizionamento"
        ])
        
        if viz_type == "Mappa Copertura SPL":
            st.subheader("Mappa di Copertura SPL")
            
            # Parametri cassa
            col1, col2 = st.columns(2)
            with col1:
                speaker_x = st.slider("Posizione X cassa (m)", 0.0, length, length/4)
                speaker_y = st.slider("Posizione Y cassa (m)", 0.0, width, width/2)
            with col2:
                power = st.slider("Potenza (W)", 50, 2000, 500)
                sensitivity = st.slider("Sensibilità (dB)", 85, 105, 95)
            
            # Calcola copertura
            X, Y, spl_map = calculate_spl_coverage(speaker_x, speaker_y, length, width, sensitivity, power)
            
            # Grafico heatmap
            fig_spl = go.Figure(data=go.Heatmap(
                z=spl_map,
                x=X[0],
                y=Y[:,0],
                colorscale='Viridis',
                colorbar=dict(title="SPL (dB)")
            ))
            
            # Aggiungi posizione cassa
            fig_spl.add_trace(go.Scatter(
                x=[speaker_x], y=[speaker_y],
                mode='markers',
                marker=dict(size=15, color='red', symbol='diamond'),
                name='Cassa'
            ))
            
            fig_spl.update_layout(
                title="Mappa di Copertura SPL",
                xaxis_title="Lunghezza (m)",
                yaxis_title="Larghezza (m)",
                height=500
            )
            
            st.plotly_chart(fig_spl, use_container_width=True)
        
        elif viz_type == "Risposta in Frequenza 3D":
            st.subheader("Risposta in Frequenza 3D della Stanza")
            
            # Simulazione risposta in frequenza
            frequencies = np.logspace(1.5, 4, 100)  # 30 Hz - 10 kHz
            
            # Calcolo modi e risposta
            modes = calculate_room_modes(length, width, height, max_freq=1000)
            
            # Simulazione risposta (semplificata)
            response = np.ones_like(frequencies)
            for mode in modes:
                if mode['frequency'] < 1000:
                    # Aggiunge risonanza al modo
                    resonance = 1 / (1 + ((frequencies - mode['frequency']) / 10)**2)
                    response += resonance * 0.1
            
            # Grafico 3D
            fig_3d = go.Figure(data=go.Surface(
                x=frequencies,
                y=np.linspace(0, length, 20),
                z=np.outer(response, np.ones(20)),
                colorscale='Viridis'
            ))
            
            fig_3d.update_layout(
                title="Risposta in Frequenza 3D",
                scene=dict(
                    xaxis_title="Frequenza (Hz)",
                    yaxis_title="Posizione (m)",
                    zaxis_title="Risposta (dB)"
                ),
                height=600
            )
            
            st.plotly_chart(fig_3d, use_container_width=True)
        
        elif viz_type == "Simulazione Riflessioni":
            st.subheader("Simulazione Prime Riflessioni")
            
            # Parametri sorgente e ascoltatore
            col1, col2 = st.columns(2)
            with col1:
                source_x = st.slider("Sorgente X (m)", 0.0, length, length*0.3)
                source_y = st.slider("Sorgente Y (m)", 0.0, width, width*0.5)
            with col2:
                listener_x = st.slider("Ascoltatore X (m)", 0.0, length, length*0.7)
                listener_y = st.slider("Ascoltatore Y (m)", 0.0, width, width*0.5)
            
            # Visualizzazione 2D della stanza
            fig_room = go.Figure()
            
            # Contorno stanza
            fig_room.add_trace(go.Scatter(
                x=[0, length, length, 0, 0],
                y=[0, 0, width, width, 0],
                mode='lines',
                line=dict(color='black', width=2),
                name='Stanza'
            ))
            
            # Sorgente e ascoltatore
            fig_room.add_trace(go.Scatter(
                x=[source_x], y=[source_y],
                mode='markers',
                marker=dict(size=12, color='red'),
                name='Sorgente'
            ))
            
            fig_room.add_trace(go.Scatter(
                x=[listener_x], y=[listener_y],
                mode='markers',
                marker=dict(size=12, color='blue'),
                name='Ascoltatore'
            ))
            
            # Linea diretta
            fig_room.add_trace(go.Scatter(
                x=[source_x, listener_x],
                y=[source_y, listener_y],
                mode='lines',
                line=dict(color='green', width=2),
                name='Suono Diretto'
            ))
            
            # Prime riflessioni (semplificato)
            # Riflessione parete sinistra
            mirror_x = -source_x
            fig_room.add_trace(go.Scatter(
                x=[mirror_x, listener_x],
                y=[source_y, listener_y],
                mode='lines',
                line=dict(color='orange', width=1, dash='dash'),
                name='Riflessione Parete'
            ))
            
            fig_room.update_layout(
                title="Simulazione Prime Riflessioni",
                xaxis_title="Lunghezza (m)",
                yaxis_title="Larghezza (m)",
                height=500,
                showlegend=True
            )

st.plotly_chart(fig_room, use_container_width=True)
    
    # Calcolo tempi di arrivo
    st.subheader("Tempi di Arrivo")
    
    direct_distance = math.sqrt((listener_x - source_x)**2 + (listener_y - source_y)**2)
    direct_time = direct_distance / 343  # velocità del suono
    
    # Riflessioni principali
    reflections = []
    
    # Parete sinistra
    refl_dist = math.sqrt((0 - source_x)**2 + (source_y - source_y)**2) + \
               math.sqrt((listener_x - 0)**2 + (listener_y - source_y)**2)
    reflections.append(("Parete Sinistra", refl_dist / 343))
    
    # Parete destra
    refl_dist = math.sqrt((length - source_x)**2 + (source_y - source_y)**2) + \
               math.sqrt((listener_x - length)**2 + (listener_y - source_y)**2)
    reflections.append(("Parete Destra", refl_dist / 343))
    
    # Parete posteriore
    refl_dist = math.sqrt((source_x - source_x)**2 + (0 - source_y)**2) + \
               math.sqrt((listener_x - source_x)**2 + (listener_y - 0)**2)
    reflections.append(("Parete Posteriore", refl_dist / 343))
    
    # Parete anteriore
    refl_dist = math.sqrt((source_x - source_x)**2 + (width - source_y)**2) + \
               math.sqrt((listener_x - source_x)**2 + (listener_y - width)**2)
    reflections.append(("Parete Anteriore", refl_dist / 343))
    
    # Tabella tempi
    reflection_data = []
    reflection_data.append(("Suono Diretto", direct_time * 1000, 0))
    
    for name, time in reflections:
        delay = (time - direct_time) * 1000
        reflection_data.append((name, time * 1000, delay))
    
    refl_df = pd.DataFrame(reflection_data, columns=["Tipo", "Tempo (ms)", "Ritardo (ms)"])
    st.dataframe(refl_df.round(2))

    elif viz_type == "Analisi Posizionamento":
        st.subheader("Analisi Posizionamento Ottimale")
        
        # Griglia di posizioni
        positions_x = np.linspace(0.5, length-0.5, 10)
        positions_y = np.linspace(0.5, width-0.5, 8)
        
        # Calcolo score per ogni posizione
        scores = []
        for px in positions_x:
            row_scores = []
            for py in positions_y:
                # Score basato su distanza dalle pareti e simmetria
                wall_distance = min(px, length-px, py, width-py)
                center_distance = math.sqrt((px - length/2)**2 + (py - width/2)**2)
                
                # Score combinato (più alto è meglio)
                score = wall_distance * 0.7 + (max(length, width) - center_distance) * 0.3
                row_scores.append(score)
            scores.append(row_scores)
        
        # Heatmap posizionamento
        fig_pos = go.Figure(data=go.Heatmap(
            z=scores,
            x=positions_y,
            y=positions_x,
            colorscale='RdYlGn',
            colorbar=dict(title="Score Posizionamento")
        ))
        
        fig_pos.update_layout(
            title="Analisi Posizionamento Ottimale",
            xaxis_title="Larghezza (m)",
            yaxis_title="Lunghezza (m)",
            height=500
        )
        
        st.plotly_chart(fig_pos, use_container_width=True)
        
        # Migliori posizioni
        best_positions = []
        scores_array = np.array(scores)
        max_indices = np.unravel_index(np.argsort(scores_array.ravel())[-3:], scores_array.shape)
        
        for i in range(3):
            x_idx, y_idx = max_indices[0][-(i+1)], max_indices[1][-(i+1)]
            best_positions.append({
                'Posizione': f"#{i+1}",
                'X (m)': positions_x[x_idx],
                'Y (m)': positions_y[y_idx],
                'Score': scores_array[x_idx, y_idx]
            })
        
        st.write("**Top 3 Posizioni Consigliate:**")
        st.dataframe(pd.DataFrame(best_positions).round(2))

# ===== PROGETTI SALVATI =====
elif page == "💾 Progetti Salvati":
    st.title("💾 Gestione Progetti")
    
    # Simulazione sistema salvataggio (in produzione useresti un database)
    if 'saved_projects' not in st.session_state:
        st.session_state.saved_projects = []
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Progetto Corrente")
        current = st.session_state.current_project
        st.write(f"**Nome**: {current['name']}")
        st.write(f"**Dimensioni**: {current['room_dimensions']['length']} x {current['room_dimensions']['width']} x {current['room_dimensions']['height']} m")
        st.write(f"**Volume**: {current['room_dimensions']['length'] * current['room_dimensions']['width'] * current['room_dimensions']['height']:.1f} m³")
    
    with col2:
        if st.button("💾 Salva Progetto"):
            # Crea copia del progetto corrente
            project_copy = {
                'name': current['name'],
                'saved_date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'room_dimensions': current['room_dimensions'].copy(),
                'materials': current['materials'].copy(),
                'speakers': current['speakers'].copy() if 'speakers' in current else []
            }
            st.session_state.saved_projects.append(project_copy)
            st.success("Progetto salvato!")
    
    # Lista progetti salvati
    if st.session_state.saved_projects:
        st.subheader("Progetti Salvati")
        
        for i, project in enumerate(st.session_state.saved_projects):
            with st.expander(f"{project['name']} - {project['saved_date']}"):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**Dimensioni**: {project['room_dimensions']['length']} x {project['room_dimensions']['width']} x {project['room_dimensions']['height']} m")
                    volume = project['room_dimensions']['length'] * project['room_dimensions']['width'] * project['room_dimensions']['height']
                    st.write(f"**Volume**: {volume:.1f} m³")
                
                with col2:
                    if st.button(f"🔄 Carica", key=f"load_{i}"):
                        st.session_state.current_project = project.copy()
                        st.success("Progetto caricato!")
                        st.rerun()
                
                with col3:
                    if st.button(f"🗑️ Elimina", key=f"delete_{i}"):
                        st.session_state.saved_projects.pop(i)
                        st.success("Progetto eliminato!")
                        st.rerun()
    
    # Import/Export
    st.subheader("Import/Export")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Export Progetto**")
        if st.button("📤 Esporta JSON"):
            project_json = json.dumps(st.session_state.current_project, indent=2)
            st.download_button(
                label="⬇️ Scarica JSON",
                data=project_json,
                file_name=f"{st.session_state.current_project['name']}.json",
                mime="application/json"
            )
    
    with col2:
        st.write("**Import Progetto**")
        uploaded_file = st.file_uploader("Carica JSON", type=['json'])
        if uploaded_file is not None:
            try:
                project_data = json.load(uploaded_file)
                st.session_state.current_project = project_data
                st.success("Progetto importato!")
                st.rerun()
            except:
                st.error("Errore nel caricamento del file")

# ===== REPORT COMPLETO =====
elif page == "📊 Report Completo":
    st.title("📊 Report Completo del Progetto")
    
    current = st.session_state.current_project
    dims = current['room_dimensions']
    length, width, height = dims['length'], dims['width'], dims['height']
    volume = length * width * height
    
    # Sezione 1: Informazioni Generali
    st.header("1. Informazioni Generali")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Progetto")
        st.write(f"**Nome**: {current['name']}")
        st.write(f"**Data**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        st.write(f"**Dimensioni**: {length} x {width} x {height} m")
        st.write(f"**Volume**: {volume:.1f} m³")
        st.write(f"**Superficie**: {2 * (length * width + length * height + width * height):.1f} m²")
    
    with col2:
        st.subheader("Proporzioni")
        ratio_lw = length / width
        ratio_lh = length / height
        ratio_wh = width / height
        
        st.write(f"**L/W**: {ratio_lw:.2f}")
        st.write(f"**L/H**: {ratio_lh:.2f}")
        st.write(f"**W/H**: {ratio_wh:.2f}")
        
        # Valutazione proporzioni
        golden_ratio = abs(ratio_lw - 1.618)
        if golden_ratio < 0.1:
            st.success("✅ Proporzioni ottime (vicine al rapporto aureo)")
        elif golden_ratio < 0.3:
            st.warning("⚠️ Proporzioni buone")
        else:
            st.error("❌ Proporzioni da migliorare")
    
    # Sezione 2: Analisi Acustica
    st.header("2. Analisi Acustica")
    
    # RT60 stimato
    surface_materials = {
        'walls': 2 * (length * height + width * height) * 0.8,
        'ceiling': length * width,
        'floor': length * width * 0.8,
        'treatment': (2 * (length * height + width * height)) * 0.2
    }
    
    frequencies, rt60_values = calculate_rt60_per_band(volume, surface_materials)
    avg_rt60 = np.mean(rt60_values)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("RT60")
        st.write(f"**RT60 Medio**: {avg_rt60:.2f} s")
        
        if avg_rt60 < 0.3:
            st.warning("⚠️ Ambiente molto secco")
        elif avg_rt60 < 0.8:
            st.success("✅ RT60 ottimale per studio")
        elif avg_rt60 < 1.5:
            st.info("ℹ️ Buono per ambienti più grandi")
        else:
            st.error("❌ Troppo riverberante")
    
    with col2:
        st.subheader("Modi della Stanza")
        modes = calculate_room_modes(length, width, height)
        problematic_modes = [m for m in modes if m['frequency'] < 200]
        
        st.write(f"**Modi totali < 300 Hz**: {len(modes)}")
        st.write(f"**Modi problematici < 200 Hz**: {len(problematic_modes)}")
        
        if len(problematic_modes) > 8:
            st.error("❌ Troppi modi problematici")
        elif len(problematic_modes) > 4:
            st.warning("⚠️ Alcuni modi problematici")
        else:
            st.success("✅ Distribuzione modi accettabile")
    
    # Sezione 3: Raccomandazioni
    st.header("3. Raccomandazioni")
    
    recommendations = []
    
    # Raccomandazioni RT60
    if avg_rt60 > 1.5:
        recommendations.append({
            'tipo': 'Critico',
            'area': 'Trattamento Acustico',
            'descrizione': 'Installare pannelli fonoassorbenti per ridurre RT60',
            'priorita': 'Alta'
        })
    elif avg_rt60 < 0.3:
        recommendations.append({
            'tipo': 'Attenzione',
            'area': 'Trattamento Acustico',
            'descrizione': 'Aggiungere superfici riflettenti per aumentare RT60',
            'priorita': 'Media'
        })
    
    # Raccomandazioni modi
    if len(problematic_modes) > 6:
        recommendations.append({
            'tipo': 'Critico',
            'area': 'Bass Trap',
            'descrizione': 'Installare bass trap negli angoli per controllo modi',
            'priorita': 'Alta'
        })
    
    # Raccomandazioni proporzioni
    if golden_ratio > 0.5:
        recommendations.append({
            'tipo': 'Suggerimento',
            'area': 'Layout',
            'descrizione': 'Considerare riorganizzazione spazio per migliorare proporzioni',
            'priorita': 'Bassa'
        })
    
    # Tabella raccomandazioni
    if recommendations:
        rec_df = pd.DataFrame(recommendations)
        st.dataframe(rec_df, use_container_width=True)
    else:
        st.success("✅ Nessuna raccomandazione critica - ambiente ben configurato!")
    
    # Sezione 4: Export Report
    st.header("4. Export Report")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Genera Report PDF"):
            # Qui implementeresti la generazione PDF
            st.info("Funzione PDF in sviluppo - utilizza il report dettagliato qui sopra")
    
    with col2:
        if st.button("📊 Esporta Dati Excel"):
            # Qui implementeresti l'export Excel
            st.info("Funzione Excel in sviluppo - utilizza l'export JSON per i dati")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("🎵 **Calcolatore Acustico Pro**")
st.sidebar.markdown("Versione 2.0 - Avanzato")
st.sidebar.markdown("© 2024 - Strumento per professionisti audio")

# Info tecniche
with st.sidebar.expander("ℹ️ Info Tecniche"):
    st.write("""
    **Formule utilizzate:**
    - RT60: Sabine (0.161 × V / A)
    - Modi: f = c/2 × √((nx/L)² + (ny/W)² + (nz/H)²)
    - SPL: dB = Sens + 10log(P) - 20log(d)
    
    **Limitazioni:**
    - Calcoli semplificati per demo
    - Non considera diffusione
    - Assorbimento costante per materiale
    """)

# Chiamata funzione principale
if __name__ == "__main__":
    main()
