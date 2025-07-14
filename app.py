import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3

# --- Funzioni di calcolo ---

def calculate_rt60_per_band(volume, surface_materials, materials_df):
    """
    Calcola il tempo di riverberazione RT60 per frequenza,
    usando il volume e l'area dei materiali con assorbimenti specifici.
    """
    freq = materials_df['Frequency'].values
    total_absorption = np.zeros_like(freq, dtype=float)

    for material, area in surface_materials.items():
        if material not in materials_df.columns:
            continue  # evita errori se manca materiale nel DB
        absorption_coeff = materials_df[material].values
        total_absorption += absorption_coeff * area

    # Formula di Sabine
    with np.errstate(divide='ignore', invalid='ignore'):
        rt60 = 0.161 * volume / total_absorption
        rt60 = np.where(total_absorption == 0, np.nan, rt60)

    return freq, rt60

def calculate_room_modes(length, width, height, max_mode=10):
    """
    Calcola le frequenze modali principali della stanza.
    """
    modes = []
    c = 343  # velocità del suono in m/s

    for nx in range(max_mode + 1):
        for ny in range(max_mode + 1):
            for nz in range(max_mode + 1):
                if nx == ny == nz == 0:
                    continue
                f = (c / 2) * np.sqrt((nx / length) ** 2 + (ny / width) ** 2 + (nz / height) ** 2)
                modes.append((nx, ny, nz, f))
    modes.sort(key=lambda x: x[3])
    return modes[:100]

def calculate_spl_coverage(room_dims, speaker_pos, speaker_power, grid_res=0.5):
    """
    Calcola la mappa SPL in 2D sulla base della posizione dell'altoparlante
    e del suo pattern direttivo semplificato.
    """
    length, width, height = room_dims['length'], room_dims['width'], room_dims['height']
    x = np.arange(0, length + grid_res, grid_res)
    y = np.arange(0, width + grid_res, grid_res)
    X, Y = np.meshgrid(x, y)

    speaker_x, speaker_y = speaker_pos

    # Calcolo distanza
    distances = np.sqrt((X - speaker_x) ** 2 + (Y - speaker_y) ** 2)
    distances = np.where(distances < 0.1, 0.1, distances)  # evita divisioni per zero

    # Angoli per pattern direttivo
    angles = np.arctan2(Y - speaker_y, X - speaker_x)  # radianti
    directivity_factor = np.cos(2 * angles) ** 2  # pattern di direttività semplificato

    spl = speaker_power * directivity_factor / (distances ** 2)
    spl_db = 20 * np.log10(spl)
    return X, Y, spl_db

# --- Setup DB e dati materiali ---

