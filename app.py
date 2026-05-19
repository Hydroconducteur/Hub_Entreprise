import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Hub Entreprise", page_icon="📱", layout="wide")

VOTRE_LIEN_ACTUEL = "https://maupu45.streamlit.app"

# --- CONNEXION CLOUD TURSO ---
conn = st.connection("db", type="sql")

# --- INITIALISATION ---
def init_db():
    queries = [
        "CREATE TABLE IF NOT EXISTS planning (id INTEGER PRIMARY KEY AUTOINCREMENT, num_tache TEXT, assigne_a TEXT, intitule TEXT, temps_estime TEXT, date_realisation TEXT, date_creation_brute TEXT, priorite TEXT)",
        "CREATE TABLE IF NOT EXISTS tchat (id INTEGER PRIMARY KEY AUTOINCREMENT, expediteur TEXT, destinataire TEXT, texte TEXT, date_envoi TEXT, date_creation_brute TEXT)",
        "CREATE TABLE IF NOT EXISTS utilisateurs (prenom TEXT PRIMARY KEY)",
        "CREATE TABLE IF NOT EXISTS planning_archive (id INTEGER PRIMARY KEY AUTOINCREMENT, num_tache TEXT, assigne_a TEXT, intitule TEXT, temps_estime TEXT, date_realisation TEXT, date_creation_brute TEXT, priorite TEXT, date_archivage TEXT)",
        "CREATE TABLE IF NOT EXISTS tchat_archive (id INTEGER PRIMARY KEY AUTOINCREMENT, expediteur TEXT, destinataire TEXT, texte TEXT, date_envoi TEXT, date_creation_brute TEXT, date_archivage TEXT)"
    ]
    for q in queries:
        conn.session.execute(q)
    conn.session.commit()

init_db()

# --- ARCHIVAGE AUTOMATIQUE ---
def nettoyer_et_archiver_data():
    now = datetime.now(ZoneInfo("Europe/Paris"))
    date_2w = (now - timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S")
    date_6m = (now - timedelta(days=180)).strftime("%Y-%m-%d %H:%M:%S")
    date_act = now.strftime("%Y-%m-%d %H:%M:%S")
    
    conn.session.execute("INSERT INTO tchat_archive SELECT *, ? FROM tchat WHERE date_creation_brute < ?", (date_act, date_2w))
    conn.session.execute("DELETE FROM tchat WHERE date_creation_brute < ?", (date_2w,))
    conn.session.execute("INSERT INTO planning_archive SELECT *, ? FROM planning WHERE date_realisation LIKE 'Le %' AND date_creation_brute < ?", (date_act, date_2w))
    conn.session.execute("DELETE FROM planning WHERE date_realisation LIKE 'Le %' AND date_creation_brute < ?", (date_2w,))
    conn.session.execute("DELETE FROM tchat_archive WHERE date_creation_brute < ?", (date_6m,))
    conn.session.execute("DELETE FROM planning_archive WHERE date_creation_brute < ?", (date_6m,))
    conn.session.commit()

nettoyer_et_archiver_data()

# --- SESSION & LOGINS ---
if "user" not in st.session_state: st.session_state.user = None
if "role" not in st.session_state: st.session_state.role = None

# Connexion via URL
if st.session_state.user is None:
    params = st.query_params
    if "qui" in params:
        p = params["qui"].strip().capitalize()
        if p:
            st.session_state.user = p
            st.session_state.role = "Administrateur" if p == "Christophe" else "Employé"
            conn.session.execute("INSERT OR IGNORE INTO utilisateurs (prenom) VALUES (?)", (p,))
            conn.session.commit()
            st.rerun()

# Interface Barre Latérale
with st.sidebar:
    st.title("🔑 Espace Connexion")
    if st.session_state.user is None:
        identifiant = st.text_input("Identifiant")
        if st.button("Se connecter"):
            if identifiant:
                st.session_state.user = identifiant.strip().capitalize()
                st.session_state.role = "Administrateur" if st.session_state.user == "Christophe" else "Employé"
                conn.session.execute("INSERT OR IGNORE INTO utilisateurs (prenom) VALUES (?)", (st.session_state.user,))
                conn.session.commit()
                st.rerun()
    else:
        st.success(f"Connecté : {st.session_state.user}")
        if st.button("Se déconnecter"): st.session_state.user = None; st.rerun()

    liste_pages = ["📋 Planning", "💬 Tchat"]
    if st.session_state.role == "Administrateur": liste_pages.append("🗄️ Archives")
    page = st.radio("Navigation", liste_pages)

# --- PAGES ---
if st.session_state.user is None: st.stop()

if page == "📋 Planning":
    st.title("📋 Planning")
    if st.session_state.role == "Administrateur":
        with st.form("add_tache"):
            t = st.text_input("Mission")
            if st.form_submit_button("Ajouter"):
                conn.session.execute("INSERT INTO planning (intitule, date_realisation) VALUES (?, ?)", (t, "En cours ⏳"))
                conn.session.commit()
    
    taches = conn.query("SELECT * FROM planning")
    st.table(taches)

elif page == "💬 Tchat":
    st.title("💬 Tchat")
    msg = st.text_input("Message")
    if st.button("Envoyer"):
        conn.session.execute("INSERT INTO tchat (expediteur, texte, date_envoi) VALUES (?, ?, ?)", (st.session_state.user, msg, datetime.now().strftime("%H:%M")))
        conn.session.commit()
    st.table(conn.query("SELECT * FROM tchat"))

elif page == "🗄️ Archives":
    st.title("🗄️ Archives (6 mois)")
    st.table(conn.query("SELECT * FROM planning_archive"))
