import streamlit as st
import requests
import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Configuration de la page
st.set_page_config(page_title="Hub Entreprise Pro", page_icon="📱", layout="wide")

VOTRE_LIEN_ACTUEL = st.secrets["APP_URL"]

# CSS PC/Téléphone
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

/* 1. Le Bouton d'Action Principal (Fait / Annuler) */
div[data-testid="stHorizontalBlock"]:has(.row-marker) div[data-testid="column"] button:has(div:contains("Fait")),
div[data-testid="stHorizontalBlock"]:has(.row-marker) div[data-testid="column"] button:has(div:contains("Annuler")) {
    background: linear-gradient(135deg, #3b82f6, #1d4ed8) !important;
    color: white !important;
    border: none !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    padding: 6px 14px !important;
    border-radius: 6px !important;
    box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2) !important;
    transition: all 0.2s ease !important;
}
div[data-testid="stHorizontalBlock"]:has(.row-marker) div[data-testid="column"] button:has(div:contains("Fait")):hover,
div[data-testid="stHorizontalBlock"]:has(.row-marker) div[data-testid="column"] button:has(div:contains("Annuler")):hover {
    background: linear-gradient(135deg, #2563eb, #1e40af) !important;
    box-shadow: 0 4px 8px rgba(37, 99, 235, 0.3) !important;
    transform: translateY(-1px) !important;
}

/* 2. Le Bouton Supprimer (Poubelle) */
div[data-testid="stHorizontalBlock"]:has(.row-marker) div[data-testid="column"] button:has(div:contains("🗑️")) {
    background: transparent !important;
    color: #94a3b8 !important;
    border: 1px solid rgba(148, 163, 184, 0.15) !important;
    border-radius: 6px !important;
    font-size: 0.9rem !important;
    padding: 5px !important;
    transition: all 0.2s ease !important;
}
div[data-testid="stHorizontalBlock"]:has(.row-marker) div[data-testid="column"] button:has(div:contains("🗑️")):hover {
    background: rgba(239, 68, 68, 0.1) !important;
    color: #ef4444 !important;
    border-color: rgba(239, 68, 68, 0.4) !important;
}

/* --- 💻 GRILLE DE DONNÉES DESKTOP (PC) --- */
@media (min-width: 769px) {
    /* En-tête du tableau modernisé et élargi */
    div[data-testid="stHorizontalBlock"]:has(.header-mark) {
        background: rgba(30, 41, 59, 0.4) !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
        margin-bottom: 14px !important;
        border-bottom: 2px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    /* Supprime les décalages et marges internes de Streamlit sous l'en-tête */
    div[data-testid="stHorizontalBlock"]:has(.header-mark) [data-testid="element-container"] {
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Formatage et alignement parfait au centre des écritots */
    div[data-testid="stHorizontalBlock"]:has(.header-mark) div[data-testid="stMarkdownContainer"] p {
        color: #94a3b8 !important;
        font-weight: 600 !important;
        font-size: 0.8rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.8px !important;
        text-align: center !important;
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1.2 !important;
    }

    /* Lignes du tableau (Cartes horizontales épurées) */
    div[data-testid="stHorizontalBlock"]:has(.row-marker) {
        background: #1e293b !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 8px !important;
        padding: 10px 16px !important;
        margin-bottom: 8px !important;
        align-items: center !important;
        transition: all 0.2s ease !important;
        position: relative;
    }
    
    div[data-testid="stHorizontalBlock"]:has(.row-marker):hover {
        border-color: rgba(255, 255, 255, 0.15) !important;
        background: #243146 !important;
        transform: translateX(2px);
    }

    /* Bordures colorées de priorité discrètes et élégantes */
    div[data-testid="stHorizontalBlock"]:has(.urg-4) { border-left: 4px solid #dc2626 !important; }
    div[data-testid="stHorizontalBlock"]:has(.urg-3) { border-left: 4px solid #ea580c !important; }
    div[data-testid="stHorizontalBlock"]:has(.urg-2) { border-left: 4px solid #f97316 !important; }
    div[data-testid="stHorizontalBlock"]:has(.urg-1) { border-left: 4px solid #eab308 !important; }

    div[data-testid="stHorizontalBlock"] [data-testid="element-container"] {
        margin-bottom: 0 !important;
        margin-top: 0 !important;
    }

    /* Style du bouton Mission cliquable et Popovers */
    div[data-testid="stHorizontalBlock"]:has(.row-marker) div[data-testid="column"]:nth-of-type(3) button,
    div[data-testid="stHorizontalBlock"]:has(.row-marker) div[data-testid="column"]:nth-of-type(7) button {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        color: #f8fafc !important;
        text-align: left !important;
        padding: 6px 12px !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        border-radius: 6px !important;
        width: 100% !important;
        justify-content: flex-start !important;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    div[data-testid="stHorizontalBlock"]:has(.row-marker) div[data-testid="column"]:nth-of-type(3) button:hover,
    div[data-testid="stHorizontalBlock"]:has(.row-marker) div[data-testid="column"]:nth-of-type(7) button:hover {
        background: rgba(255, 255, 255, 0.08) !important;
        border-color: rgba(37, 99, 235, 0.4) !important;
        color: #3b82f6 !important;
    }
}

/* Boutton Urgence */
.urgency-container {
    display: flex;
    gap: 4px;
    align-items: center;
    justify-content: center;
}
.urg-box {
    width: 14px;
    height: 14px;
    border-radius: 3px;
    background-color: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.1);
}
.urg-1 .b1 { background-color: #eab308; border-color: #eab308; box-shadow: 0 0 5px rgba(234, 179, 8, 0.4); }
.urg-2 .b1, .urg-2 .b2 { background-color: #f97316; border-color: #f97316; box-shadow: 0 0 5px rgba(249, 115, 22, 0.4); }
.urg-3 .b1, .urg-3 .b2, .urg-3 .b3 { background-color: #ea580c; border-color: #ea580c; box-shadow: 0 0 5px rgba(234, 88, 12, 0.4); }
.urg-4 .b1, .urg-4 .b2, .urg-4 .b3, .urg-4 .b4 { background-color: #dc2626; border-color: #dc2626; box-shadow: 0 0 5px rgba(220, 38, 38, 0.4); }

/* 📱 CSS Mobile */
@media (max-width: 768px) {
    .mob-only { display: block !important; }
    .pc-only { display: none !important; }
    
    div[data-testid="stHorizontalBlock"]:has(.header-mark) { display: none !important; }
    
    div[data-testid="stHorizontalBlock"]:has(.row-marker) {
        background: #1e293b !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        padding: 14px !important;
        margin-bottom: 12px !important;
        display: flex !important;
        flex-direction: column !important;
    }
    
    div[data-testid="stHorizontalBlock"]:has(.urg-4) { border-left: 5px solid #dc2626 !important; }
    div[data-testid="stHorizontalBlock"]:has(.urg-3) { border-left: 5px solid #ea580c !important; }
    div[data-testid="stHorizontalBlock"]:has(.urg-2) { border-left: 5px solid #f97316 !important; }
    div[data-testid="stHorizontalBlock"]:has(.urg-1) { border-left: 5px solid #eab308 !important; }

    div[data-testid="stHorizontalBlock"]:has(.row-marker) > div[data-testid="column"] {
        width: 100% !important;
        display: block !important;
        margin: 0 !important;
    }
    
    .mob-title {
        font-size: 1rem !important;
        font-weight: 700 !important;
        color: #f8fafc !important;
        padding-bottom: 6px !important;
        margin-bottom: 10px !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
    
    .mob-row {
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        padding: 6px 0 !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.04) !important;
    }
    .mob-row:last-of-type { border-bottom: none !important; }
    
    .mob-lbl {
        font-size: 0.72rem !important;
        color: #64748b !important;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .mob-val {
        font-size: 0.88rem !important;
        color: #e2e8f0 !important;
        font-weight: 600;
    }

    div[data-testid="stHorizontalBlock"]:has(.row-marker) div[data-testid="column"]:nth-of-type(3) button,
    div[data-testid="stHorizontalBlock"]:has(.row-marker) div[data-testid="column"]:nth-of-type(7) button {
        width: 100% !important;
        text-align: left !important;
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        padding: 8px 12px !important;
        border-radius: 6px !important;
        margin-top: 4px !important;
        color: #f8fafc !important;
    }

    div[data-testid="stHorizontalBlock"]:has(.row-marker) button {
        width: 100% !important;
        border-radius: 6px !important;
        padding: 8px !important;
        font-weight: 600 !important;
        margin-top: 6px !important;
    }
}

.status-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.78rem;
    font-weight: 600;
    text-align: center;
    min-width: 90px;
}
.status-pending {
    background: rgba(245, 158, 11, 0.1) !important;
    color: #fbbf24 !important;
    border: 1px solid rgba(245, 158, 11, 0.2);
}
.status-done {
    background: rgba(16, 185, 129, 0.1) !important;
    color: #34d399 !important;
    border: 1px solid rgba(16, 185, 129, 0.2);
}

.prio-badge {
    font-size: 0.82rem;
    font-weight: 500;
    color: #e2e8f0;
}
</style>
""", unsafe_allow_html=True)


# Connexion a la base de donnée Turso HTTP
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

# Innitialisation de la base de donnée mise a jour
def initialiser_structure_base():
    cursor.execute("CREATE TABLE IF NOT EXISTS planning (id INTEGER PRIMARY KEY AUTOINCREMENT, num_tache TEXT, assigne_a TEXT, intitule TEXT, temps_estime TEXT, date_realisation TEXT, date_creation_brute TEXT, priorite TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS tchat (id INTEGER PRIMARY KEY AUTOINCREMENT, expediteur TEXT, destinataire TEXT, texte TEXT, date_envoi TEXT, date_creation_brute TEXT, garder_permanent INTEGER DEFAULT 0)")
    cursor.execute("CREATE TABLE IF NOT EXISTS utilisateurs (prenom TEXT PRIMARY KEY, code_secret TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS planning_archive (id INTEGER PRIMARY KEY AUTOINCREMENT, num_tache TEXT, assigne_a TEXT, intitule TEXT, temps_estime TEXT, date_realisation TEXT, date_creation_brute TEXT, priorite TEXT, date_archivage TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS tchat_archive (id INTEGER PRIMARY KEY AUTOINCREMENT, expediteur TEXT, destinataire TEXT, texte TEXT, date_envoi TEXT, date_creation_brute TEXT, date_archivage TEXT, garder_permanent INTEGER DEFAULT 0)")
    
    try: cursor.execute("ALTER TABLE planning ADD COLUMN priorite TEXT DEFAULT '🟢 Pas très important'")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE planning ADD COLUMN commentaire TEXT DEFAULT ''")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE tchat ADD COLUMN garder_permanent INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE tchat_archive ADD COLUMN garder_permanent INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE utilisateurs ADD COLUMN code_secret TEXT DEFAULT '1234'")
    except sqlite3.OperationalError: pass
    
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


# Algorithme de nettoyage automatique + archivage
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

# Gestion des sessions
if "user" not in st.session_state: st.session_state.user = None
if "role" not in st.session_state: st.session_state.role = None
if "navigation_page" not in st.session_state: st.session_state.navigation_page = "📋 Planning de l'équipe"
if "modal_mission" not in st.session_state: st.session_state.modal_mission = None

# Connexion automatique via URL
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

# Écran de connexion principale
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

# Barre lattéral
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
        
        with st.expander("👥 Liste Blanche & Codes", expanded=False):
            with st.form("form_ajouter_employe", clear_on_submit=True):
                st.caption("Ajouter un nouvel employé autorisé :")
                nv_nom = st.text_input("Prénom").strip().capitalize()
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


# Page 1 Planning Dynamique
if page == "📋 Planning de l'équipe":
    st.title("📋 Planning Global de l'Équipe")
    st.caption("Suivi en temps réel. Cliquez sur le bloc d'une mission pour l'ouvrir en grand.")

    if st.session_state.modal_mission:
        date_m, qui_m, quoi_m = st.session_state.modal_mission
        with st.container(border=True):
            st.markdown(f"### 🔍 Détails de la Mission — Créée le {date_m}")
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
            
            with st.form("form_tache", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    qui = st.selectbox("Assigné à", liste_employes) if liste_employes else st.text_input("Assigné à")
                    priorite_choisie = st.selectbox("Urgence", ["1 - Faible 🟢", "2 - Moyen 🟡", "3 - Important 🟠", "4 - Critique 🔴"])
                with col2:
                    temps = st.text_input("Temps estimé (ex: 2h30)")
                    action = st.text_area("Description du travail")
                
                if st.form_submit_button("Ajouter au planning"):
                    if qui and action:
                        now_paris = datetime.now(ZoneInfo("Europe/Paris"))
                        now_brute = now_paris.strftime("%Y-%m-%d %H:%M:%S")
                        
                        cursor.execute("INSERT INTO planning (num_tache, assigne_a, intitule, temps_estime, date_realisation, date_creation_brute, priorite, commentaire) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", ("", qui, action, temps, "En cours ⏳", now_brute, priorite_choisie, ""))
                        conn.commit()
                        st.rerun()

    st.write("### 📅 Tâches actives")
    
    col_f1, col_f2 = st.columns([1, 2])
    with col_f1:
        filtre_statut = st.selectbox("📌 Filtrer l'affichage :", ["Toutes les tâches", "⏳ En cours uniquement", "✅ Terminées uniquement"])

    @st.fragment(run_every=8)
    def afficher_tableau_taches(filtre):
        query = "SELECT id, date_creation_brute, assigne_a, intitule, temps_estime, date_realisation, priorite, commentaire FROM planning"
        
        if filtre == "⏳ En cours uniquement": query += " WHERE date_realisation LIKE '%En cours%'"
        elif filtre == "✅ Terminées uniquement": query += " WHERE date_realisation NOT LIKE '%En cours%'"
        
        query += " ORDER BY date_creation_brute DESC"
        
        cursor.execute(query)
        taches = cursor.fetchall()
        
        if taches:
            if st.session_state.role == "Administrateur":
                rep = [1.0, 1.2, 2.5, 1.4, 0.8, 1.3, 1.3, 1.2, 0.6]
                cols_h = st.columns(rep, vertical_alignment="center")
            else:
                rep = [1.0, 1.2, 2.7, 1.4, 0.8, 1.4, 1.4, 1.2]
                cols_h = st.columns(rep, vertical_alignment="center")
            
            with cols_h[0]: st.markdown("<p><span class='header-mark'></span>DATE</p>", unsafe_allow_html=True)
            with cols_h[1]: st.markdown("<p>Assigné à</p>", unsafe_allow_html=True)
            with cols_h[2]: st.markdown("<p>Mission (Cliquer)</p>", unsafe_allow_html=True)
            with cols_h[3]: st.markdown("<p>Urgence</p>", unsafe_allow_html=True)
            with cols_h[4]: st.markdown("<p>Temps</p>", unsafe_allow_html=True)
            with cols_h[5]: st.markdown("<p>Statut</p>", unsafe_allow_html=True)
            with cols_h[6]: st.markdown("<p>Commentaire</p>", unsafe_allow_html=True)
            with cols_h[7]: st.markdown("<p>Action</p>", unsafe_allow_html=True)
            if st.session_state.role == "Administrateur": 
                with cols_h[8]: st.markdown("<p>Suppr.</p>", unsafe_allow_html=True)

            for t in taches:
                id_t, date_b, qui, quoi, temps, statut, priorite, commentaire = t
                if not priorite: priorite = "1 - Faible 🟢"
                if commentaire is None: commentaire = ""
                
                if date_b:
                    try:
                        date_aff = datetime.strptime(date_b, "%Y-%m-%d %H:%M:%S").strftime("%d/%m à %H:%M")
                    except:
                        date_aff = date_b
                else:
                    date_aff = "Inconnue"
                
                urg_class = "urg-1"
                if "2" in priorite or "Moyen" in priorite: urg_class = "urg-2"
                elif "3" in priorite or "Important" in priorite: urg_class = "urg-3"
                elif "4" in priorite or "Critique" in priorite or "Très urgent" in priorite: urg_class = "urg-4"
                elif "urgent" in priorite.lower(): urg_class = "urg-4"
                
                cols = st.columns(rep, vertical_alignment="center")
                
                with cols[0]:
                    st.markdown(f'<div class="row-marker {urg_class}"></div><div class="pc-only" style="text-align: center; font-weight: 700; color: #94a3b8; font-size: 0.8rem;">{date_aff}</div><div class="mob-only mob-title">📅 Date: {date_aff}</div>', unsafe_allow_html=True)
                
                with cols[1]:
                    st.markdown(f'<div class="pc-only" style="text-align: center; font-weight: 600; color: #e2e8f0;">{qui}</div><div class="mob-only mob-row"><span class="mob-lbl">👤 Assigné à</span><span class="mob-val">{qui}</span></div>', unsafe_allow_html=True)
                
                with cols[2]:
                    st.markdown('<div class="mob-only" style="margin-top: 4px; margin-bottom: -2px;"><span class="mob-lbl">📋 Mission (Ouvrir)</span></div>', unsafe_allow_html=True)
                    limite_caracteres = 30
                    quoi_affiche = quoi if len(quoi) <= limite_caracteres else quoi[:limite_caracteres] + "..."
                    if st.button(quoi_affiche, key=f"mission_btn_{id_t}", use_container_width=True):
                        st.session_state.modal_mission = (date_aff, qui, quoi)
                        st.rerun()

                with cols[3]:
                    urgency_html = f'''
                    <div class="urgency-container {urg_class}" title="{priorite}">
                        <div class="urg-box b1"></div>
                        <div class="urg-box b2"></div>
                        <div class="urg-box b3"></div>
                        <div class="urg-box b4"></div>
                    </div>
                    '''
                    st.markdown(f'''
                    <div class="pc-only">{urgency_html}</div>
                    <div class="mob-only mob-row">
                        <span class="mob-lbl">🚨 Urgence</span>
                        <span class="mob-val" style="display:flex; justify-content:flex-end;">{urgency_html}</span>
                    </div>
                    ''', unsafe_allow_html=True)
                
                with cols[4]:
                    st.markdown(f'<div class="pc-only" style="text-align: center; font-weight: 500; color: #cbd5e1;">{temps}</div><div class="mob-only mob-row"><span class="mob-lbl">⏱️ Temps</span><span class="mob-val">{temps}</span></div>', unsafe_allow_html=True)
                
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
                    st.markdown('<div class="mob-only" style="margin-top: 4px; margin-bottom: -2px;"><span class="mob-lbl">💬 Commentaire</span></div>', unsafe_allow_html=True)
                    label_comm = f"💬 {commentaire[:10]}..." if commentaire else "📝 Ajouter"
                    with st.popover(label_comm, use_container_width=True):
                        nouveau_comm = st.text_area("Remarque / Difficulté :", value=commentaire, key=f"comm_area_{id_t}")
                        if st.button("Enregistrer", key=f"save_comm_{id_t}"):
                            cursor.execute("UPDATE planning SET commentaire = ? WHERE id = ?", (nouveau_comm, id_t))
                            conn.commit()
                            st.rerun()
                    
                with cols[7]:
                    if "En cours" in statut:
                        if st.session_state.user == qui or st.session_state.role == "Administrateur":
                            if st.button("Fait ✅", key=f"btn_fait_{id_t}", use_container_width=True):
                                maintenant = datetime.now(ZoneInfo("Europe/Paris")).strftime("%d/%m/%Y à %H:%M")
                                cursor.execute("UPDATE planning SET date_realisation = ? WHERE id = ?", (f"Fait le {maintenant}", id_t))
                                conn.commit()
                                st.rerun()
                        else:
                            st.markdown("<div class='pc-only' style='color: #475569; text-align: center; opacity:0.5;'>—</div>", unsafe_allow_html=True)
                    else:
                        if st.session_state.user == qui or st.session_state.role == "Administrateur":
                            if st.button("Annuler ↩️", key=f"btn_annuler_{id_t}", use_container_width=True):
                                cursor.execute("UPDATE planning SET date_realisation = 'En cours ⏳' WHERE id = ?", (id_t,))
                                conn.commit()
                                st.rerun()
                        else:
                            st.markdown("<div class='pc-only' style='color: #475569; text-align: center; opacity:0.5;'>—</div>", unsafe_allow_html=True)
                
                if st.session_state.role == "Administrateur":
                    with cols[8]:
                        if st.button("🗑️", key=f"btn_del_tache_{id_t}", use_container_width=True):
                            cursor.execute("DELETE FROM planning WHERE id = ?", (id_t,))
                            conn.commit()
                            st.rerun()
        else:
            st.info("Aucune tâche ne correspond à ce filtre.")

    afficher_tableau_taches(filtre_statut)


# Page 2 Tchat de groupe et Tchat privé
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


# Page 3 Archives
elif page == "🗄️ Archives (6 mois)" and st.session_state.role == "Administrateur":
    st.title("🗄️ Archives Administrateur")
    
    if st.session_state.modal_mission:
        date_m, qui_m, quoi_m = st.session_state.modal_mission
        with st.container(border=True):
            st.markdown(f"### 🔍 Détails de la Mission Archivée — Créée le {date_m}")
            st.markdown(f"👤 **Assigné à :** {qui_m}")
            st.info(quoi_m)
            if st.button("Fermer la description ❌", use_container_width=True):
                st.session_state.modal_mission = None
                st.rerun()
        st.write("---")

    onglet_taches, = st.tabs(["📋 Archives Tâches"])
    
    with onglet_taches:
        cursor.execute("""
            SELECT 'historique' AS provenance, id, date_creation_brute, assigne_a, intitule, temps_estime, date_realisation, priorite, date_archivage 
            FROM planning_archive
            UNION ALL
            SELECT 'recents' AS provenance, id, date_creation_brute, assigne_a, intitule, temps_estime, date_realisation, priorite, 'En attente' AS date_archivage 
            FROM planning 
            WHERE date_realisation LIKE 'Fait le %'
            ORDER BY date_archivage DESC
        """)
        taches_archived = cursor.fetchall()
        
        if taches_archived:
            rep_arch = [1.0, 1.2, 3.2, 1.5, 0.8, 1.8, 1.4, 0.6]
            cols_h = st.columns(rep_arch, vertical_alignment="center")
            
            with cols_h[0]: st.markdown("<p><span class='header-mark'></span>DATE</p>", unsafe_allow_html=True)
            with cols_h[1]: st.markdown("<p>Assigné à</p>", unsafe_allow_html=True)
            with cols_h[2]: st.markdown("<p>Mission</p>", unsafe_allow_html=True)
            with cols_h[3]: st.markdown("<p>Urgence</p>", unsafe_allow_html=True)
            with cols_h[4]: st.markdown("<p>Temps</p>", unsafe_allow_html=True)
            with cols_h[5]: st.markdown("<p>Statut</p>", unsafe_allow_html=True)
            with cols_h[6]: st.markdown("<p>Archivé le</p>", unsafe_allow_html=True)
            with cols_h[7]: st.markdown("<p>Suppr.</p>", unsafe_allow_html=True)
            
            for ta in taches_archived:
                provenance, id_arch, date_b, qui, quoi, temps, statut, priorite, date_arch = ta
                
                if date_b:
                    try:
                        date_aff = datetime.strptime(date_b, "%Y-%m-%d %H:%M:%S").strftime("%d/%m à %H:%M")
                    except:
                        date_aff = date_b
                else:
                    date_aff = "Inconnue"
                
                urg_class = "urg-1"
                if priorite:
                    if "2" in priorite or "Moyen" in priorite: urg_class = "urg-2"
                    elif "3" in priorite or "Important" in priorite: urg_class = "urg-3"
                    elif "4" in priorite or "Critique" in priorite or "Très urgent" in priorite: urg_class = "urg-4"
                    elif "urgent" in priorite.lower(): urg_class = "urg-4"
                
                c = st.columns(rep_arch, vertical_alignment="center")
                
                with c[0]: st.markdown(f'<div class="row-marker {urg_class}"></div><div class="pc-only" style="text-align: center; font-weight: bold; color: #94a3b8; font-size:0.8rem;">{date_aff}</div><div class="mob-only mob-title">🗄️ Archive Date : {date_aff}</div>', unsafe_allow_html=True)
                with c[1]: st.markdown(f'<div class="pc-only" style="text-align: center; color: #e2e8f0;">{qui}</div><div class="mob-only mob-row"><span class="mob-lbl">👤 Assigné à</span><span class="mob-val">{qui}</span></div>', unsafe_allow_html=True)
                
                with c[2]:
                    st.markdown('<div class="mob-only" style="margin-top: 4px; margin-bottom: -2px;"><span class="mob-lbl">📋 Mission (Détails)</span></div>', unsafe_allow_html=True)
                    limite_caracteres = 30
                    quoi_affiche_arch = quoi if len(quoi) <= limite_caracteres else quoi[:limite_caracteres] + "..."
                    if st.button(quoi_affiche_arch, key=f"mission_btn_arch_{provenance}_{id_arch}", use_container_width=True):
                        st.session_state.modal_mission = (date_aff, qui, quoi)
                        st.rerun()

                with c[3]:
                    urgency_html = f'''
                    <div class="urgency-container {urg_class}" title="{priorite}">
                        <div class="urg-box b1"></div>
                        <div class="urg-box b2"></div>
                        <div class="urg-box b3"></div>
                        <div class="urg-box b4"></div>
                    </div>
                    '''
                    st.markdown(f'''
                    <div class="pc-only">{urgency_html}</div>
                    <div class="mob-only mob-row">
                        <span class="mob-lbl">🚨 Urgence</span>
                        <span class="mob-val" style="display:flex; justify-content:flex-end;">{urgency_html}</span>
                    </div>
                    ''', unsafe_allow_html=True)
                
                with c[4]: st.markdown(f'<div class="pc-only" style="text-align: center; color: #cbd5e1;">{temps}</div><div class="mob-only mob-row"><span class="mob-lbl">⏱️ Temps</span><span class="mob-val">{temps}</span></div>', unsafe_allow_html=True)
                
                with c[5]: 
                    st.markdown(f'<div class="pc-only" style="text-align: center;"><span class="status-badge status-done">Archivé</span></div><div class="mob-only mob-row"><span class="mob-lbl">⚡ Statut</span><span class="status-badge status-done">Archivé</span></div>', unsafe_allow_html=True)
                
                with c[6]: st.markdown(f'<div class="pc-only" style="text-align: center; font-style: italic; color: #64748b; font-size: 0.82rem;">{date_arch}</div><div class="mob-only mob-row"><span class="mob-lbl">📅 Archivage</span><span class="mob-val">{date_arch}</span></div>', unsafe_allow_html=True)
                
                with c[7]:
                    if st.button("🗑️", key=f"btn_del_arch_{provenance}_{id_arch}", use_container_width=True):
                        if provenance == 'historique': cursor.execute("DELETE FROM planning_archive WHERE id = ?", (id_arch,))
                        else: cursor.execute("DELETE FROM planning WHERE id = ?", (id_arch,))
                        conn.commit()
                        st.rerun()
        else:
            st.info("Les archives de tâches sont vides.")