@st.cache_resource
def init_database():
    conn = sqlite3.connect(':memory:')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        room_length REAL,
        room_width REAL,
        room_height REAL,
        speaker_x REAL,
        speaker_y REAL,
        speaker_power REAL
    )''')
    conn.commit()
    return conn

@st.cache_data
def load_materials_db():
    # Esempio dati materiali; in produzione caricare da CSV o DB esterno
    data = {
        'Frequency': [125, 250, 500, 1000, 2000, 4000],
        'Pareti': [0.10, 0.05, 0.04, 0.03, 0.02, 0.02],
        'Soffitto': [0.15, 0.10, 0.07, 0.05, 0.04, 0.03],
        'Pavimento': [0.20, 0.15, 0.10, 0.07, 0.05, 0.04],
        'Trattamento': [0.50, 0.60, 0.65, 0.70, 0.75, 0.80]
    }
    return pd.DataFrame(data)

# --- Funzioni di UI ---

def save_project(conn, project):
    c = conn.cursor()
    c.execute('''
        INSERT INTO projects (name, room_length, room_width, room_height, speaker_x, speaker_y, speaker_power)
        VALUES (?, ?, ?, ?, ?, ?, ?)''',
        (project['name'], project['room_dimensions']['length'], project['room_dimensions']['width'], project['room_dimensions']['height'],
         project['speaker_position'][0], project['speaker_position'][1], project['speaker_power']))
    conn.commit()

def load_projects(conn):
    c = conn.cursor()
    c.execute('SELECT id, name FROM projects')
    return c.fetchall()

def load_project_by_id(conn, project_id):
    c = conn.cursor()
    c.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
    row = c.fetchone()
    if row:
        return {
            'id': row[0],
            'name': row[1],
            'room_dimensions': {'length': row[2], 'width': row[3], 'height': row[4]},
            'speaker_position': (row[5], row[6]),
            'speaker_power': row[7]
        }
    return None

# --- Applicazione principale ---

def main():
    st.set_page_config(page_title="Acoustic Calculator Pro", layout="wide")
    conn = init_database()
    materials_db = load_materials_db()

    if 'current_project' not in st.session_state:
        st.session_state.current_project = {
            'name': 'Nuovo Progetto',
            'room_dimensions': {'length': 5.0, 'width': 4.0, 'height': 3.0},
            'speaker_position': (2.0, 2.0),
            'speaker_power': 1.0,
        }
    if 'saved_projects' not in st.session_state:
        st.session_state.saved_projects = []

    st.title("🎵 Acoustic Calculator Pro")

    page = st.sidebar.selectbox("Seleziona pagina", [
        "🏠 Home",
        "🎛️ Configurazione",
        "🔬 Analisi Avanzata",
        "💾 Salva/Carica Progetti"
    ])

    # --- Pagina Home ---
    if page == "🏠 Home":
        st.write("Benvenuto nell'app per il calcolo acustico. Usa la sidebar per navigare.")

    # --- Pagina Configurazione ---
    elif page == "🎛️ Configurazione":
        st.header("Configurazione stanza e altoparlante")

        dims = st.session_state.current_project['room_dimensions']
        dims['length'] = st.number_input("Lunghezza stanza (m)", min_value=1.0, max_value=30.0, value=dims['length'])
        dims['width'] = st.number_input("Larghezza stanza (m)", min_value=1.0, max_value=30.0, value=dims['width'])
        dims['height'] = st.number_input("Altezza stanza (m)", min_value=2.0, max_value=10.0, value=dims['height'])

        speaker_pos = st.session_state.current_project['speaker_position']
        x = st.number_input("Posizione X altoparlante (m)", min_value=0.0, max_value=dims['length'], value=speaker_pos[0])
        y = st.number_input("Posizione Y altoparlante (m)", min_value=0.0, max_value=dims['width'], value=speaker_pos[1])
        st.session_state.current_project['speaker_position'] = (x, y)

        power = st.number_input("Potenza altoparlante (W)", min_value=0.1, max_value=10.0, value=st.session_state.current_project['speaker_power'])
        st.session_state.current_project['speaker_power'] = power

        st.success("Configurazione aggiornata!")

    # --- Pagina Analisi Avanzata ---
    elif page == "🔬 Analisi Avanzata":
        st.header("Analisi Acustica Avanzata")

        dims = st.session_state.current_project['room_dimensions']
        length, width, height = dims['length'], dims['width'], dims['height']
        volume = length * width * height
        st.write(f"Volume stanza: {volume:.2f} m³")

        surface_materials = {
            'Pareti': 2 * (length * height + width * height) * 0.8,
            'Soffitto': length * width * 1.0,
            'Pavimento': length * width * 0.8,
            'Trattamento': 2 * (length * height + width * height) * 0.2
        }

        freq, rt60 = calculate_rt60_per_band(volume, surface_materials, materials_db)

        st.subheader("Tempo di riverberazione (RT60) per frequenza")
        fig, ax = plt.subplots()
        ax.plot(freq, rt60, marker='o')
        ax.set_xlabel('Frequenza (Hz)')
        ax.set_ylabel('RT60 (s)')
        ax.set_title('Tempo di riverberazione stimato')
        ax.grid(True)
        st.pyplot(fig)

        st.subheader("Frequenze modali principali")
        modes = calculate_room_modes(length, width, height, max_mode=8)
        modes_df = pd.DataFrame(modes, columns=['nx', 'ny', 'nz', 'Freq (Hz)'])
        st.dataframe(modes_df.style.format({'Freq (Hz)': '{:.2f}'}))

        st.subheader("Mappa SPL approssimata a 2D")
        speaker_pos = st.session_state.current_project['speaker_position']
        speaker_power = st.session_state.current_project['speaker_power']
        X, Y, spl_db = calculate_spl_coverage(dims, speaker_pos, speaker_power)

        fig2, ax2 = plt.subplots(figsize=(8, 6))
        c = ax2.contourf(X, Y, spl_db, levels=50, cmap='inferno')
        ax2.plot(speaker_pos[0], speaker_pos[1], 'bo', label='Altoparlante')
        ax2.set_xlabel('Lunghezza (m)')
        ax2.set_ylabel('Larghezza (m)')
        ax2.set_title('Distribuzione SPL stimata (dB)')
        fig2.colorbar(c, ax=ax2, label='SPL (dB)')
        ax2.legend()
        st.pyplot(fig2)

    # --- Pagina Salvataggio e caricamento ---
    elif page == "💾 Salva/Carica Progetti":
        st.header("Salva e Carica Progetti")

        project_name = st.text_input("Nome progetto", value=st.session_state.current_project['name'])

        if st.button("Salva progetto"):
            st.session_state.current_project['name'] = project_name or "Progetto Senza Nome"
            save_project(conn, st.session_state.current_project)
            st.success("Progetto salvato!")

        st.subheader("Progetti salvati")
        projects = load_projects(conn)

        for pid, pname in projects:
            col1, col2, col3 = st.columns([4, 1, 1])
            col1.write(pname)
            if col2.button("Carica", key=f"load_{pid}"):
                proj = load_project_by_id(conn, pid)
                if proj:
                    st.session_state.current_project = proj
                    st.success(f"Progetto '{pname}' caricato!")
                    st.experimental_rerun()
            if col3.button("Elimina", key=f"del_{pid}"):
                c = conn.cursor()
                c.execute("DELETE FROM projects WHERE id = ?", (pid,))
                conn.commit()
                st.success(f"Progetto '{pname}' eliminato!")
                st.experimental_rerun()

if __name__ == "__main__":
    main()
