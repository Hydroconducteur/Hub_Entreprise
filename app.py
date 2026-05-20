import streamlit as st
import requests
import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Hub Entreprise", page_icon="📱", layout="wide")

VOTRE_LIEN_ACTUEL = "https://maupu45.streamlit.app"

# --- INJECTION CSS RESPONSIVE & ALIGNEMENT HORIZONTAL PARFAIT ---
st.markdown("""
<style>
.mobile-text { display: none; }
.desktop-text { display: block; }

/* --- ALIGNEMENT DESKTOP GLOBAL ULTRA-PRÉCIS --- */
/* Cible uniquement les lignes de tableaux (Planning & Archives) et les en-têtes */
div[data-testid="stHorizontalBlock"]:has(button[key^="mission_btn_"]),
div[data-testid="stHorizontalBlock"]:has(button[key^="mission_btn_arch_"]),
div[data-testid="stHorizontalBlock"]:has(.header-mark) {
    align-items: center !important;
}

/* Force chaque colonne à se comporter comme un bloc centré verticalement */
div[data-testid="stHorizontalBlock"]:has(button[key^="mission_btn_"]) > div[data-testid="column"],
div[data-testid="stHorizontalBlock"]:has(button[key^="mission_btn_arch_"]) > div[data-testid="column"],
div[data-testid="stHorizontalBlock"]:has(.header-mark) > div[data-testid="column"] {
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    min-height: 40px !important;
}

/* Élimine les décalages de marges internes de Streamlit pour le texte et les boutons */
div[data-testid="stHorizontalBlock"]:has(button[key^="mission_btn_"]) .element-container,
div[data-testid="stHorizontalBlock"]:has(button[key^="mission_btn_arch_"]) .element-container,
div[data-testid="stHorizontalBlock"]:has(.header-mark) .element-container {
    margin: 0 !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

/* Ajustement spécifique des blocs boutons pour qu'ils soient centrés sur l'axe */
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] {
    margin: 0 !important;
    padding: 0 !important;
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
}

/* Annulation des marges de paragraphe pour aligner parfaitement le texte brut */
div[data-testid="stHorizontalBlock"] div[data-testid="stMarkdownContainer"] p {
    margin: 0 !important;
    padding: 0 !important;
    text-align: center !important;
}

/* Style épuré pour le bouton de la mission (style lien cliquable) */
div[data-testid="stHorizontalBlock"] button[key^="mission_btn_"] {
    text-align: left !important;
    justify-content: flex-start !important;
    border: 1px dashed rgba(128, 128, 128, 0.3) !important;
    background-color: transparent !important;
    padding: 6px 10px !important;
    width: 100% !important;
    height: 38px !important;
}

/* Styles spécifiques pour l'affichage Mobile (Smartphones) */
@media (max-width: 768px) {
    .mobile-text { display: block !important; }
    .desktop-text { display: none !important; }
    
    div[data-testid="stHorizontalBlock"]:has(.header-mark) {
        display: none !important;
    }
    
    div[data-testid="stHorizontalBlock"]:has(button[key^="mission_btn_"]) {
        flex-direction: column !important;
        border: 1px solid rgba(128, 128, 128, 0.18) !important;
        border-radius: 16px !important;
        padding: 20px !important;
        margin-bottom: 22px !important;
        background-color: var(--secondary-background-color) !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.05) !important;
        gap: 10px !important;
    }
    
    div[data-testid="stHorizontalBlock"]:has(button[key^="mission_btn_"]) > div[data-testid="column"] {
        display: block !important;
        min-height: auto !important;
        width: 100% !important;
    }
    
    .mobile-field {
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        padding: 8px 0 !important;
        border-bottom: 1px solid rgba(128, 128, 128, 0.08) !important;
        width: 100% !important;
    }
    
    .mobile-label {
        font-size: 0.78em !important;
        text-transform: uppercase !important;
        letter-spacing: 0.8px !important;
        opacity: 0.55 !important;
        font-weight: 600 !important;
    }
    
    .mobile-value {
        font-size: 0.95em !important;
        font-weight: 500 !important;
        text-align: right !important;
    }
    
    .mobile-header {
        padding-bottom: 8px !important;
        border-bottom: 2px solid var(--primary-color) !important;
        margin-bottom: 6px !important;
        width: 100% !important;
    }
    
    .mobile-title {
        font-size: 1.05em !important;
        font-weight: 800 !important;
        color: var(--primary-color) !important;
    }
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

# --- INITIALISATION BASE DE DONNÉES ---
def initialiser_structure_base():
    cursor.execute("CREATE TABLE IF NOT EXISTS planning (id INTEGER PRIMARY KEY AUTOINCREMENT, num_tache TEXT, assigne_a TEXT, intitule TEXT, temps_estime TEXT, date_realisation TEXT, date_creation_brute TEXT, priorite TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS tchat (id INTEGER PRIMARY KEY AUTOINCREMENT, expediteur TEXT, destinataire TEXT, texte TEXT, date_envoi TEXT, date_creation_brute TEXT, garder_permanent INTEGER DEFAULT 0)")
    cursor.execute("CREATE TABLE IF NOT EXISTS utilisateurs (prenom TEXT PRIMARY KEY)")
    cursor.execute("CREATE TABLE IF NOT EXISTS planning_archive (id INTEGER PRIMARY KEY AUTOINCREMENT, num_tache TEXT, assigne_a TEXT, intitule TEXT, temps_estime TEXT, date_realisation TEXT, date_creation_brute TEXT, priorite TEXT, date_archivage TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS tchat_archive (id INTEGER PRIMARY KEY AUTOINCREMENT, expediteur TEXT, destinataire TEXT, texte TEXT, date_envoi TEXT, date_creation_brute TEXT, date_archivage TEXT, garder_permanent INTEGER DEFAULT 0)")
    
    try: cursor.execute("ALTER TABLE planning ADD COLUMN priorite TEXT DEFAULT '🟢 Pas très important'")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE tchat ADD COLUMN garder_permanent INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE tchat_archive ADD COLUMN garder_permanent INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    
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

# --- CONNEXION AUTOMATIQUE VIA URL ---
parametres_url = st.query_params
if st.session_state.user is None and "qui" in parametres_url:
    prenom_detecte = parametres_url["qui"].strip().capitalize()
    if prenom_detecte != "":
        if prenom_detecte == "Christophe":
            st.session_state.user = prenom_detecte
            st.session_state.role = "Administrateur"
        else:
            st.session_state.user = prenom_detecte
            st.session_state.role = "Employé"
        cursor.execute("INSERT OR IGNORE INTO utilisateurs (prenom) VALUES (?)", (st.session_state.user,))
        conn.commit()
        st.rerun()

# --- ÉCRAN DE CONNEXION PRINCIPAL ---
if st.session_state.user is None:
    st.title("📱 Hub Logistique & Entreprise")
    st.subheader("Veuillez vous identifier pour accéder aux outils.")
    
    with st.container(border=True):
        identifiant = st.text_input("Identifiant (Votre Prénom)")
        role_choisi = st.selectbox("Sélectionnez votre rôle", ["Employé", "Administrateur"])
        
        if st.button("Se connecter au Hub 🚀", use_container_width=True):
            prenom_propre = identifiant.strip().capitalize()
            if prenom_propre != "":
                if prenom_propre == "Christophe":
                    st.session_state.user = prenom_propre
                    st.session_state.role = "Administrateur"
                else:
                    if role_choisi == "Administrateur":
                        st.error("❌ Accès Administrateur refusé.")
                        st.session_state.user = prenom_propre
                        st.session_state.role = "Employé"
                    else:
                        st.session_state.user = prenom_propre
                        st.session_state.role = "Employé"
                
                cursor.execute("INSERT OR IGNORE INTO utilisateurs (prenom) VALUES (?)", (prenom_propre,))
                conn.commit()
                st.rerun()
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
        st.title("🛡️ Gestion Système")
        cursor.execute("SELECT prenom FROM utilisateurs WHERE prenom != 'Christophe' ORDER BY prenom ASC")
        membres = cursor.fetchall()
        
        with st.expander("👥 Membres enregistrés", expanded=False):
            if membres:
                for m in membres:
                    nom_membre = m[0]
                    col_m_nom, col_m_del = st.columns([7, 3], vertical_alignment="center")
                    col_m_nom.write(f"• **{nom_membre}**")
                    if col_m_del.button("🗑️", key=f"user_del_{nom_membre}", use_container_width=True):
                        cursor.execute("DELETE FROM utilisateurs WHERE prenom = ?", (nom_membre,))
                        conn.commit()
                        st.rerun()
            else:
                st.caption("Aucun employé connecté.")

        with st.expander("🔗 Liens d'accès direct", expanded=False):
            st.caption("Liens magiques de connexion automatique :")
            base_url = VOTRE_LIEN_ACTUEL

            st.write("Lien **Christophe** :")
            st.code(f"{base_url}/?qui=Christophe", language="text")
            
            for u in membres:
                st.write(f"Lien **{u[0]}** :")
                st.code(f"{base_url}/?qui={u[0]}", language="text")


# ==========================================
# PAGE 1 : LE PLANNING DYNAMIQUE
# ==========================================
if page == "📋 Planning de l'équipe":
    st.title("📋 Planning Global de l'Équipe")
    st.caption("Suivi synchronisé en temps réel. Cliquez sur la mission pour la lire en grand.")

    # FENÊTRE DE FOCUS DE LA MISSION SELECTIONNÉE
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

    st.write("### 📅 Liste des tâches")
    
    @st.fragment(run_every=8)
    def afficher_tableau_taches():
        cursor.execute("SELECT id, num_tache, assigne_a, intitule, temps_estime, date_realisation, priorite FROM planning")
        taches = cursor.fetchall()
        
        if taches:
            if st.session_state.role == "Administrateur":
                rep = [0.6, 1.2, 2.5, 1.8, 0.7, 2.4, 1.4, 0.6]
                cols_h = st.columns(rep, vertical_alignment="center")
            else:
                rep = [0.6, 1.3, 2.8, 1.9, 0.8, 2.6, 1.4]
                cols_h = st.columns(rep, vertical_alignment="center")
            
            with cols_h[0]: st.markdown("<div class='header-mark' style='text-align: center; font-weight: bold;'>N°</div>", unsafe_allow_html=True)
            with cols_h[1]: st.markdown("<div style='text-align: center; font-weight: bold;'>Assigné à</div>", unsafe_allow_html=True)
            with cols_h[2]: st.markdown("<div style='text-align: center; font-weight: bold;'>Mission (cliquable)</div>", unsafe_allow_html=True)
            with cols_h[3]: st.markdown("<div style='text-align: center; font-weight: bold;'>Urgence</div>", unsafe_allow_html=True)
            with cols_h[4]: st.markdown("<div style='text-align: center; font-weight: bold;'>Temps</div>", unsafe_allow_html=True)
            with cols_h[5]: st.markdown("<div style='text-align: center; font-weight: bold;'>Statut</div>", unsafe_allow_html=True)
            with cols_h[6]: st.markdown("<div style='text-align: center; font-weight: bold;'>Action</div>", unsafe_allow_html=True)
            if st.session_state.role == "Administrateur": 
                with cols_h[7]: st.markdown("<div style='text-align: center; font-weight: bold;'>Suppr.</div>", unsafe_allow_html=True)
                
            st.markdown('<hr class="desktop-text" style="margin: 10px 0; border-color: #cbd5e1;">', unsafe_allow_html=True)

            for t in taches:
                id_t, num, qui, quoi, temps, statut, priorite = t
                if not priorite: priorite = "🟢 Pas très important"
                
                cols = st.columns(rep, vertical_alignment="center")
                
                with cols[0]:
                    st.markdown(f'<div class="desktop-text"><b>{num}</b></div><div class="mobile-text mobile-header"><span class="mobile-title">🔢 Tâche N° {num}</span></div>', unsafe_allow_html=True)
                
                with cols[1]:
                    st.markdown(f'<div class="desktop-text">{qui}</div><div class="mobile-text mobile-field"><span class="mobile-label">👤 Assigné à</span><span class="mobile-value">{qui}</span></div>', unsafe_allow_html=True)
                
                # Système de troncation
                limite_caracteres = 28
                quoi_affiche = quoi if len(quoi) <= limite_caracteres else quoi[:limite_caracteres] + "..."
                
                with cols[2]:
                    st.markdown('<div class="mobile-text" style="margin-top: 4px;"><span class="mobile-label">📋 Mission (cliquer pour agrandir)</span></div>', unsafe_allow_html=True)
                    if st.button(quoi_affiche, key=f"mission_btn_{id_t}", use_container_width=True, help="Cliquez pour lire la description complète"):
                        st.session_state.modal_mission = (num, qui, quoi)
                        st.rerun()

                with cols[3]:
                    st.markdown(f'<div class="desktop-text">{priorite}</div><div class="mobile-text mobile-field"><span class="mobile-label">🚨 Urgence</span><span class="mobile-value">{priorite}</span></div>', unsafe_allow_html=True)
                
                with cols[4]:
                    st.markdown(f'<div class="desktop-text">{temps}</div><div class="mobile-text mobile-field"><span class="mobile-label">⏱️ Temps</span><span class="mobile-value">{temps}</span></div>', unsafe_allow_html=True)
                
                with cols[5]:
                    color = "#eab308" if "En cours" in statut else "#22c55e"
                    emoji = "🟡" if "En cours" in statut else "🟢"
                    st.markdown(f"""
                    <div class="desktop-text" style="font-weight: bold; color: {color}; text-align: center;">{emoji} {statut}</div>
                    <div class="mobile-text mobile-field" style="border-bottom: none !important;">
                        <span class="mobile-label">⚡ Statut</span>
                        <span class="mobile-value" style="color: {color}; font-weight: bold;">{emoji} {statut}</span>
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
                            st.markdown("<div class='desktop-text' style='color: gray; text-align: center;'>—</div>", unsafe_allow_html=True)
                    else:
                        if st.session_state.user == qui or st.session_state.role == "Administrateur":
                            if st.button("Annuler ↩️", key=f"btn_annuler_{id_t}", use_container_width=True):
                                cursor.execute("UPDATE planning SET date_realisation = 'En cours ⏳' WHERE id = ?", (id_t,))
                                conn.commit()
                                st.rerun()
                        else:
                            st.markdown("<div class='desktop-text' style='color: gray; text-align: center;'>—</div>", unsafe_allow_html=True)
                
                if st.session_state.role == "Administrateur":
                    with cols[7]:
                        if st.button("🗑️", key=f"btn_del_tache_{id_t}", use_container_width=True):
                            cursor.execute("DELETE FROM planning WHERE id = ?", (id_t,))
                            conn.commit()
                            st.rerun()
                        
                st.markdown('<hr class="desktop-text" style="margin: 10px 0; border-color: #f1f5f9;">', unsafe_allow_html=True)
        else:
            st.info("Aucune tâche planifiée.")

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
# 🗄️ PAGE 3 : ARCHIVES
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
            SELECT 'recents' AS provenance, id, num_tache, assigne_a, intitule, temps_estime, date_realisation, priorite, 'En attente de transfert' AS date_archivage 
            FROM planning 
            WHERE date_realisation LIKE 'Fait le %'
            ORDER BY date_archivage DESC
        """)
        taches_archived = cursor.fetchall()
        
        if taches_archived:
            rep_arch = [0.6, 1.2, 2.5, 1.5, 0.8, 2.0, 1.4, 0.8]
            cols_h = st.columns(rep_arch, vertical_alignment="center")
            
            with cols_h[0]: st.markdown("<div class='header-mark' style='text-align: center; font-weight: bold;'>N°</div>", unsafe_allow_html=True)
            with cols_h[1]: st.markdown("<div style='text-align: center; font-weight: bold;'>Assigné à</div>", unsafe_allow_html=True)
            with cols_h[2]: st.markdown("<div style='text-align: center; font-weight: bold;'>Mission (cliquable)</div>", unsafe_allow_html=True)
            with cols_h[3]: st.markdown("<div style='text-align: center; font-weight: bold;'>Urgence</div>", unsafe_allow_html=True)
            with cols_h[4]: st.markdown("<div style='text-align: center; font-weight: bold;'>Temps</div>", unsafe_allow_html=True)
            with cols_h[5]: st.markdown("<div style='text-align: center; font-weight: bold;'>Statut</div>", unsafe_allow_html=True)
            with cols_h[6]: st.markdown("<div style='text-align: center; font-weight: bold;'>Archivé le</div>", unsafe_allow_html=True)
            with cols_h[7]: st.markdown("<div style='text-align: center; font-weight: bold;'>Suppr.</div>", unsafe_allow_html=True)
            
            st.markdown('<hr style="margin: 10px 0; border-color: #cbd5e1;">', unsafe_allow_html=True)
            
            for ta in taches_archived:
                provenance, id_arch, num, qui, quoi, temps, statut, priorite, date_arch = ta
                c = st.columns(rep_arch, vertical_alignment="center")
                
                with c[0]: st.markdown(f'<div><b>{num}</b></div>', unsafe_allow_html=True)
                with c[1]: st.markdown(f'<div>{qui}</div>', unsafe_allow_html=True)
                
                with c[2]:
                    limite_caracteres = 25
                    quoi_affiche_arch = quoi if len(quoi) <= limite_caracteres else quoi[:limite_caracteres] + "..."
                    if st.button(quoi_affiche_arch, key=f"mission_btn_arch_{provenance}_{id_arch}", use_container_width=True):
                        st.session_state.modal_mission = (num, qui, quoi)
                        st.rerun()

                with c[3]: st.markdown(f'<div>{priorite}</div>', unsafe_allow_html=True)
                with c[4]: st.markdown(f'<div>{temps}</div>', unsafe_allow_html=True)
                with c[5]: st.markdown(f'<div style="font-weight: bold; text-align: center;">{statut}</div>', unsafe_allow_html=True)
                with c[6]: st.markdown(f'<div><i>{date_arch}</i></div>', unsafe_allow_html=True)
                
                with c[7]:
                    if st.button("🗑️", key=f"btn_del_arch_{provenance}_{id_arch}", use_container_width=True):
                        if provenance == 'historique': cursor.execute("DELETE FROM planning_archive WHERE id = ?", (id_arch,))
                        else: cursor.execute("DELETE FROM planning WHERE id = ?", (id_arch,))
                        conn.commit()
                        st.rerun()
                    
                st.markdown('<hr style="margin: 10px 0; border-color: #f1f5f9;">', unsafe_allow_html=True)
        else:
            st.info("Archives de tâches vides.")
            
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
