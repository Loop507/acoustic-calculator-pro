import streamlit as st
import sqlite3

@st.cache_resource
def get_connection():
    # Connessione persistente, thread-safe in Streamlit
    conn = sqlite3.connect('acoustic_calculator.db', check_same_thread=False)
    return conn

def init_db(conn):
    cursor = conn.cursor()
    # Crea tabella altoparlanti se non esiste
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS speakers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            speaker TEXT NOT NULL,
            diameter REAL NOT NULL,
            height REAL NOT NULL
        )
    ''')
    conn.commit()

    # Inserisce dati di esempio se tabella vuota
    cursor.execute("SELECT COUNT(*) FROM speakers")
    count = cursor.fetchone()[0]
    if count == 0:
        sample_data = [
            ('SEAS Prestige 27TAF/G', 27, 7),
            ('Visaton BG 20', 20, 5),
            ('Visaton BG 13', 13, 4),
        ]
        cursor.executemany(
            'INSERT INTO speakers (speaker, diameter, height) VALUES (?, ?, ?)', sample_data
        )
        conn.commit()

def main():
    st.title("Calcolatore Acustico")

    conn = get_connection()
    init_db(conn)
    cursor = conn.cursor()

    # Carica gli altoparlanti disponibili
    cursor.execute("SELECT id, speaker FROM speakers")
    rows = cursor.fetchall()
    speakers = {str(row[0]): row[1] for row in rows}

    selected_id = st.selectbox("Scegli un altoparlante", options=list(speakers.keys()), format_func=lambda x: speakers[x])

    cursor.execute("SELECT diameter, height FROM speakers WHERE id = ?", (selected_id,))
    result = cursor.fetchone()
    if result:
        diameter, height = result
        st.write(f"Diametro: {diameter} cm")
        st.write(f"Altezza: {height} cm")
    else:
        st.write("Altoparlante non trovato.")

    # Puoi aggiungere qui altri input o calcoli

if __name__ == "__main__":
    main()
