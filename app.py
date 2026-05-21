import streamlit as st
import requests
import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Hub Entreprise Pro", page_icon="📱", layout="wide")

VOTRE_LIEN_ACTUEL = "https://maupu45.streamlit.app"

# --- INJECTION CSS PREMIUM & ULTRA-ADAPTATIVE ---
st.markdown("""
<style>
/* Reset et utilitaires */
.mob-only { display: none; }
.pc-only { display: block; }

/* Force le centrage parfait de TOUS les boutons Streamlit dans leurs colonnes respectives */
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] {
    display: flex !important;
    justify-content: center !important;
    width: 100% !important;
}

/* --- 🌟 STYLISATION DES BOUTONS DU TABLEAU (LOOK PREMIUM) --- */

/* 1. Le Bouton d'Action Principal (Fait / Annuler) - Colonne 7 */
div[data-testid="stHorizontalBlock"]:has(.row-marker) div[data-testid="column"]:nth-of-type(7) button {
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
    color: white !important;
    border: none !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 6px 16px !important;
    border-radius: 8px !important;
    box-shadow: 0 3px 8px rgba(37, 99, 235, 0.25) !important;
    transition: all 0.2s ease-in-out !important;
    cursor: pointer !important;
}
div[data-testid="stHorizontalBlock"]:has(.row-marker) div[data-testid="column"]:nth-of-type(7) button:hover {
    background: linear-gradient(135deg, #1d4ed8, #1e40af) !important;
    box-shadow: 0 5px 14px rgba(37, 99, 235, 0.4) !important;
    transform: translateY(-1px) !important;
}
div[data-testid="stHorizontalBlock"]:has(.row-marker) div[data-testid="column"]:nth-of-type(7) button:active {
    transform: translateY(1px) !important;
}

/* 2. Le Bouton Supprimer (Poubelle) - Colonne 8 */
div[data-testid="stHorizontalBlock"]:has(.row-marker) div[data-testid="column"]:nth-of-type(8) button {
    background: rgba(239, 68, 68, 0.06) !important;
    color: #ef4444 !important;
    border: 1px solid rgba(239, 68, 68, 0.2) !important;
    border-radius: 8px !important;
    font-size: 1.05rem !important;
    padding: 5px !important;
    transition: all 0.2s ease-in-out !important;
}
div[data-testid="stHorizontalBlock"]:has(.row-marker) div[data-testid="column"]:nth-of-type(8) button:hover {
    background: #ef4444 !important;
    color: white !important;
    border-color: #ef4444 !important;
    box-shadow: 0 4px 12px rgba(239, 68, 68, 0.35) !important;
    transform: translateY(-1px) !important;
}
div[data-testid="stHorizontalBlock"]:has(.row-marker) div[data-testid="column"]:nth-of-type(8) button:active {
    transform: translateY(1px) !important;
}


/* --- 💻 COMPORTEMENT GRAPHIQUE DESKTOP (PC) --- */
@media (min-width: 769px) {
    div[data-testid="stHorizontalBlock"]:has(.header-mark) {
        background: rgba(128, 128, 128, 0.08) !important;
        border-radius: 10px !important;
        padding: 14px 20px !important;
        margin-bottom: 16px !important;
        border-bottom: 3px solid var(--primary-color) !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.header-mark) div[data-testid="stMarkdownContainer"] p {
        color: var(--text-color) !important;
        font-weight: 700 !important;
        font-size: 0.82rem !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        opacity: 0.8;
        text-align: center !important;
    }

    div[data-testid="stHorizontalBlock"]:has(.row-marker) {
        background: var(--secondary-background-color) !important;
        border: 1px solid rgba(128, 128, 128, 0.15) !important;
        border-radius: 10px !important;
        padding: 12px 20px !important;
        margin-bottom: 10px !important;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05) !important;
        align-items: center !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease !important;
    }
    
    div[data-testid="stHorizontalBlock"]:has(.row-marker):hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.12) !important;
        border-color: rgba(128, 128, 128, 0.3) !important;
    }

    div[data-testid="stHorizontalBlock"]:has(.prio-high) { border-left: 5px solid #ef4444 !important; }
    div[data-testid="stHorizontalBlock"]:has(.prio-med) { border-left: 5px solid #f97316 !important; }
    div[data-testid="stHorizontalBlock"]:has(.prio-low) { border-left: 5px solid #10b981 !important; }

    div[data-testid="stHorizontalBlock"] [data-testid="element-container"] {
        margin-bottom: 0 !important;
        margin-top: 0 !important;
    }

    div[data-testid="stHorizontalBlock"]:has(.row-marker) div[data-testid="column"]:nth-of-type(3) button {
        background: transparent !important;
        border: none !important;
        color: var(--text-color) !important;
        text-align: center !important;
        padding: 0 !important;
        font-weight: 500 !important;
        font-size: 0.92rem !important;
        text-decoration: underline rgba(128, 128, 128, 0.2) !important;
        width: 100% !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.row-marker) div[data-testid="column"]:nth-of-type(3) button:hover {
        color: var(--primary-color) !important;
        text-decoration: underline var(--primary-color) !important;
        background: transparent !important;
    }
}

/* --- 📱 COMPORTEMENT GRAPHIQUE MOBILE (SMARTPHONES) --- */
@media (max-width: 768px) {
    .mob-only { display: block !important; }
    .pc-only { display: none !important; }
    
    div[data-testid="stHorizontalBlock"]:has(.header-mark) { display: none !important; }
    
    div[data-testid="stHorizontalBlock"]:has(.row-marker) {
        background: var(--secondary-background-color) !important;
        border: 1px solid rgba(128, 128, 128, 0.18) !important;
        border-radius: 14px !important;
        padding: 16px !important;
        margin-bottom: 16px !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.08) !important;
        display: flex !important;
        flex-direction: column !important;
    }
    
    div[data-testid="stHorizontalBlock"]:has(.prio-high) { border-left: 6px solid #ef4444 !important; }
    div[data-testid="stHorizontalBlock"]:has(.prio-med) { border-left: 6px solid #f97316 !important; }
    div[data-testid="stHorizontalBlock"]:has(.prio-low) { border-left: 6px solid #10b981 !important; }

    div[data-testid="stHorizontalBlock"]:has(.row-marker) > div[data-testid="column"] {
        width: 100% !important;
        display: block !important;
        margin: 0 !important;
    }
    
    .mob-title {
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        color: var(--text-color) !important;
        padding-bottom: 6px !important;
        margin-bottom: 12px !important;
        border-bottom: 1px solid rgba(128, 128, 128, 0.15) !important;
    }
    
    .mob-row {
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        padding: 8px 0 !important;
        border-bottom: 1px solid rgba(128, 128, 128, 0.08) !important;
    }
    .mob-row:last-of-type { border-bottom: none !important; }
    
    .mob-lbl {
        font-size: 0.75rem !important;
        color: rgba(128, 128, 128, 0.6) !important;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .mob-val {
        font-size: 0.92rem !important;
        color: var(--text-color) !important;
        font-weight: 600;
    }

    div[data-testid="stHorizontalBlock"]:has(.row-marker) div[data-testid="column"]:nth-of-type(3) button {
        width: 100% !important;
        text-align: center !important;
        background: rgba(128, 128, 128, 0.08) !important;
        border: 1px dashed rgba(128, 128, 128, 0.3) !important;
        padding: 8px !important;
        border-radius: 8px !important;
        margin-top: 5px !important;
    }

    div[data-testid="stHorizontalBlock"]:has(.row-marker) button {
        width: 100% !important;
        border-radius: 8px !important;
        padding: 10px !important;
        font-weight: 600 !important;
        margin-top: 8px !important;
    }
}

/* --- BADGES DE STATUT STYLE CAPSULE (PILLS) --- */
.status-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
    text-align: center;
}
.status-pending {
    background: rgba(245, 158, 11, 0.12) !important;
    color: #f59e0b !important;
    border: 1px solid rgba(245, 158, 11, 0.3);
}
.status-done {
    background: rgba(16, 185, 129, 0.12) !important;
    color: #10b981 !important;
    border: 1px solid rgba(16, 185, 129, 0.3);
}
</style>
""", unsafe_allow_html=True)


