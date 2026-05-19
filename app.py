import streamlit as st
import sqlite3
from datetime import datetime, timedelta

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Hub Entreprise", page_icon="📱", layout="wide")

# --- CONNEXION BASE DE DONNÉES CLOUD PERMANENTE ---
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


# ==========================================
# 🧹 SYSTEME DE NETTOYAGE AUTOMATIQUE (14 JOURS)
# ==========================================
def nettoyer_ancienne_data():
    il_y_a_deux_semaines = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("DELETE FROM tchat WHERE date_creation_brute < ?", (il_y_a_deux_semaines,))
    cursor.execute("DELETE FROM planning WHERE date_realisation LIKE 'Le %' AND date_creation_brute < ?", (il_y_a_deux_semaines,))
    conn.commit()

nettoyer_ancienne_data()


# --- GESTION DE LA SESSION USER ---
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None
if "navigation_page" not in st.session_state:
    st.session_state.navigation_page = "📋 Planning de l'équipe"

# --- BARRE LATÉRALE (CONNEXION & NAVIGATION) ---
with st.sidebar:
    st.title("🔑 Espace Connexion")
    
    if st.session_state.user is None:
        identifiant = st.text_input("Identifiant (Prénom)")
        role_choisi = st.selectbox("Votre rôle", ["Employé", "Administrateur"])
        
        if st.button("Se connecter", use_container_width=True):
            prenom_propre = identifiant.strip().capitalize()
            if prenom_propre != "":
                # SÉCURITÉ ADMIN : Seul Christophe peut être Admin
                if role_choisi == "Administrateur" and prenom_propre != "Christophe":
                    st.error("❌ Accès Admin refusé. Seul Christophe est administrateur.")
                    st.session_state.user = prenom_propre
                    st.session_state.role = "Employé"
                else:
                    st.session_state.user = prenom_propre
                    st.session_state.role = role_choisi
                
                # Enregistrer l'utilisateur dans la base pour l'autocomplétion de l'admin
                cursor.execute("INSERT OR IGNORE INTO utilisateurs (prenom) VALUES (?)", (st.session_state.user,))
                conn.commit()
                st.rerun()
    else:
        st.success(f"Connecté : {st.session_state.user} ({st.session_state.role})")
        if st.button("Se déconnecter", use_container_width=True):
            st.session_state.user = None
            st.session_state.role = None
            # Force la réinitialisation visuelle du bouton radio sur le planning
            st.session_state.navigation_page = "📋 Planning de l'équipe"
            st.rerun()
            
    st.write("---")
    st.title("🗺️ Navigation")
    # Gestion forcée de la page par la session state key
    page = st.radio("Aller vers :", ["📋 Planning de l'équipe", "💬 Zone Tchat"], key="navigation_page")

# --- EMPECHER L'ACCÈS SANS CONNEXION ---
if st.session_state.user is None:
    st.warning("⚠️ Veuillez entrer votre prénom dans la barre latérale pour accéder à l'application.")
    st.stop()


# ==========================================
# PAGE 1 : LE PLANNING DYNAMIQUE
# ==========================================
if page == "📋 Planning de l'équipe":
    st.title("📋 Planning Global de l'Équipe")
    st.caption("Suivi des tâches en temps réel.")

    # Formulaire Ajout de Tâche (Réservé à Christophe l'Admin)
    if st.session_state.role == "Administrateur":
        with st.expander("➕ Ajouter une nouvelle tâche (Réservé Admin)", expanded=False):
            
            # Récupérer la liste de tous les utilisateurs connectés pour l'autocomplétion
            cursor.execute("SELECT prenom FROM utilisateurs WHERE prenom != 'Christophe'")
            res_users = cursor.fetchall()
            liste_employes = [row[0] for row in res_users]
            
            with st.form("form_tache"):
                col1, col2 = st.columns(2)
                with col1:
                    num_t = st.text_input("N° de tâche", value="001")
                    # AUTOCOMPLÉTION : Liste déroulante des employés connus
                    if liste_employes:
                        qui = st.selectbox("Assigné à (Sélectionner un employé)", liste_employes)
                    else:
                        qui = st.text_input("Assigné à (Aucun employé connecté pour l'instant, tapez son nom)")
                with col2:
                    temps = st.text_input("Temps approximatif (ex: 2h30, 1j)")
                    action = st.text_area("Intitulé / Travail à réaliser")
                
                if st.form_submit_button("Inscrire au planning"):
                    if qui and action:
                        now_brute = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        cursor.execute(
                            "INSERT INTO planning (num_tache, assigne_a, intitule, temps_estime, date_realisation, date_creation_brute) VALUES (?, ?, ?, ?, ?, ?)",
                            (num_t, qui, action, temps, "En cours ⏳", now_brute)
                        )
                        conn.commit()
                        st.success("Tâche ajoutée avec succès !")
                        st.rerun()
                    else:
                        st.error("Veuillez remplir les champs obligatoires.")

    # Affichage du Tableau
    st.write("### 📅 Tableau de suivi")
    cursor.execute("SELECT id, num_tache, assigne_a, intitule, temps_estime, date_realisation FROM planning")
    taches = cursor.fetchall()
    
    if taches:
        col_h_n, col_h_q, col_h_i, col_h_t, col_h_s, col_h_act = st.columns([1, 2, 4, 2, 2, 2])
        col_h_n.write("**N°**")
        col_h_q.write("**Assigné à**")
        col_h_i.write("**Mission**")
        col_h_t.write("**Temps prévu**")
        col_h_s.write("**Statut / Réalisation**")
        col_h_act.write("**Action**")
        st.write("---")

        for t in taches:
            id_t, num, qui, quoi, temps, statut = t
            
            col_n, col_q, col_i, col_t, col_s, col_act = st.columns([1, 2, 4, 2, 2, 2])
            col_n.write(f"**{num}**")
            col_q.write(qui)
            col_i.write(quoi)
            col_t.write(temps)
            
            if statut == "En cours ⏳":
                col_s.warning(statut)
            else:
                col_s.success(statut)
                
            if statut == "En cours ⏳" and (st.session_state.user == qui or st.session_state.role == "Administrateur"):
                if col_act.button("Fait ✅", key=f"btn_{id_t}"):
                    maintenant = datetime.now().strftime("%d/%m/%Y à %H:%M")
                    cursor.execute("UPDATE planning SET date_realisation = ? WHERE id = ?", (f"Le {maintenant}", id_t))
                    conn.commit()
                    st.toast(f"Tâche {num} validée !")
                    st.rerun()
            else:
                col_act.write("")
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

    # Zone d'affichage des messages
    zone_msg = st.container(height=350)
    with zone_msg:
        if messages:
            for m in messages:
                id_msg, exp, txt, date = m
                
                # Si l'utilisateur est Admin, bouton supprimer à droite
                if st.session_state.role == "Administrateur":
                    col_b_msg, col_b_del = st.columns([9.5, 0.5])
                    with col_b_msg:
                        if exp == st.session_state.user:
                            st.chat_message("user").write(f"**Vous** ({date}) : {txt}")
                        else:
                            st.chat_message("assistant").write(f"**{exp}** ({date}) : {txt}")
                    with col_b_del:
                        if st.button("🗑️", key=f"del_{id_msg}"):
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
            maintenant_heure = datetime.now().strftime("%H:%M")
            now_brute = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute(
                "INSERT INTO tchat (expediteur, destinataire, texte, date_envoi, date_creation_brute) VALUES (?, ?, ?, ?, ?)",
                (st.session_state.user, dest, nouveau_msg.strip(), maintenant_heure, now_brute)
            )
            conn.commit()
            st.rerun()
