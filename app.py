import streamlit as st
import sqlite3

@st.cache_resource
def init_database():
    conn = sqlite3.connect('acoustic_calculator.db')
    cursor = conn.cursor()

    # Controlla se la tabella speakers esiste già
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='speakers'")
    if not cursor.fetchone():
        # Crea la tabella speakers
        cursor.execute('''
            CREATE TABLE speakers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                speaker TEXT NOT NULL,
                diameter REAL NOT NULL,
                height REAL NOT NULL
            )
        ''')

        # Inserisci dati di default
        speakers_data = [
            ('SEAS Prestige 27TAF/G', 27, 7),
            ('Visaton BG 20', 20, 5),
            ('Visaton BG 13', 13, 4),
        ]

        cursor.executemany('INSERT INTO speakers (speaker, diameter, height) VALUES (?, ?, ?)', speakers_data)
        conn.commit()

    return conn

def main():
    st.title("Calcolatore Acustico")

    conn = init_database()
    cursor = conn.cursor()

    # Prendi la lista dei speakers dal DB
    cursor.execute("SELECT id, speaker FROM speakers")
    speakers = cursor.fetchall()
    speaker_options = {str(id): name for id, name in speakers}

    selected_id = st.selectbox("Scegli un altoparlante", options=list(speaker_options.keys()),
                               format_func=lambda x: speaker_options[x])

    if selected_id:
        cursor.execute("SELECT diameter, height FROM speakers WHERE id=?", (selected_id,))
        row = cursor.fetchone()
        if row:
            diameter, height = row
            st.write(f"Diametro: {diameter} cm")
            st.write(f"Altezza: {height} cm")

    # Altre parti del tuo codice con input/output etc.

if __name__ == "__main__":
    main()