# --- CONNEXION BASE DE DONNÉES CLOUD (TURSO HTTP) ---
DB_URL = st.secrets["DB_URL"].replace("libsql://", "https://")
TOKEN = st.secrets["DB_TOKEN"]

class TursoAdapter:
    def __init__(self):
        self.last_fetched_rows = []

    def execute(self, sql, params=()):
        if "turso_session" not in st.session_state:
            st.session_state.turso_session = requests.Session()
            
        headers = {
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json"
        }
        
        args = []
        for p in params:
            if isinstance(p, int): args.append({"type": "integer", "value": str(p)})
            elif isinstance(p, float): args.append({"type": "float", "value": str(p)})
            elif p is None: args.append({"type": "null"})
            else: args.append({"type": "text", "value": str(p)})
                
        payload = {
            "requests": [
                {"type": "execute", "stmt": {"sql": sql, "args": args}},
                {"type": "close"}
            ]
        }
        
        resp = st.session_state.turso_session.post(f"{DB_URL}/v2/pipeline", json=payload, headers=headers)
        if resp.status_code != 200:
            raise sqlite3.OperationalError(f"Erreur HTTP {resp.status_code}: {resp.text}")
            
        data = resp.json()
        results = data.get("results", [])
        if not results:
            self.last_fetched_rows = []
            return self
            
        first_result = results[0]
        if first_result.get("type") == "error":
            raise sqlite3.OperationalError(first_result.get("error", {}).get("message", "Erreur SQL"))
            
        raw_rows = first_result.get("response", {}).get("result", {}).get("rows", [])
        parsed_rows = []
        for raw_row in raw_rows:
            parsed_row = []
            for col in raw_row:
                ctype = col.get("type")
                cval = col.get("value")
                if ctype == "integer": parsed_row.append(int(cval))
                elif ctype == "float": parsed_row.append(float(cval))
                elif ctype == "null": parsed_row.append(None)
                else: parsed_row.append(cval)
            parsed_rows.append(tuple(parsed_row))
            
        self.last_fetched_rows = parsed_rows
        return self

    def fetchall(self): return self.last_fetched_rows
    def fetchone(self): return self.last_fetched_rows[0] if self.last_fetched_rows else None
    def commit(self): pass
    def cursor(self): return self

