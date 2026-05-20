import streamlit as st
import requests
import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Hub Entreprise", page_icon="📱", layout="wide")

# Adresse par défaut
VOTRE_LIEN_ACTUEL = "https://maupu45.streamlit.app"

# --- CONNEXION BASE DE DONNÉES CLOUD (TURSO HTTP) ---
DB_URL = st.secrets["DB_URL"].replace("libsql://", "https://")
TOKEN = st.secrets["DB_TOKEN"]

class TursoAdapter:
    def __init__(self):
        self.last_fetched_rows = []

    def execute(self, sql, params=()):
        # Utilisation d'une session persistante (HTTP Keep-Alive) pour éliminer la latence réseau
        if "turso_session" not in st.session_state:
            st.session_state.turso_session = requests.Session()
            
        headers = {
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json"
        }
        
        args = []
        for p in params:
            if isinstance(p, int):
                args.append({"type": "integer", "value": str(p)})
            elif isinstance(p, float):
                args.append({"type": "float", "value": str(p)})
            elif p is None:
                args.append({"type": "null"})
            else:
                args.append({"type": "text", "value": str(p)})
                
        payload = {
            "requests": [
                {"type": "execute", "stmt": {"sql": sql, "args": args}},
                {"type": "close"}
            ]
        }
        
        # Appel via la session persistante de la session_state
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
            error_msg = first_result.get("error", {}).get("message", "Erreur SQL inconnue")
            raise sqlite3.OperationalError(error_msg)
            
        raw_rows = first_result.get("response", {}).get("result", {}).get("rows", [])
        parsed_rows = []
        for raw_row in raw_rows:
            parsed_row = []
            for col in raw_row:
                ctype = col.get("type")
                cval = col.get("value")
                if ctype == "integer":
                    parsed_row.append(int(cval))
                elif ctype == "float":
                    parsed_row.append(float(cval))
                elif ctype == "null":
                    parsed_row.append(None)
                else:
                    parsed_row.append(cval)
            parsed_rows.append(tuple(parsed_row))
            
        self.last_fetched_rows = parsed_rows
        return self

    def fetchall(self):
        return self.last_fetched_rows

    def fetchone(self):
        return self.last_fetched_rows[0] if self.last_fetched_rows else None

    def commit(self):
        pass

    def cursor(self):
        return self

conn = TursoAdapter()
cursor = conn.cursor()

