import streamlit as st
import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Configuration de la page
st.set_page_config(page_title="Hub Entreprise", page_icon="📱", layout="wide")

# Connexion a la base de donnée permanente
conn = sqlite3.connect("donnees_permanentes.db", check_same_thread=False)
cursor = conn.cursor()

# Création des tables si elles n'existent pas
cursor.execute("""
CREATE TABLE IF NOT EXISTS planning (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    num_tache TEXT,
    assigne_a TEXT,
    intitule TEXT,
    temps_estime TEXT,
    date_realisation TEXT,
    date_creation_brute TEXT
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

# Table pour se souvenir des employés connectés
cursor.execute("""
CREATE TABLE IF NOT EXISTS utilisateurs (
    prenom TEXT PRIMARY KEY
)""")
conn.commit()


# Système de nettoyage au bout de 14j
def nettoyer_ancienne_data():
    il_y_a_deux_semaines = (datetime.now(ZoneInfo("Europe/Paris")) - timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("DELETE FROM tchat WHERE date_creation_brute < ?", (il_y_a_deux_semaines,))
    cursor.execute("DELETE FROM planning WHERE date_realisation LIKE 'Le %' AND date_creation_brute < ?", (il_y_a_deux_semaines,))
    conn.commit()

nettoyer_ancienne_data()


# Gestion session utilisateur
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None
if "navigation_page" not in st.session_state:
    st.session_state.navigation_page = "📋 Planning de l'équipe"


# Système de connexion automatique par lien
if st.session_state.user is None:
    # On intercepte les paramètres présents dans l'URL du navigateur
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
            
            # Sauvegarde automatique dans la liste des utilisateurs
            cursor.execute("INSERT OR IGNORE INTO utilisateurs (prenom) VALUES (?)", (st.session_state.user,))
            conn.commit()
            st.rerun()


# Barre de connexion
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
            # Nettoyage URL automatique au changement de compte
            st.query_params.clear()
            st.rerun()
            
    st.write("---")
    st.title("🗺️ Navigation")
    page = st.radio("Aller vers :", ["📋 Planning de l'équipe", "💬 Zone Tchat"], key="navigation_page")

    # Panneau gestion utilisateur pour uniquement l'admin
    if st.session_state.role == "Administrateur":
        st.write("---")
        st.title("🛡️ Modération")
        
        with st.expander("👥 Liste des utilisateurs", expanded=False):
            cursor.execute("SELECT prenom FROM utilisateurs WHERE prenom != 'Christophe' ORDER BY prenom ASC")
            membres = cursor.fetchall()
            
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
            st.caption("Copie ces liens pour ton équipe (connexion automatique sans mot de passe) :")
            # Adresse site dynamique
            base_url = "https://hub-entreprise.streamlit.app" 
            st.code(f"{base_url}/?qui=Christophe", language="text")
            
            cursor.execute("SELECT prenom FROM utilisateurs WHERE prenom != 'Christophe' ORDER BY prenom ASC")
            tous_les_users = cursor.fetchall()
            for u in tous_les_users:
                st.write(f"Lien pour **{u[0]}** :")
                st.code(f"{base_url}/?qui={u[0]}", language="text")

# Warning si pas co
if st.session_state.user is None:
    st.warning("⚠️ Veuillez entrer votre prénom dans la barre latérale ou utiliser votre lien d'accès direct.")
    st.stop()


# Page 1
if page == "📋 Planning de l'équipe":
    st.title("📋 Planning Global de l'Équipe")
    st.caption("Suivi des tâches en temps réel.")

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
                with col2:
                    temps = st.text_input("Temps approximatif (ex: 2h30, 1j)")
                    action = st.text_area("Intitulé / Travail à réaliser")
                
                if st.form_submit_button("Inscrire au planning"):
                    if qui and action:
                        now_brute = datetime.now(ZoneInfo("Europe/Paris")).strftime("%Y-%m-%d %H:%M:%S")
                        cursor.execute(
                            "INSERT INTO planning (num_tache, assigne_a, intitule, temps_estime, date_realisation, date_creation_brute) VALUES (?, ?, ?, ?, ?, ?)",
                            (num_t, qui, action, temps, "En cours ⏳", now_brute)
                        )
                        conn.commit()
                        st.success("Tâche ajoutée avec succès !")
                        st.rerun()
                    else:
                        st.error("Veuillez remplir les champs obligatoires.")

    st.write("### 📅 Tableau de suivi")
    cursor.execute("SELECT id, num_tache, assigne_a, intitule, temps_estime, date_realisation FROM planning")
    taches = cursor.fetchall()
    
    if taches:
        if st.session_state.role == "Administrateur":
            repartition_colonnes = [0.8, 1.5, 3.2, 1.0, 2.6, 1.2, 1.1]
            col_h_n, col_h_q, col_h_i, col_h_t, col_h_s, col_h_act, col_h_del = st.columns(repartition_colonnes, vertical_alignment="center")
        else:
            repartition_colonnes = [0.8, 1.8, 3.8, 1.0, 3.4, 1.2]
            col_h_n, col_h_q, col_h_i, col_h_t, col_h_s, col_h_act = st.columns(repartition_colonnes, vertical_alignment="center")
        
        col_h_n.markdown("<div style='text-align: center;'><b>N°</b></div>", unsafe_allow_html=True)
        col_h_q.markdown("<div style='text-align: center;'><b>Assigné à</b></div>", unsafe_allow_html=True)
        col_h_i.markdown("<div style='text-align: center;'><b>Mission</b></div>", unsafe_allow_html=True)
        col_h_t.markdown("<div style='text-align: center;'><b>Temps</b></div>", unsafe_allow_html=True)
        col_h_s.markdown("<div style='text-align: center;'><b>Statut / Réalisation</b></div>", unsafe_allow_html=True)
        col_h_act.markdown("<div style='text-align: center;'><b>Action</b></div>", unsafe_allow_html=True)
        if st.session_state.role == "Administrateur":
            col_h_del.markdown("<div style='text-align: center;'><b>Suppr.</b></div>", unsafe_allow_html=True)
            
        st.write("---")

        for t in taches:
            id_t, num, qui, quoi, temps, statut = t
            
            if st.session_state.role == "Administrateur":
                col_n, col_q, col_i, col_t, col_s, col_act, col_del = st.columns(repartition_colonnes, vertical_alignment="center")
            else:
                col_n, col_q, col_i, col_t, col_s, col_act = st.columns(repartition_colonnes, vertical_alignment="center")
            
            col_n.markdown(f"<div style='text-align: center;'><b>{num}</b></div>", unsafe_allow_html=True)
            col_q.markdown(f"<div style='text-align: center;'>{qui}</div>", unsafe_allow_html=True)
            col_i.markdown(f"<div style='text-align: center;'>{quoi}</div>", unsafe_allow_html=True)
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


#Page 2
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