conn = TursoAdapter()
cursor = conn.cursor()

# --- INITIALISATION BASE DE DONNÉES COCHÉE ET MISE À JOUR ADM ---
def initialiser_structure_base():
    cursor.execute("CREATE TABLE IF NOT EXISTS planning (id INTEGER PRIMARY KEY AUTOINCREMENT, num_tache TEXT, assigne_a TEXT, intitule TEXT, temps_estime TEXT, date_realisation TEXT, date_creation_brute TEXT, priorite TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS tchat (id INTEGER PRIMARY KEY AUTOINCREMENT, expediteur TEXT, destinataire TEXT, texte TEXT, date_envoi TEXT, date_creation_brute TEXT, garder_permanent INTEGER DEFAULT 0)")
    cursor.execute("CREATE TABLE IF NOT EXISTS utilisateurs (prenom TEXT PRIMARY KEY, code_secret TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS planning_archive (id INTEGER PRIMARY KEY AUTOINCREMENT, num_tache TEXT, assigne_a TEXT, intitule TEXT, temps_estime TEXT, date_realisation TEXT, date_creation_brute TEXT, priorite TEXT, date_archivage TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS tchat_archive (id INTEGER PRIMARY KEY AUTOINCREMENT, expediteur TEXT, destinataire TEXT, texte TEXT, date_envoi TEXT, date_creation_brute TEXT, date_archivage TEXT, garder_permanent INTEGER DEFAULT 0)")
    
    try: cursor.execute("ALTER TABLE planning ADD COLUMN priorite TEXT DEFAULT '🟢 Pas très important'")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE tchat ADD COLUMN garder_permanent INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE tchat_archive ADD COLUMN garder_permanent INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE utilisateurs ADD COLUMN code_secret TEXT DEFAULT '1234'")
    except sqlite3.OperationalError: pass
    
    # --- MISE À JOUR ET FORCAGE DU CODE POUR CHRISTOPHE ---
    cursor.execute("SELECT prenom, code_secret FROM utilisateurs WHERE prenom = 'Christophe'")
    admin_row = cursor.fetchone()
    
    if not admin_row:
        cursor.execute("INSERT OR REPLACE INTO utilisateurs (prenom, code_secret) VALUES ('Christophe', 'Admin45')")
    elif admin_row[1] == '1234' or admin_row[1] is None or admin_row[1] == '':
        cursor.execute("UPDATE utilisateurs SET code_secret = 'Admin45' WHERE prenom = 'Christophe'")
        
    conn.commit()

if "db_ready" not in st.session_state:
    initialiser_structure_base()
    st.session_state.db_ready = True