# --- INITIALISATION DE LA BASE (S'EXÉCUTE 1 SEULE FOIS) ---
@st.cache_resource
def initialiser_structure_base():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS planning (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        num_tache TEXT,
        assigne_a TEXT,
        intitule TEXT,
        temps_estime TEXT,
        date_realisation TEXT,
        date_creation_brute TEXT,
        priorite TEXT
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tchat (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        expediteur TEXT,
        destinataire TEXT,
        texte TEXT,
        date_envoi TEXT,
        date_creation_brute TEXT
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS utilisateurs (
        prenom TEXT PRIMARY KEY
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS planning_archive (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        num_tache TEXT,
        assigne_a TEXT,
        intitule TEXT,
        temps_estime TEXT,
        date_realisation TEXT,
        date_creation_brute TEXT,
        priorite TEXT,
        date_archivage TEXT
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tchat_archive (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        expediteur TEXT,
        destinataire TEXT,
        texte TEXT,
        date_envoi TEXT,
        date_creation_brute TEXT,
        date_archivage TEXT
    )""")
    
    try:
        cursor.execute("ALTER TABLE planning ADD COLUMN priorite TEXT DEFAULT '🟢 Pas très important'")
    except sqlite3.OperationalError:
        pass
        
    conn.commit()
    return True

initialiser_structure_base()


# =========================================================================
# 🧹 NETTOYAGE & ARCHIVAGE (OPTIMISÉ : 1 FOIS TOUTES LES 12H)
# =========================================================================
@st.cache_data(ttl=43200)
def nettoyer_et_archiver_data():
    now_paris = datetime.now(ZoneInfo("Europe/Paris"))
    il_y_a_deux_semaines = (now_paris - timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S")
    il_y_a_six_mois = (now_paris - timedelta(days=180)).strftime("%Y-%m-%d %H:%M:%S")
    date_actuelle = now_paris.strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
        INSERT INTO tchat_archive (expediteur, destinataire, texte, date_envoi, date_creation_brute, date_archivage)
        SELECT expediteur, destinataire, texte, date_envoi, date_creation_brute, ?
        FROM tchat WHERE date_creation_brute < ?
    """, (date_actuelle, il_y_a_deux_semaines))
    cursor.execute("DELETE FROM tchat WHERE date_creation_brute < ?", (il_y_a_deux_semaines,))
    
    cursor.execute("""
        INSERT INTO planning_archive (num_tache, assigne_a, intitule, temps_estime, date_realisation, date_creation_brute, priorite, date_archivage)
        SELECT num_tache, assigne_a, intitule, temps_estime, date_realisation, date_creation_brute, priorite, ?
        FROM planning WHERE date_realisation LIKE 'Le %' AND date_creation_brute < ?
    """, (date_actuelle, il_y_a_deux_semaines))
    cursor.execute("DELETE FROM planning WHERE date_realisation LIKE 'Le %' AND date_creation_brute < ?", (il_y_a_deux_semaines,))
    
    cursor.execute("DELETE FROM tchat_archive WHERE date_creation_brute < ?", (il_y_a_six_mois,))
    cursor.execute("DELETE FROM planning_archive WHERE date_creation_brute < ?", (il_y_a_six_mois,))
    
    conn.commit()
    return True

nettoyer_et_archiver_data()


# --- GESTION DE LA SESSION USER ---
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None
if "navigation_page" not in st.session_state:
    st.session_state.navigation_page = "📋 Planning de l'équipe"


# ==========================================================
# 🚀 CONNEXION AUTOMATIQUE VIA LIEN (?qui=Prenom)
# ==========================================================
if st.session_state.user is None:
    parametres_url = st.query_params
    if "qui" in parametres_url:
        prenom_detecte = parametres_url["qui"].strip().capitalize()
        if prenom_detecte != "":
            if prenom_detecte == "Christophe":
                st.session_state.user = "Christophe"
                st.session_state.role = "Administrateur"
            else:
                st.session_state.user = prenom_detecte
                st.session_state.role = "Employé"
            
            cursor.execute("INSERT OR IGNORE INTO utilisateurs (prenom) VALUES (?)", (st.session_state.user,))
            conn.commit()
            st.rerun()


# --- BARRE LATÉRALE (CONNEXION, NAVIGATION & MODÉRATION) ---
with st.sidebar:
    st.title("🔑 Espace Connexion")
    
    if st.session_state.user is None:
        identifiant = st.text_input("Identifiant (Prénom)")
        role_choisi = st.selectbox("Votre rôle", ["Employé", "Administrateur"])
        
        if st.button("Se connecter", use_container_width=True):
            prenom_propre = identifiant.strip().capitalize()
            if prenom_propre != "":
                if role_choisi == "Administrateur" and prenom_propre != "Christophe":
                    st.error("❌ Accès Admin refusé. Seul Christophe est administrateur.")
                    st.session_state.user = prenom_propre
                    st.session_state.role = "Employé"
                else:
                    st.session_state.user = prenom_propre
                    st.session_state.role = role_choisi
                
                cursor.execute("INSERT OR IGNORE INTO utilisateurs (prenom) VALUES (?)", (st.session_state.user,))
                conn.commit()
                st.rerun()
    else:
        st.success(f"Connecté : {st.session_state.user} ({st.session_state.role})")
        if st.button("Se déconnecter", use_container_width=True):
            st.session_state.user = None
            st.session_state.role = None
            st.session_state.navigation_page = "📋 Planning de l'équipe"
            st.query_params.clear()
            st.rerun()
            
    st.write("---")
    st.title("🗺️ Navigation")
    
    liste_pages = ["📋 Planning de l'équipe", "💬 Zone Tchat"]
    if st.session_state.role == "Administrateur":
        liste_pages.append("🗄️ Archives (6 mois)")
        
    page = st.radio("Aller vers :", liste_pages, key="navigation_page")

    # --- PANNEAU DE GESTION (EXCLUSIF ADMIN) ---
    if st.session_state.role == "Administrateur":
        st.write("---")
        st.title("🛡️ Modération")
        
        # OPTIMISATION : Une seule requête pour obtenir les membres de la sidebar au lieu de deux
        cursor.execute("SELECT prenom FROM utilisateurs WHERE prenom != 'Christophe' ORDER BY prenom ASC")
        membres = cursor.fetchall()
        
        with st.expander("👥 Liste des utilisateurs", expanded=False):
            if membres:
                for m in membres:
                    nom_membre = m[0]
                    col_m_nom, col_m_del = st.columns([7, 3], vertical_alignment="center")
                    col_m_nom.write(f"• **{nom_membre}**")
                    if col_m_del.button("🗑️", key=f"user_del_{nom_membre}", use_container_width=True, help=f"Supprimer {nom_membre}"):
                        cursor.execute("DELETE FROM utilisateurs WHERE prenom = ?", (nom_membre,))
                        conn.commit()
                        st.toast(f"Utilisateur {nom_membre} supprimé de la base.")
                        st.rerun()
            else:
                st.caption("Aucun employé enregistré pour le moment.")
                
        with st.expander("🔗 Liens d'accès direct", expanded=False):
            st.caption("Copie ces liens pour ton équipe (connexion automatique) :")
            
            base_url = VOTRE_LIEN_ACTUEL
            if "hub-entreprise.streamlit.app" in base_url:
                st.warning("💡 Pense à adapter la variable `VOTRE_LIEN_ACTUEL` à la ligne 11 si l'adresse de ton application change.")

            st.write("Lien pour **Christophe (Admin)** :")
            st.code(f"{base_url}/?qui=Christophe", language="text")
            
            # Réutilisation directe des membres déjà chargés en mémoire
            for u in membres:
                st.write(f"Lien pour **{u[0]}** :")
                st.code(f"{base_url}/?qui={u[0]}", language="text")

# --- EMPECHER L'ACCÈS SANS CONNEXION ---
if st.session_state.user is None:
    st.warning("⚠️ Veuillez entrer votre prénom dans la barre latérale ou utiliser votre lien d'accès direct.")
    st.stop()


# ==========================================
# PAGE 1 : LE PLANNING DYNAMIQUE
# ==========================================
if page == "📋 Planning de l'équipe":
    st.title("📋 Planning Global de l'Équipe")
    st.caption("Suivi des tâches actives (Moins de 14 jours après réalisation).")

    if st.session_state.role == "Administrateur":
        with st.expander("➕ Ajouter une nouvelle tâche (Réservé Admin)", expanded=False):
            cursor.execute("SELECT prenom FROM utilisateurs WHERE prenom != 'Christophe'")
            res_users = cursor.fetchall()
            liste_employes = [row[0] for row in res_users]
            
            with st.form("form_tache"):
                col1, col2 = st.columns(2)
                with col1:
                    num_t = st.text_input("N° de tâche", value="001")
                    if liste_employes:
                        qui = st.selectbox("Assigné à (Sélectionner un employé)", liste_employes)
                    else:
                        qui = st.text_input("Assigné à (Aucun employé connecté pour l'instant, tapez son nom)")
                    
                    priorite_choisie = st.selectbox(
                        "Niveau d'urgence / Importance", 
                        ["🟢 Pas très important", "🟠 Important", "🔴 Très urgent"]
                    )
                with col2:
                    temps = st.text_input("Temps approximatif (ex: 2h30, 1j)")
                    action = st.text_area("Intitulé / Travail à réaliser")
                
                if st.form_submit_button("Inscrire au planning"):
                    if qui and action:
                        now_brute = datetime.now(ZoneInfo("Europe/Paris")).strftime("%Y-%m-%d %H:%M:%S")
                        cursor.execute(
                            "INSERT INTO planning (num_tache, assigne_a, intitule, temps_estime, date_realisation, date_creation_brute, priorite) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (num_t, qui, action, temps, "En cours ⏳", now_brute, priorite_choisie)
                        )
                        conn.commit()
                        st.success("Tâche ajoutée avec succès !")
                        st.rerun()
                    else:
                        st.error("Veuillez remplir les champs obligatoires.")

    st.write("### 📅 Tableau de suivi")
    cursor.execute("SELECT id, num_tache, assigne_a, intitule, temps_estime, date_realisation, priorite FROM planning")
    taches = cursor.fetchall()
    
    if taches:
        if st.session_state.role == "Administrateur":
            repartition_colonnes = [0.7, 1.4, 2.8, 1.8, 0.8, 2.2, 1.1, 1.0]
            col_h_n, col_h_q, col_h_i, col_h_p, col_h_t, col_h_s, col_h_act, col_h_del = st.columns(repartition_colonnes, vertical_alignment="center")
        else:
            repartition_colonnes = [0.7, 1.5, 3.2, 1.9, 0.9, 2.4, 1.1]
            col_h_n, col_h_q, col_h_i, col_h_p, col_h_t, col_h_s, col_h_act = st.columns(repartition_colonnes, vertical_alignment="center")
        
        col_h_n.markdown("<div style='text-align: center;'><b>N°</b></div>", unsafe_allow_html=True)
        col_h_q.markdown("<div style='text-align: center;'><b>Assigné à</b></div>", unsafe_allow_html=True)
        col_h_i.markdown("<div style='text-align: center;'><b>Mission</b></div>", unsafe_allow_html=True)
        col_h_p.markdown("<div style='text-align: center;'><b>Urgence</b></div>", unsafe_allow_html=True)
        col_h_t.markdown("<div style='text-align: center;'><b>Temps</b></div>", unsafe_allow_html=True)
        col_h_s.markdown("<div style='text-align: center;'><b>Statut / Réalisation</b></div>", unsafe_allow_html=True)
        col_h_act.markdown("<div style='text-align: center;'><b>Action</b></div>", unsafe_allow_html=True)
        if st.session_state.role == "Administrateur":
            col_h_del.markdown("<div style='text-align: center;'><b>Suppr.</b></div>", unsafe_allow_html=True)
            
        st.write("---")

        for t in taches:
            id_t, num, qui, quoi, temps, statut, priorite = t
            if not priorite: priorite = "🟢 Pas très important"
            
            if st.session_state.role == "Administrateur":
                col_n, col_q, col_i, col_p, col_t, col_s, col_act, col_del = st.columns(repartition_colonnes, vertical_alignment="center")
            else:
                col_n, col_q, col_i, col_p, col_t, col_s, col_act = st.columns(repartition_colonnes, vertical_alignment="center")
            
            col_n.markdown(f"<div style='text-align: center;'><b>{num}</b></div>", unsafe_allow_html=True)
            col_q.markdown(f"<div style='text-align: center;'>{qui}</div>", unsafe_allow_html=True)
            col_i.markdown(f"<div style='text-align: center;'>{quoi}</div>", unsafe_allow_html=True)
            col_p.markdown(f"<div style='text-align: center;'>{priorite}</div>", unsafe_allow_html=True)
            col_t.markdown(f"<div style='text-align: center;'>{temps}</div>", unsafe_allow_html=True)
            
            if statut == "En cours ⏳":
                col_s.markdown("<div style='text-align: center;'>🟡 <b>En cours</b></div>", unsafe_allow_html=True)
            else:
                col_s.markdown(f"<div style='text-align: center;'>🟢 {statut}</div>", unsafe_allow_html=True)
                
            if statut == "En cours ⏳":
                if st.session_state.user == qui or st.session_state.role == "Administrateur":
                    if col_act.button("Fait ✅", key=f"btn_fait_{id_t}", use_container_width=True):
                        maintenant = datetime.now(ZoneInfo("Europe/Paris")).strftime("%d/%m/%Y à %H:%M")
                        cursor.execute("UPDATE planning SET date_realisation = ? WHERE id = ?", (f"Fait le {maintenant}", id_t))
                        conn.commit()
                        st.toast(f"Tâche {num} validée !")
                        st.rerun()
                else:
                    col_act.markdown("<div style='text-align: center; color: gray;'>—</div>", unsafe_allow_html=True)
            else:
                if st.session_state.user == qui or st.session_state.role == "Administrateur":
                    if col_act.button("Annuler ↩️", key=f"btn_annuler_{id_t}", use_container_width=True):
                        cursor.execute("UPDATE planning SET date_realisation = 'En cours ⏳' WHERE id = ?", (id_t,))
                        conn.commit()
                        st.toast(f"Tâche {num} remise en cours !")
                        st.rerun()
                else:
                    col_act.markdown("<div style='text-align: center; color: gray;'>—</div>", unsafe_allow_html=True)
            
            if st.session_state.role == "Administrateur":
                if col_del.button("🗑️", key=f"btn_del_tache_{id_t}", use_container_width=True, help="Supprimer définitivement cette tâche"):
                    cursor.execute("DELETE FROM planning WHERE id = ?", (id_t,))
                    conn.commit()
                    st.toast(f"Tâche {num} définitivement supprimée.")
                    st.rerun()
                    
            st.write("---")
    else:
        st.info("Aucune tâche prévue pour le moment.")


# ==========================================
# PAGE 2 : LE TCHAT PRIVÉ ET GROUPÉ
# ==========================================
elif page == "💬 Zone Tchat":
    st.title("💬 Centre de Communication")
    
    cursor.execute("SELECT prenom FROM utilisateurs")
    res_users = cursor.fetchall()
    employes = [row[0] for row in res_users]
    if "Christophe" not in employes:
        employes.append("Christophe")
        
    options_tchat = ["📢 Canal #Général (Tout le monde)"] + [f"🔒 Privé avec {emp}" for emp in employes if emp != st.session_state.user]
    choix_tchat = st.selectbox("Où voulez-vous écrire ?", options_tchat)

    st.write("---")

    if choix_tchat == "📢 Canal #Général (Tout le monde)":
        st.subheader("📢 Canal #Général")
        cursor.execute("SELECT id, expediteur, texte, date_envoi FROM tchat WHERE destinataire = 'Tous' ORDER BY id ASC")
        messages = cursor.fetchall()
    else:
        cible = choix_tchat.replace("🔒 Privé avec ", "")
        st.subheader(f"🔒 Discussion privée avec {cible}")
        cursor.execute(
            "SELECT id, expediteur, texte, date_envoi FROM tchat WHERE (expediteur = ? AND destinataire = ?) OR (expediteur = ? AND destinataire = ?) ORDER BY id ASC",
            (st.session_state.user, cible, cible, st.session_state.user)
        )
        messages = cursor.fetchall()

    zone_msg = st.container(height=350)
    with zone_msg:
        if messages:
            for m in messages:
                id_msg, exp, txt, date = m
                
                if st.session_state.role == "Administrateur":
                    col_b_msg, col_b_del = st.columns([9.2, 0.8], vertical_alignment="center")
                    with col_b_msg:
                        if exp == st.session_state.user:
                            st.chat_message("user").write(f"**Vous** ({date}) : {txt}")
                        else:
                            st.chat_message("assistant").write(f"**{exp}** ({date}) : {txt}")
                    with col_b_del:
                        if st.button("🗑️", key=f"del_{id_msg}", use_container_width=True, help="Supprimer ce message"):
                            cursor.execute("DELETE FROM tchat WHERE id = ?", (id_msg,))
                            conn.commit()
                            st.rerun()
                else:
                    if exp == st.session_state.user:
                        st.chat_message("user").write(f"**Vous** ({date}) : {txt}")
                    else:
                        st.chat_message("assistant").write(f"**{exp}** ({date}) : {txt}")
        else:
            st.caption("Aucun message dans cette discussion pour le moment...")

    with st.form("form_msg", clear_on_submit=True):
        col_txt, col_btn = st.columns([8, 2])
        nouveau_msg = col_txt.text_input("Votre message...", label_visibility="collapsed")
        if col_btn.form_submit_button("Envoyer 🚀", use_container_width=True) and nouveau_msg.strip() != "":
            dest = "Tous" if choix_tchat == "📢 Canal #Général (Tout le monde)" else choix_tchat.replace("🔒 Privé avec ", "")
            
            now_paris = datetime.now(ZoneInfo("Europe/Paris"))
            maintenant_heure = now_paris.strftime("%H:%M")
            now_brute = now_paris.strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute(
                "INSERT INTO tchat (expediteur, destinataire, texte, date_envoi, date_creation_brute) VALUES (?, ?, ?, ?, ?)",
                (st.session_state.user, dest, nouveau_msg.strip(), maintenant_heure, now_brute)
            )
            conn.commit()
            st.rerun()


# =========================================================================
# 🗄️ NOUVELLE PAGE : ARCHIVES ET HISTORIQUE (RESERVÉ STRICTEMENT ADMIN)
# =========================================================================
elif page == "🗄️ Archives (6 mois)" and st.session_state.role == "Administrateur":
    st.title("🗄️ Archives et Historique de l'Entreprise")
    st.caption("Espace de sauvegarde sécurisé (Rétention des données pendant 6 mois maximum).")
    
    onglet_taches, onglet_messages = st.tabs(["📋 Archives des Tâches", "💬 Archives du Tchat"])
    
    with onglet_taches:
        st.write("### 📅 Historique des tâches terminées")
        cursor.execute("SELECT num_tache, assigne_a, intitule, temps_estime, date_realisation, priorite, date_archivage FROM planning_archive ORDER BY id DESC")
        taches_archived = cursor.fetchall()
        
        if taches_archived:
            repartition_arch = [0.8, 1.5, 3.2, 1.8, 1.0, 2.5, 1.5]
            c_h_n, c_h_q, c_h_i, c_h_p, c_h_t, c_h_s, c_h_a = st.columns(repartition_arch, vertical_alignment="center")
            c_h_n.markdown("<div style='text-align: center;'><b>N°</b></div>", unsafe_allow_html=True)
            c_h_q.markdown("<div style='text-align: center;'><b>Assigné à</b></div>", unsafe_allow_html=True)
            c_h_i.markdown("<div style='text-align: center;'><b>Mission</b></div>", unsafe_allow_html=True)
            c_h_p.markdown("<div style='text-align: center;'><b>Urgence</b></div>", unsafe_allow_html=True)
            c_h_t.markdown("<div style='text-align: center;'><b>Temps</b></div>", unsafe_allow_html=True)
            c_h_s.markdown("<div style='text-align: center;'><b>Date de Fin</b></div>", unsafe_allow_html=True)
            c_h_a.markdown("<div style='text-align: center;'><b>Archivé le</b></div>", unsafe_allow_html=True)
            st.write("---")
            
            for ta in taches_archived:
                num, qui, quoi, temps, statut, priorite, date_arch = ta
                c_n, c_q, c_i, c_p, c_t, c_s, c_a = st.columns(repartition_arch, vertical_alignment="center")
                
                c_n.markdown(f"<div style='text-align: center;'><b>{num}</b></div>", unsafe_allow_html=True)
                c_q.markdown(f"<div style='text-align: center;'>{qui}</div>", unsafe_allow_html=True)
                c_i.markdown(f"<div style='text-align: center;'>{quoi}</div>", unsafe_allow_html=True)
                c_p.markdown(f"<div style='text-align: center;'>{priorite}</div>", unsafe_allow_html=True)
                c_t.markdown(f"<div style='text-align: center;'>{temps}</div>", unsafe_allow_html=True)
                c_s.markdown(f"<div style='text-align: center;'>🟢 {statut}</div>", unsafe_allow_html=True)
                
                try:
                    dt_arch = datetime.strptime(date_arch, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y")
                except:
                    dt_arch = date_arch
                c_a.markdown(f"<div style='text-align: center; color: gray;'>{dt_arch}</div>", unsafe_allow_html=True)
                st.write("---")
        else:
            st.info("Aucune ancienne tâche dans les archives pour le moment.")
            
    with onglet_messages:
        st.write("### 💬 Historique des anciennes conversations")
        cursor.execute("SELECT expediteur, destinataire, texte, date_creation_brute FROM tchat_archive ORDER BY id DESC")
        messages_archived = cursor.fetchall()
        
        if messages_archived:
            container_arch_msg = st.container(height=400)
            with container_arch_msg:
                for ma in messages_archived:
                    exp, dest, txt, date_brute = ma
                    try:
                        dt_msg = datetime.strptime(date_brute, "%Y-%m-%d %H:%M:%S").strftime("%d/%m à %H:%M")
                    except:
                        dt_msg = date_brute
                        
                    if dest == "Tous":
                        st.markdown(f"📢 **[Canal Général]** *({dt_msg})* **{exp}** : {txt}")
                    else:
                        st.markdown(f"🔒 **[Privé]** *({dt_msg})* **{exp}** ➔ **{dest}** : {txt}")
        else:
            st.info("Aucun ancien message dans les archives pour le moment.")
