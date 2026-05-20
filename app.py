import streamlit as st
import requests
import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Hub Entreprise", page_icon="📱", layout="wide")

VOTRE_LIEN_ACTUEL = "https://maupu45.streamlit.app"

# --- INJECTION CSS RESPONSIVE & ALIGNEMENT ---
st.markdown("""
<style>
.mobile-text { display: none; }
.desktop-text { display: block; }

/* FIX ALIGNEMENT VERTICAL BOUTONS VS TEXTE */
.align-center-fix {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    min-height: 42px !important; /* Hauteur standard d'un bouton Streamlit */
    margin-bottom: 0 !important;
}

.align-center-fix p {
    margin-bottom: 0 !important;
}

@media (max-width: 768px) {
    .mobile-text { display: block !important; }
    .desktop-text { display: none !important; }
    
    div[data-testid="stHorizontalBlock"]:has(.header-mark) {
        display: none !important;
    }
    
    div[data-testid="stHorizontalBlock"]:has(.task-row-mark) {
        flex-direction: column !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        padding: 16px !important;
        margin-bottom: 14px !important;
        background-color: #ffffff !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
        gap: 8px !important;
    }
    
    div[data-testid="stHorizontalBlock"]:has(.task-row-mark) + div hr {
        display: none !important;
    }
    
    .stChatMessage {
        padding: 10px !important;
        margin-bottom: 8px !important;
    }
    
    .align-center-fix {
        min-height: auto !important;
        justify-content: flex-start !important;
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

# --- INITIALISATION OPTIMISÉE ---
def initialiser_structure_base():
    cursor.execute("CREATE TABLE IF NOT EXISTS planning (id INTEGER PRIMARY KEY AUTOINCREMENT, num_tache TEXT, assigne_a TEXT, intitule TEXT, temps_estime TEXT, date_realisation TEXT, date_creation_brute TEXT, priorite TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS tchat (id INTEGER PRIMARY KEY AUTOINCREMENT, expediteur TEXT, destinataire TEXT, texte TEXT, date_envoi TEXT, date_creation_brute TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS utilisateurs (prenom TEXT PRIMARY KEY)")
    cursor.execute("CREATE TABLE IF NOT EXISTS planning_archive (id INTEGER PRIMARY KEY AUTOINCREMENT, num_tache TEXT, assigne_a TEXT, intitule TEXT, temps_estime TEXT, date_realisation TEXT, date_creation_brute TEXT, priorite TEXT, date_archivage TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS tchat_archive (id INTEGER PRIMARY KEY AUTOINCREMENT, expediteur TEXT, destinataire TEXT, texte TEXT, date_envoi TEXT, date_creation_brute TEXT, date_archivage TEXT)")
    try:
        cursor.execute("ALTER TABLE planning ADD COLUMN priorite TEXT DEFAULT '🟢 Pas très important'")
    except sqlite3.OperationalError:
        pass
    conn.commit()

if "db_ready" not in st.session_state:
    initialiser_structure_base()
    st.session_state.db_ready = True


# --- NETTOYAGE & ARCHIVAGE AUTOMATIQUE ---
@st.cache_data(ttl=43200)
def nettoyer_et_archiver_data():
    now_paris = datetime.now(ZoneInfo("Europe/Paris"))
    il_y_a_deux_semaines = (now_paris - timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S")
    il_y_a_six_mois = (now_paris - timedelta(days=180)).strftime("%Y-%m-%d %H:%M:%S")
    date_actuelle = now_paris.strftime("%Y-%m-%d %H:%M:%S")
    
    # Archivage automatique du tchat de plus de 14 jours
    cursor.execute("""
        INSERT INTO tchat_archive (expediteur, destinataire, texte, date_envoi, date_creation_brute, date_archivage)
        SELECT expediteur, destinataire, texte, date_envoi, date_creation_brute, ?
        FROM tchat WHERE date_creation_brute < ?
    """, (date_actuelle, il_y_a_deux_semaines))
    cursor.execute("DELETE FROM tchat WHERE date_creation_brute < ?", (il_y_a_deux_semaines,))
    
    # Déplacement physique des tâches terminées depuis plus de 14 jours
    cursor.execute("""
        INSERT INTO planning_archive (num_tache, assigne_a, intitule, temps_estime, date_realisation, date_creation_brute, priorite, date_archivage)
        SELECT num_tache, assigne_a, intitule, temps_estime, date_realisation, date_creation_brute, priorite, ?
        FROM planning WHERE date_realisation LIKE 'Fait le %' AND date_creation_brute < ?
    """, (date_actuelle, il_y_a_deux_semaines))
    cursor.execute("DELETE FROM planning WHERE date_realisation LIKE 'Fait le %' AND date_creation_brute < ?", (il_y_a_deux_semaines,))
    
    # Suppressions définitives après 6 mois
    cursor.execute("DELETE FROM tchat_archive WHERE date_creation_brute < ?", (il_y_a_six_mois,))
    cursor.execute("DELETE FROM planning_archive WHERE date_creation_brute < ?", (il_y_a_six_mois,))
    conn.commit()
    return True

nettoyer_et_archiver_data()

# --- GESTION DES SESSIONS ---
if "user" not in st.session_state: st.session_state.user = None
if "role" not in st.session_state: st.session_state.role = None
if "navigation_page" not in st.session_state: st.session_state.navigation_page = "📋 Planning de l'équipe"

# --- CONNEXION AUTOMATIQUE VIA URL ---
parametres_url = st.query_params
if st.session_state.user is None and "qui" in parametres_url:
    prenom_detecte = parametres_url["qui"].strip().capitalize()
    if prenom_detecte != "":
        if prenom_detecte in ["Christophe", "Chris"]:
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
                if prenom_propre in ["Christophe", "Chris"]:
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
        cursor.execute("SELECT prenom FROM utilisateurs WHERE prenom NOT IN ('Christophe', 'Chris') ORDER BY prenom ASC")
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
            
            st.write("Lien **Chris** :")
            st.code(f"{base_url}/?qui=Chris", language="text")
            
            for u in membres:
                st.write(f"Lien **{u[0]}** :")
                st.code(f"{base_url}/?qui={u[0]}", language="text")


# ==========================================
# PAGE 1 : LE PLANNING DYNAMIQUE
# ==========================================
if page == "📋 Planning de l'équipe":
    st.title("📋 Planning Global de l'Équipe")
    st.caption("Suivi synchronisé en temps réel (sans rechargement de page).")

    if st.session_state.role == "Administrateur":
        with st.expander("➕ Créer et affecter une nouvelle tâche", expanded=False):
            cursor.execute("SELECT prenom FROM utilisateurs WHERE prenom NOT IN ('Christophe', 'Chris')")
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
                rep = [0.7, 1.4, 2.8, 1.8, 0.8, 2.2, 1.1, 1.0]
                cols_h = st.columns(rep, vertical_alignment="center")
            else:
                rep = [0.7, 1.5, 3.2, 1.9, 0.9, 2.4, 1.1]
                cols_h = st.columns(rep, vertical_alignment="center")
            
            cols_h[0].markdown("<div class='header-mark' style='text-align: center;'><b>N°</b></div>", unsafe_allow_html=True)
            cols_h[1].markdown("<div style='text-align: center;'><b>Assigné à</b></div>", unsafe_allow_html=True)
            cols_h[2].markdown("<div style='text-align: center;'><b>Mission</b></div>", unsafe_allow_html=True)
            cols_h[3].markdown("<div style='text-align: center;'><b>Urgence</b></div>", unsafe_allow_html=True)
            cols_h[4].markdown("<div style='text-align: center;'><b>Temps</b></div>", unsafe_allow_html=True)
            cols_h[5].markdown("<div style='text-align: center;'><b>Statut</b></div>", unsafe_allow_html=True)
            cols_h[6].markdown("<div style='text-align: center;'><b>Action</b></div>", unsafe_allow_html=True)
            if st.session_state.role == "Administrateur": cols_h[7].markdown("<div style='text-align: center;'><b>Suppr.</b></div>", unsafe_allow_html=True)
                
            st.markdown('<hr class="desktop-text" style="margin: 10px 0; border-color: #cbd5e1;">', unsafe_allow_html=True)

            for t in taches:
                id_t, num, qui, quoi, temps, statut, priorite = t
                if not priorite: priorite = "🟢 Pas très important"
                
                cols = st.columns(rep, vertical_alignment="center")
                
                cols[0].markdown(f'<div class="task-row-mark desktop-text align-center-fix"><b>{num}</b></div><div class="mobile-text" style="font-size: 1.15em; color: #1e3a8a; margin-bottom: 4px; border-bottom: 2px solid #e2e8f0; padding-bottom: 4px;"><b>🔢 Tâche N° {num}</b></div>', unsafe_allow_html=True)
                cols[1].markdown(f'<div class="desktop-text align-center-fix">{qui}</div><div class="mobile-text"><b>👤 Assigné à :</b> {qui}</div>', unsafe_allow_html=True)
                cols[2].markdown(f'<div class="desktop-text align-center-fix">{quoi}</div><div class="mobile-text"><b>📋 Mission :</b> {quoi}</div>', unsafe_allow_html=True)
                cols[3].markdown(f'<div class="desktop-text align-center-fix">{priorite}</div><div class="mobile-text"><b>🚨 Urgence :</b> {priorite}</div>', unsafe_allow_html=True)
                cols[4].markdown(f'<div class="desktop-text align-center-fix">{temps}</div><div class="mobile-text"><b>⏱️ Temps :</b> {temps}</div>', unsafe_allow_html=True)
                
                if statut == "En cours ⏳":
                    cols[5].markdown('<div class="desktop-text align-center-fix">🟡 <b>En cours</b></div><div class="mobile-text" style="margin-bottom: 6px;"><b>⚡ Statut :</b> 🟡 En cours</div>', unsafe_allow_html=True)
                else:
                    cols[5].markdown(f'<div class="desktop-text align-center-fix">🟢 {statut}</div><div class="mobile-text" style="margin-bottom: 6px;"><b>⚡ Statut :</b> 🟢 {statut}</div>', unsafe_allow_html=True)
                    
                if statut == "En cours ⏳":
                    if st.session_state.user == qui or st.session_state.role == "Administrateur":
                        if cols[6].button("Fait ✅", key=f"btn_fait_{id_t}", use_container_width=True):
                            maintenant = datetime.now(ZoneInfo("Europe/Paris")).strftime("%d/%m/%Y à %H:%M")
                            cursor.execute("UPDATE planning SET date_realisation = ? WHERE id = ?", (f"Fait le {maintenant}", id_t))
                            conn.commit()
                            st.rerun()
                    else:
                        cols[6].markdown("<div class='desktop-text align-center-fix' style='color: gray;'>—</div>", unsafe_allow_html=True)
                else:
                    if st.session_state.user == qui or st.session_state.role == "Administrateur":
                        if cols[6].button("Annuler ↩️", key=f"btn_annuler_{id_t}", use_container_width=True):
                            cursor.execute("UPDATE planning SET date_realisation = 'En cours ⏳' WHERE id = ?", (id_t,))
                            conn.commit()
                            st.rerun()
                    else:
                        cols[6].markdown("<div class='desktop-text align-center-fix' style='color: gray;'>—</div>", unsafe_allow_html=True)
                
                if st.session_state.role == "Administrateur":
                    if cols[7].button("🗑️", key=f"btn_del_tache_{id_t}", use_container_width=True):
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
    
    cursor.execute("SELECT prenom FROM utilisateurs")
    employes = [row[0] for row in cursor.fetchall()]
    if "Christophe" not in employes: employes.append("Christophe")
    if "Chris" not in employes: employes.append("Chris")
        
    options_tchat = ["📢 Canal #Général"] + [f"🔒 Privé avec {emp}" for emp in employes if emp != st.session_state.user]
    choix_tchat = st.selectbox("Discussion active :", options_tchat)
    st.write("---")

    @st.fragment(run_every=6)
    def afficher_flux_messages(cible_tchat):
        if cible_tchat == "📢 Canal #Général":
            st.subheader("📢 Fil d'actualité Général")
            cursor.execute("SELECT id, expediteur, texte, date_envoi FROM tchat WHERE destinataire = 'Tous' ORDER BY id ASC")
        else:
            cible = cible_tchat.replace("🔒 Privé avec ", "")
            st.subheader(f"🔒 Bulle privée avec {cible}")
            cursor.execute("SELECT id, expediteur, texte, date_envoi FROM tchat WHERE (expediteur = ? AND destinataire = ?) OR (expediteur = ? AND destinataire = ?) ORDER BY id ASC", (st.session_state.user, cible, cible, st.session_state.user))
        
        messages = cursor.fetchall()
        zone_msg = st.container(height=380)
        with zone_msg:
            if messages:
                for m in messages:
                    id_msg, exp, txt, date = m
                    if st.session_state.role == "Administrateur":
                        col_b_msg, col_b_del = st.columns([9.1, 0.9], vertical_alignment="center")
                        with col_b_msg:
                            st.chat_message("user" if exp == st.session_state.user else "assistant").write(f"**{'Vous' if exp == st.session_state.user else exp}** ({date}) : {txt}")
                        if col_b_del.button("🗑️", key=f"del_{id_msg}", use_container_width=True):
                            cursor.execute("DELETE FROM tchat WHERE id = ?", (id_msg,))
                            conn.commit()
                            st.rerun()
                    else:
                        st.chat_message("user" if exp == st.session_state.user else "assistant").write(f"**{'Vous' if exp == st.session_state.user else exp}** ({date}) : {txt}")
            else:
                st.caption("Aucun échange pour le moment.")

    afficher_flux_messages(choix_tchat)

    with st.form("form_msg", clear_on_submit=True):
        col_txt, col_btn = st.columns([8.2, 1.8], vertical_alignment="center")
        nouveau_msg = col_txt.text_input("Tapez votre message ici...", label_visibility="collapsed")
        if col_btn.form_submit_button("Envoyer 🚀", use_container_width=True) and nouveau_msg.strip() != "":
            dest = "Tous" if choix_tchat == "📢 Canal #Général" else choix_tchat.replace("🔒 Privé avec ", "")
            now_paris = datetime.now(ZoneInfo("Europe/Paris"))
            cursor.execute("INSERT INTO tchat (expediteur, destinataire, texte, date_envoi, date_creation_brute) VALUES (?, ?, ?, ?, ?)", (st.session_state.user, dest, nouveau_msg.strip(), now_paris.strftime("%H:%M"), now_paris.strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            st.rerun()


# ==========================================
# 🗄️ PAGE 3 : ARCHIVES VISIBLES ET SUPPRIMABLES
# ==========================================
elif page == "🗄️ Archives (6 mois)" and st.session_state.role == "Administrateur":
    st.title("🗄️ Archives Administrateur")
    
    onglet_taches, onglet_messages = st.tabs(["📋 Archives Tâches", "💬 Archives Tchat"])
    
    with onglet_taches:
        # REQUÊTE UNIFIÉE : On fusionne les tâches déplacées ET celles marquées "Fait" en cours pour tout voir en direct
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
            cols_h[0].markdown("<div style='text-align: center;'><b>N°</b></div>", unsafe_allow_html=True)
            cols_h[1].markdown("<div style='text-align: center;'><b>Assigné à</b></div>", unsafe_allow_html=True)
            cols_h[2].markdown("<div style='text-align: center;'><b>Mission</b></div>", unsafe_allow_html=True)
            cols_h[3].markdown("<div style='text-align: center;'><b>Urgence</b></div>", unsafe_allow_html=True)
            cols_h[4].markdown("<div style='text-align: center;'><b>Temps</b></div>", unsafe_allow_html=True)
            cols_h[5].markdown("<div style='text-align: center;'><b>Statut</b></div>", unsafe_allow_html=True)
            cols_h[6].markdown("<div style='text-align: center;'><b>Archivé le</b></div>", unsafe_allow_html=True)
            cols_h[7].markdown("<div style='text-align: center;'><b>Suppr.</b></div>", unsafe_allow_html=True)
            
            st.markdown('<hr style="margin: 10px 0; border-color: #cbd5e1;">', unsafe_allow_html=True)
            
            for ta in taches_archived:
                provenance, id_arch, num, qui, quoi, temps, statut, priorite, date_arch = ta
                c = st.columns(rep_arch, vertical_alignment="center")
                
                c[0].markdown(f'<div class="align-center-fix"><b>{num}</b></div>', unsafe_allow_html=True)
                c[1].markdown(f'<div class="align-center-fix">{qui}</div>', unsafe_allow_html=True)
                c[2].markdown(f'<div class="align-center-fix">{quoi}</div>', unsafe_allow_html=True)
                c[3].markdown(f'<div class="align-center-fix">{priorite}</div>', unsafe_allow_html=True)
                c[4].markdown(f'<div class="align-center-fix">{temps}</div>', unsafe_allow_html=True)
                c[5].markdown(f'<div class="align-center-fix">{statut}</div>', unsafe_allow_html=True)
                c[6].markdown(f'<div class="align-center-fix"><i>{date_arch}</i></div>', unsafe_allow_html=True)
                
                # Bouton de suppression définitive aligné au poil
                if c[7].button("🗑️", key=f"btn_del_arch_{provenance}_{id_arch}", use_container_width=True):
                    if provenance == 'historique':
                        cursor.execute("DELETE FROM planning_archive WHERE id = ?", (id_arch,))
                    else:
                        cursor.execute("DELETE FROM planning WHERE id = ?", (id_arch,))
                    conn.commit()
                    st.rerun()
                    
                st.markdown('<hr style="margin: 10px 0; border-color: #f1f5f9;">', unsafe_allow_html=True)
        else:
            st.info("Archives de tâches vides.")
            
    with onglet_messages:
        cursor.execute("SELECT id, expediteur, destinataire, texte, date_creation_brute FROM tchat_archive ORDER BY id DESC")
        messages_archived = cursor.fetchall()
        
        if messages_archived:
            with st.container(height=400):
                for ma in messages_archived:
                    id_msg_arch, exp, dest, txt, date_brute = ma
                    col_b_msg, col_b_del = st.columns([9.1, 0.9], vertical_alignment="center")
                    
                    with col_b_msg:
                        st.write(f"📢 **[{dest}]** *({date_brute})* **{exp}** : {txt}")
                    
                    if col_b_del.button("🗑️", key=f"del_arch_msg_{id_msg_arch}", use_container_width=True):
                        cursor.execute("DELETE FROM tchat_archive WHERE id = ?", (id_msg_arch,))
                        conn.commit()
                        st.rerun()
        else:
            st.info("Aucun message archivé.")