# --- ALGORITHME DE NETTOYAGE & ARCHIVAGE AUTOMATIQUE ---
@st.cache_data(ttl=60)
def nettoyer_et_archiver_data():
    try:
        now_paris = datetime.now(ZoneInfo("Europe/Paris"))
        heure_actuelle = now_paris.hour
        date_actuelle_str = now_paris.strftime("%Y-%m-%d %H:%M:%S")
        
        if heure_actuelle >= 20 or heure_actuelle < 8:
            cursor.execute("SELECT COUNT(*) FROM tchat")
            if cursor.fetchone()[0] > 0:
                cursor.execute("""
                    INSERT INTO tchat_archive (expediteur, destinataire, texte, date_envoi, date_creation_brute, date_archivage, garder_permanent)
                    SELECT expediteur, destinataire, texte, date_envoi, date_creation_brute, ?, garder_permanent FROM tchat
                """, (date_actuelle_str,))
                cursor.execute("DELETE FROM tchat")
                conn.commit()

        il_y_a_deux_semaines = (now_paris - timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("DELETE FROM tchat_archive WHERE date_creation_brute < ? AND garder_permanent = 0", (il_y_a_deux_semaines,))
        conn.commit()
        
        cursor.execute("""
            INSERT INTO planning_archive (num_tache, assigne_a, intitule, temps_estime, date_realisation, date_creation_brute, priorite, date_archivage)
            SELECT num_tache, assigne_a, intitule, temps_estime, date_realisation, date_creation_brute, priorite, ?
            FROM planning WHERE date_realisation LIKE 'Fait le %' AND date_creation_brute < ?
        """, (date_actuelle_str, il_y_a_deux_semaines))
        cursor.execute("DELETE FROM planning WHERE date_realisation LIKE 'Fait le %' AND date_creation_brute < ?", (il_y_a_deux_semaines,))
        
        il_y_a_six_mois = (now_paris - timedelta(days=180)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("DELETE FROM planning_archive WHERE date_creation_brute < ?", (il_y_a_six_mois,))
        conn.commit()
    except Exception:
        pass
    return True

nettoyer_et_archiver_data()

# --- GESTION DES SESSIONS ---
if "user" not in st.session_state: st.session_state.user = None
if "role" not in st.session_state: st.session_state.role = None
if "navigation_page" not in st.session_state: st.session_state.navigation_page = "📋 Planning de l'équipe"
if "modal_mission" not in st.session_state: st.session_state.modal_mission = None

# --- CONNEXION AUTOMATIQUE VIA URL (SÉCURISÉE) ---
parametres_url = st.query_params
if st.session_state.user is None and "qui" in parametres_url and "code" in parametres_url:
    prenom_detecte = parametres_url["qui"].strip().capitalize()
    code_detecte = parametres_url["code"].strip()
    
    cursor.execute("SELECT code_secret FROM utilisateurs WHERE prenom = ?", (prenom_detecte,))
    row = cursor.fetchone()
    if row and row[0] == code_detecte:
        st.session_state.user = prenom_detecte
        if prenom_detecte == "Christophe":
            st.session_state.role = "Administrateur"
        else:
            st.session_state.role = "Employé"
        st.rerun()

# --- ÉCRAN DE CONNEXION PRINCIPAL ---
if st.session_state.user is None:
    st.title("📱 Hub Logistique & Entreprise")
    st.subheader("Veuillez vous identifier pour accéder aux outils.")
    
    with st.container(border=True):
        identifiant = st.text_input("Identifiant (Votre Prénom)")
        code_s = st.text_input("Code Secret", type="password")
        
        if st.button("Se connecter au Hub 🚀", use_container_width=True):
            prenom_propre = identifiant.strip().capitalize()
            if prenom_propre != "":
                cursor.execute("SELECT code_secret FROM utilisateurs WHERE prenom = ?", (prenom_propre,))
                row = cursor.fetchone()
                
                if row and row[0] == code_s:
                    st.session_state.user = prenom_propre
                    if prenom_propre == "Christophe":
                        st.session_state.role = "Administrateur"
                    else:
                        st.session_state.role = "Employé"
                    st.rerun()
                else:
                    st.error("❌ Prénom ou Code Secret incorrect. Vous devez être invité par Christophe.")
    st.stop()

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.success(f"👤 Connecté : {st.session_state.user} ({st.session_state.role})")
    if st.button("Se déconnecter", use_container_width=True):
        st.session_state.user = None
        st.session_state.role = None
        st.session_state.navigation_page = "📋 Planning de l'équipe"
        st.query_params.clear()
        st.rerun()
        
    st.write("---")
    st.title("🗺️ Menu Principal")
    liste_pages = ["📋 Planning de l'équipe", "💬 Zone Tchat"]
    if st.session_state.role == "Administrateur": liste_pages.append("🗄️ Archives (6 mois)")
    page = st.radio("Aller vers :", liste_pages, key="navigation_page")

    if st.session_state.role == "Administrateur":
        st.write("---")
        st.title("🛡️ Gestion Sécurité")
        
        # Section de gestion des membres & codes d'accès
        with st.expander("👥 Liste Blanche & Codes", expanded=False):
            with st.form("form_ajouter_employe", clear_on_submit=True):
                st.caption("Ajouter un nouvel employé autorisé :")
                nv_nom = st.text_input("Prénom").strip().capitalize()
                # LE CORRECTIF CORRIGÉ ICI (Changement de type="text" vers type="default")
                nv_code = st.text_input("Code Secret d'accès", type="default", help="Ex: 4 chiffres")
                if st.form_submit_button("➕ Autoriser l'employé", use_container_width=True):
                    if nv_nom and nv_code:
                        cursor.execute("INSERT OR REPLACE INTO utilisateurs (prenom, code_secret) VALUES (?, ?)", (nv_nom, nv_code))
                        conn.commit()
                        st.success(f"L'employé {nv_nom} a été ajouté.")
                        st.rerun()

            st.write("---")
            cursor.execute("SELECT prenom, code_secret FROM utilisateurs WHERE prenom != 'Christophe' ORDER BY prenom ASC")
            membres = cursor.fetchall()
            if membres:
                for m in membres:
                    nom_membre, code_membre = m
                    col_m_nom, col_m_code, col_m_del = st.columns([4, 3, 3], vertical_alignment="center")
                    col_m_nom.write(f"• **{nom_membre}**")
                    col_m_code.code(code_membre, language="text")
                    if col_m_del.button("🗑️", key=f"user_del_{nom_membre}", use_container_width=True):
                        cursor.execute("DELETE FROM utilisateurs WHERE prenom = ?", (nom_membre,))
                        conn.commit()
                        st.rerun()
            else:
                st.caption("Aucun employé sur liste blanche.")

        with st.expander("🔗 Liens d'accès sécurisés", expanded=False):
            st.caption("Liens magiques de connexion automatique incluant les clés d'accès :")
            base_url = VOTRE_LIEN_ACTUEL

            cursor.execute("SELECT prenom, code_secret FROM utilisateurs WHERE prenom = 'Christophe'")
            c_data = cursor.fetchone()
            if c_data:
                st.write("Lien **Christophe** :")
                st.code(f"{base_url}/?qui=Christophe&code={c_data[1]}", language="text")
            
            for u in membres:
                st.write(f"Lien **{u[0]}** :")
                st.code(f"{base_url}/?qui={u[0]}&code={u[1]}", language="text")


# ==========================================
# PAGE 1 : LE PLANNING DYNAMIQUE PREMIUM
# ==========================================
if page == "📋 Planning de l'équipe":
    st.title("📋 Planning Global de l'Équipe")
    st.caption("Suivi des flux en temps réel. Cliquez sur le texte d'une mission pour l'ouvrir en grand.")

    if st.session_state.modal_mission:
        num_m, qui_m, quoi_m = st.session_state.modal_mission
        with st.container(border=True):
            st.markdown(f"### 🔍 Détails de la Mission — Tâche N° {num_m}")
            st.markdown(f"👤 **Assigné à :** {qui_m}")
            st.markdown("📋 **Description complète :**")
            st.info(quoi_m)
            if st.button("Fermer la description ❌", use_container_width=True):
                st.session_state.modal_mission = None
                st.rerun()
        st.write("---")

    if st.session_state.role == "Administrateur":
        with st.expander("➕ Créer et affecter une nouvelle tâche", expanded=False):
            cursor.execute("SELECT prenom FROM utilisateurs WHERE prenom != 'Christophe'")
            liste_employes = [row[0] for row in cursor.fetchall()]
            
            with st.form("form_tache"):
                col1, col2 = st.columns(2)
                with col1:
                    num_t = st.text_input("N° de tâche", value="001")
                    qui = st.selectbox("Assigné à", liste_employes) if liste_employes else st.text_input("Assigné à")
                    priorite_choisie = st.selectbox("Urgence", ["🟢 Pas très important", "🟠 Important", "🔴 Très urgent"])
                with col2:
                    temps = st.text_input("Temps estimé (ex: 2h30)")
                    action = st.text_area("Description du travail")
                
                if st.form_submit_button("Ajouter au planning"):
                    if qui and action:
                        now_brute = datetime.now(ZoneInfo("Europe/Paris")).strftime("%Y-%m-%d %H:%M:%S")
                        cursor.execute("INSERT INTO planning (num_tache, assigne_a, intitule, temps_estime, date_realisation, date_creation_brute, priorite) VALUES (?, ?, ?, ?, ?, ?, ?)", (num_t, qui, action, temps, "En cours ⏳", now_brute, priorite_choisie))
                        conn.commit()
                        st.rerun()

    st.write("### 📅 Tâches actives")
    
    @st.fragment(run_every=8)
    def afficher_tableau_taches():
        cursor.execute("SELECT id, num_tache, assigne_a, intitule, temps_estime, date_realisation, priorite FROM planning")
        taches = cursor.fetchall()
        
        if taches:
            if st.session_state.role == "Administrateur":
                rep = [0.6, 1.2, 2.7, 1.8, 0.7, 2.2, 1.4, 0.6]
                cols_h = st.columns(rep, vertical_alignment="center")
            else:
                rep = [0.6, 1.3, 3.0, 1.9, 0.8, 2.4, 1.4]
                cols_h = st.columns(rep, vertical_alignment="center")
            
            with cols_h[0]: st.markdown("<div class='header-mark'></div><div style='text-align: center;'>N°</div>", unsafe_allow_html=True)
            with cols_h[1]: st.markdown("<div style='text-align: center;'>Assigné à</div>", unsafe_allow_html=True)
            with cols_h[2]: st.markdown("<div style='text-align: center;'>Mission (Cliquer)</div>", unsafe_allow_html=True)
            with cols_h[3]: st.markdown("<div style='text-align: center;'>Urgence</div>", unsafe_allow_html=True)
            with cols_h[4]: st.markdown("<div style='text-align: center;'>Temps</div>", unsafe_allow_html=True)
            with cols_h[5]: st.markdown("<div style='text-align: center;'>Statut</div>", unsafe_allow_html=True)
            with cols_h[6]: st.markdown("<div style='text-align: center;'>Action</div>", unsafe_allow_html=True)
            if st.session_state.role == "Administrateur": 
                with cols_h[7]: st.markdown("<div style='text-align: center;'>Suppr.</div>", unsafe_allow_html=True)

            for t in taches:
                id_t, num, qui, quoi, temps, statut, priorite = t
                if not priorite: priorite = "🟢 Pas très important"
                
                prio_class = "prio-low"
                if "Important" in priorite: prio_class = "prio-med"
                elif "urgent" in priorite.lower(): prio_class = "prio-high"
                
                cols = st.columns(rep, vertical_alignment="center")
                
                with cols[0]:
                    st.markdown(f'<div class="row-marker {prio_class}"></div><div class="pc-only" style="text-align: center; font-weight: bold; opacity:0.8;">{num}</div><div class="mob-only mob-title">📋 Tâche N° {num}</div>', unsafe_allow_html=True)
                
                with cols[1]:
                    st.markdown(f'<div class="pc-only" style="text-align: center; font-weight: 600;">{qui}</div><div class="mob-only mob-row"><span class="mob-lbl">👤 Assigné à</span><span class="mob-val">{qui}</span></div>', unsafe_allow_html=True)
                
                with cols[2]:
                    st.markdown('<div class="mob-only" style="margin-top: 4px; margin-bottom: -2px;"><span class="mob-lbl">📋 Mission (Ouvrir)</span></div>', unsafe_allow_html=True)
                    limite_caracteres = 32
                    quoi_affiche = quoi if len(quoi) <= limite_caracteres else quoi[:limite_caracteres] + "..."
                    if st.button(quoi_affiche, key=f"mission_btn_{id_t}", use_container_width=True):
                        st.session_state.modal_mission = (num, qui, quoi)
                        st.rerun()

                with cols[3]:
                    st.markdown(f'<div class="pc-only" style="text-align: center; font-size:0.9rem;">{priorite}</div><div class="mob-only mob-row"><span class="mob-lbl">🚨 Urgence</span><span class="mob-val">{priorite}</span></div>', unsafe_allow_html=True)
                
                with cols[4]:
                    st.markdown(f'<div class="pc-only" style="text-align: center; font-weight:500;">{temps}</div><div class="mob-only mob-row"><span class="mob-lbl">⏱️ Temps</span><span class="mob-val">{temps}</span></div>', unsafe_allow_html=True)
                
                with cols[5]:
                    status_class = "status-pending" if "En cours" in statut else "status-done"
                    st.markdown(f"""
                    <div class="pc-only" style="text-align: center;"><span class="status-badge {status_class}">{statut}</span></div>
                    <div class="mob-only mob-row">
                        <span class="mob-lbl">⚡ Statut</span>
                        <span class="status-badge {status_class}">{statut}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with cols[6]:
                    if "En cours" in statut:
                        if st.session_state.user == qui or st.session_state.role == "Administrateur":
                            if st.button("Fait ✅", key=f"btn_fait_{id_t}", use_container_width=True):
                                maintenant = datetime.now(ZoneInfo("Europe/Paris")).strftime("%d/%m/%Y à %H:%M")
                                cursor.execute("UPDATE planning SET date_realisation = ? WHERE id = ?", (f"Fait le {maintenant}", id_t))
                                conn.commit()
                                st.rerun()
                        else:
                            st.markdown("<div class='pc-only' style='color: #cbd5e1; text-align: center; opacity:0.3;'>—</div>", unsafe_allow_html=True)
                    else:
                        if st.session_state.user == qui or st.session_state.role == "Administrateur":
                            if st.button("Annuler ↩️", key=f"btn_annuler_{id_t}", use_container_width=True):
                                cursor.execute("UPDATE planning SET date_realisation = 'En cours ⏳' WHERE id = ?", (id_t,))
                                conn.commit()
                                st.rerun()
                        else:
                            st.markdown("<div class='pc-only' style='color: #cbd5e1; text-align: center; opacity:0.3;'>—</div>", unsafe_allow_html=True)
                
                if st.session_state.role == "Administrateur":
                    with cols[7]:
                        if st.button("🗑️", key=f"btn_del_tache_{id_t}", use_container_width=True):
                            cursor.execute("DELETE FROM planning WHERE id = ?", (id_t,))
                            conn.commit()
                            st.rerun()
        else:
            st.info("Aucune tâche planifiée actuellement.")

    afficher_tableau_taches()


# ==========================================
# PAGE 2 : LE TCHAT PRIVÉ
# ==========================================
elif page == "💬 Zone Tchat":
    st.title("💬 Centre de Communication")
    st.caption("Les messages restent ici de 8h à 20h, puis partent automatiquement en Archives.")
    
    cursor.execute("SELECT prenom FROM utilisateurs")
    employes = [row[0] for row in cursor.fetchall()]
    if "Christophe" not in employes: employes.append("Christophe")
        
    options_tchat = ["📢 Canal #Général"] + [f"🔒 Privé avec {emp}" for emp in employes if emp != st.session_state.user]
    choix_tchat = st.selectbox("Discussion active :", options_tchat)
    st.write("---")

    @st.fragment(run_every=6)
    def afficher_flux_messages(cible_tchat):
        if cible_tchat == "📢 Canal #Général":
            st.subheader("📢 Fil d'actualité Général")
            cursor.execute("SELECT id, expediteur, texte, date_envoi, garder_permanent FROM tchat WHERE destinataire = 'Tous' ORDER BY id ASC")
        else:
            cible = cible_tchat.replace("🔒 Privé avec ", "")
            st.subheader(f"🔒 Bulle privée avec {cible}")
            cursor.execute("SELECT id, expediteur, texte, date_envoi, garder_permanent FROM tchat WHERE (expediteur = ? AND destinataire = ?) OR (expediteur = ? AND destinataire = ?) ORDER BY id ASC", (st.session_state.user, cible, cible, st.session_state.user))
        
        messages = cursor.fetchall()
        zone_msg = st.container(height=380)
        with zone_msg:
            if messages:
                for m in messages:
                    id_msg, exp, txt, date, permanent = m
                    
                    base_largeur = [8.5, 0.75, 0.75] if st.session_state.role == "Administrateur" else [9.2, 0.8]
                    cols_msg = st.columns(base_largeur, vertical_alignment="center")
                    
                    with cols_msg[0]:
                        label_perm = " 📌 [Sauvegardé]" if permanent == 1 else ""
                        st.chat_message("user" if exp == st.session_state.user else "assistant").write(f"**{'Vous' if exp == st.session_state.user else exp}** ({date}){label_perm} : {txt}")
                    
                    if cols_msg[1].button("📍" if permanent == 1 else "📌", key=f"pin_live_{id_msg}", help="Ne pas archiver", use_container_width=True):
                        cursor.execute("UPDATE tchat SET garder_permanent = ? WHERE id = ?", (0 if permanent == 1 else 1, id_msg))
                        conn.commit()
                        st.rerun()
                        
                    if st.session_state.role == "Administrateur" and cols_msg[2].button("🗑️", key=f"del_live_{id_msg}", use_container_width=True):
                        cursor.execute("DELETE FROM tchat WHERE id = ?", (id_msg,))
                        conn.commit()
                        st.rerun()
            else:
                st.caption("Aucun échange pour le moment.")

    afficher_flux_messages(choix_tchat)

    with st.form("form_msg", clear_on_submit=True):
        col_txt, col_btn = st.columns([8.2, 1.8], vertical_alignment="center")
        nouveau_msg = col_txt.text_input("Tapez votre message ici...", label_visibility="collapsed")
        if col_btn.form_submit_button("Envoyer 🚀", use_container_width=True) and nouveau_msg.strip() != "":
            dest = "Tous" if choix_tchat == "📢 Canal #Général" else choix_tchat.replace("🔒 Privé avec ", "")
            now_paris = datetime.now(ZoneInfo("Europe/Paris"))
            cursor.execute("INSERT INTO tchat (expediteur, destinataire, texte, date_envoi, date_creation_brute, garder_permanent) VALUES (?, ?, ?, ?, ?, 0)", (st.session_state.user, dest, nouveau_msg.strip(), now_paris.strftime("%H:%M"), now_paris.strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            st.rerun()


# ==========================================
# 🗄️ PAGE 3 : ARCHIVES ADAPTATIVES
# ==========================================
elif page == "🗄️ Archives (6 mois)" and st.session_state.role == "Administrateur":
    st.title("🗄️ Archives Administrateur")
    
    if st.session_state.modal_mission:
        num_m, qui_m, quoi_m = st.session_state.modal_mission
        with st.container(border=True):
            st.markdown(f"### 🔍 Détails de la Mission Archivée — Tâche N° {num_m}")
            st.markdown(f"👤 **Assigné à :** {qui_m}")
            st.info(quoi_m)
            if st.button("Fermer la description ❌", use_container_width=True):
                st.session_state.modal_mission = None
                st.rerun()
        st.write("---")

    onglet_taches, onglet_messages = st.tabs(["📋 Archives Tâches", "💬 Archives Tchat"])
    
    with onglet_taches:
        cursor.execute("""
            SELECT 'historique' AS provenance, id, num_tache, assigne_a, intitule, temps_estime, date_realisation, priorite, date_archivage 
            FROM planning_archive
            UNION ALL
            SELECT 'recents' AS provenance, id, num_tache, assigne_a, intitule, temps_estime, date_realisation, priorite, 'En attente' AS date_archivage 
            FROM planning 
            WHERE date_realisation LIKE 'Fait le %'
            ORDER BY date_archivage DESC
        """)
        taches_archived = cursor.fetchall()
        
        if taches_archived:
            rep_arch = [0.6, 1.2, 2.7, 1.5, 0.8, 2.0, 1.4, 0.8]
            cols_h = st.columns(rep_arch, vertical_alignment="center")
            
            with cols_h[0]: st.markdown("<div class='header-mark'></div><div style='text-align: center;'>N°</div>", unsafe_allow_html=True)
            with cols_h[1]: st.markdown("<div style='text-align: center;'>Assigné à</div>", unsafe_allow_html=True)
            with cols_h[2]: st.markdown("<div style='text-align: center;'>Mission</div>", unsafe_allow_html=True)
            with cols_h[3]: st.markdown("<div style='text-align: center;'>Urgence</div>", unsafe_allow_html=True)
            with cols_h[4]: st.markdown("<div style='text-align: center;'>Temps</div>", unsafe_allow_html=True)
            with cols_h[5]: st.markdown("<div style='text-align: center;'>Statut</div>", unsafe_allow_html=True)
            with cols_h[6]: st.markdown("<div style='text-align: center;'>Archivé le</div>", unsafe_allow_html=True)
            with cols_h[7]: st.markdown("<div style='text-align: center;'>Suppr.</div>", unsafe_allow_html=True)
            
            for ta in taches_archived:
                provenance, id_arch, num, qui, quoi, temps, statut, priorite, date_arch = ta
                
                prio_class = "prio-low"
                if "Important" in priorite: prio_class = "prio-med"
                elif "urgent" in priorite.lower(): prio_class = "prio-high"
                
                c = st.columns(rep_arch, vertical_alignment="center")
                
                with c[0]: st.markdown(f'<div class="row-marker {prio_class}"></div><div class="pc-only" style="text-align: center; font-weight: bold; opacity:0.8;">{num}</div><div class="mob-only mob-title">🗄️ Archive N° {num}</div>', unsafe_allow_html=True)
                with c[1]: st.markdown(f'<div class="pc-only" style="text-align: center;">{qui}</div><div class="mob-only mob-row"><span class="mob-lbl">👤 Assigné à</span><span class="mob-val">{qui}</span></div>', unsafe_allow_html=True)
                
                with c[2]:
                    st.markdown('<div class="mob-only" style="margin-top: 4px; margin-bottom: -2px;"><span class="mob-lbl">📋 Mission (Détails)</span></div>', unsafe_allow_html=True)
                    limite_caracteres = 26
                    quoi_affiche_arch = quoi if len(quoi) <= limite_caracteres else quoi[:limite_caracteres] + "..."
                    if st.button(quoi_affiche_arch, key=f"mission_btn_arch_{provenance}_{id_arch}", use_container_width=True):
                        st.session_state.modal_mission = (num, qui, quoi)
                        st.rerun()

                with c[3]: st.markdown(f'<div class="pc-only" style="text-align: center;">{priorite}</div><div class="mob-only mob-row"><span class="mob-lbl">🚨 Urgence</span><span class="mob-val">{priorite}</span></div>', unsafe_allow_html=True)
                with c[4]: st.markdown(f'<div class="pc-only" style="text-align: center;">{temps}</div><div class="mob-only mob-row"><span class="mob-lbl">⏱️ Temps</span><span class="mob-val">{temps}</span></div>', unsafe_allow_html=True)
                
                with c[5]: 
                    st.markdown(f'<div class="pc-only" style="text-align: center;"><span class="status-badge status-done">Fait</span></div><div class="mob-only mob-row"><span class="mob-lbl">⚡ Statut</span><span class="status-badge status-done">Fait</span></div>', unsafe_allow_html=True)
                
                with c[6]: st.markdown(f'<div class="pc-only" style="text-align: center; font-style: italic; opacity:0.8;">{date_arch}</div><div class="mob-only mob-row"><span class="mob-lbl">📅 Archivage</span><span class="mob-val">{date_arch}</span></div>', unsafe_allow_html=True)
                
                with c[7]:
                    if st.button("🗑️", key=f"btn_del_arch_{provenance}_{id_arch}", use_container_width=True):
                        if provenance == 'historique': cursor.execute("DELETE FROM planning_archive WHERE id = ?", (id_arch,))
                        else: cursor.execute("DELETE FROM planning WHERE id = ?", (id_arch,))
                        conn.commit()
                        st.rerun()
        else:
            st.info("Les archives de tâches sont vides.")
            
    with onglet_messages:
        st.caption("⚠️ Les messages classiques s'effacent automatiquement après 14 jours. Ceux avec l'épingle 📌 restent indéfiniment.")
        cursor.execute("SELECT id, expediteur, destinataire, texte, date_creation_brute, garder_permanent FROM tchat_archive ORDER BY id DESC")
        messages_archived = cursor.fetchall()
        
        if messages_archived:
            with st.container(height=400):
                for ma in messages_archived:
                    id_msg_arch, exp, dest, txt, date_brute, permanent_arch = ma
                    col_b_msg, col_b_pin, col_b_del = st.columns([8.4, 0.8, 0.8], vertical_alignment="center")
                    
                    with col_b_msg:
                        label_perm_arch = " 📌 [SAUVEGARDÉ INDÉFINIMENT]" if permanent_arch == 1 else ""
                        st.write(f"📢 **[{dest}]** *({date_brute})*{label_perm_arch} **{exp}** : {txt}")
                    
                    if col_b_pin.button("📍" if permanent_arch == 1 else "📌", key=f"pin_arch_{id_msg_arch}", use_container_width=True):
                        cursor.execute("UPDATE tchat_archive SET garder_permanent = ? WHERE id = ?", (0 if permanent_arch == 1 else 1, id_msg_arch))
                        conn.commit()
                        st.rerun()
                        
                    if col_b_del.button("🗑️", key=f"del_arch_msg_{id_msg_arch}", use_container_width=True):
                        cursor.execute("DELETE FROM tchat_archive WHERE id = ?", (id_msg_arch,))
                        conn.commit()
                        st.rerun()
        else:
            st.info("Aucun message archivé.")
