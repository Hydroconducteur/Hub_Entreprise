import streamlit as st
import sqlite3
from datetime import datetime, timedelta

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Hub Entreprise", page_icon="📱", layout="wide")

# --- CONNEXION BASE DE DONNÉES ---
conn = sqlite3.connect("entreprise.db", check_same_thread=False)
cursor = conn.cursor()

# Création des tables avec la colonne 'date_creation_brute' pour le nettoyage automatique
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
conn.commit()


# ==========================================
# 🧹 SYSTEME DE NETTOYAGE AUTOMATIQUE (14 JOURS)
# ==========================================
def nettoyer_ancienne_data():
    # Calcul du timestamp d'il y a 14 jours (Format: AAAA-MM-JJ HH:MM:SS)
    il_y_a_deux_semaines = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. Supprime les messages de tchat plus vieux que 2 semaines
    cursor.execute("DELETE FROM tchat WHERE date_creation_brute < ?", (il_y_a_deux_semaines,))
    
    # 2. Supprime uniquement les tâches MARQUÉES COMME FAITES depuis plus de 2 semaines
    # (Les tâches "En cours ⏳" restent affichées même si elles ont été créées il y a plus de 2 semaines)
    cursor.execute("DELETE FROM planning WHERE date_realisation LIKE 'Le %' AND date_creation_brute < ?", (il_y_a_deux_semaines,))
    
    conn.commit()

# Exécution automatique du nettoyage à chaque rafraîchissement ou ouverture de l'application
nettoyer_ancienne_data()


# --- GESTION DE LA SESSION USER ---
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None

# --- BARRE LATÉRALE (CONNEXION & NAVIGATION) ---
with st.sidebar:
    st.title("🔑 Espace Connexion")
    
    if st.session_state.user is None:
        identifiant = st.text_input("Identifiant (Prénom)")
        role = st.selectbox("Votre rôle", ["Employé", "Administrateur"])
        if st.button("Se connecter", use_container_width=True):
            if identifiant.strip() != "":
                st.session_state.user = identifiant.strip().capitalize()
                st.session_state.role = role
                st.rerun()
    else:
        st.success(f"Connecté : {st.session_state.user} ({st.session_state.role})")
        if st.button("Se déconnecter", use_container_width=True):
            st.session_state.user = None
            st.session_state.role = None
            st.rerun()
            
    st.write("---")
    st.title("🗺️ Navigation")
    page = st.radio("Aller vers :", ["📋 Planning de l'équipe", "💬 Zone Tchat"])

# --- EMPECHER L'ACCÈS SANS CONNEXION ---
if st.session_state.user is None:
    st.warning("⚠️ Veuillez entrer votre prénom dans la barre latérale pour accéder à l'application.")
    st.stop()


# ==========================================
# PAGE 1 : LE PLANNING DYNAMIQUE
# ==========================================
if page == "📋 Planning de l'équipe":
    st.title("📋 Planning Global de l'Équipe")
    st.caption("Suivi des tâches en temps réel (Nettoyage automatique des tâches finies après 14 jours).")

    # Formulaire Ajout de Tâche (Réservé à l'Admin)
    if st.session_state.role == "Administrateur":
        with st.expander("➕ Ajouter une nouvelle tâche (Réservé Admin)", expanded=False):
            with st.form("form_tache"):
                col1, col2 = st.columns(2)
                with col1:
                    num_t = st.text_input("N° de tâche", value="001")
                    qui = st.text_input("Assigné à (Prénom de l'employé)")
                with col2:
                    temps = st.text_input("Temps approximatif (ex: 2h30, 1j)")
                    action = st.text_area("Intitulé / Travail à réaliser")
                
                if st.form_submit_button("Inscrire au planning"):
                    if qui and action:
                        now_brute = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        cursor.execute(
                            "INSERT INTO planning (num_tache, assigne_a, intitule, temps_estime, date_realisation, date_creation_brute) VALUES (?, ?, ?, ?, ?, ?)",
                            (num_t, qui.capitalize(), action, temps, "En cours ⏳", now_brute)
                        )
                        conn.commit()
                        st.success("Tâche ajoutée avec succès !")
                        st.rerun()
                    else:
                        st.error("Veuillez remplir au moins l'assignation et l'intitulé.")

    # Affichage du Tableau
    st.write("### 📅 Tableau de suivi")
    cursor.execute("SELECT id, num_tache, assigne_a, intitule, temps_estime, date_realisation FROM planning")
    taches = cursor.fetchall()
    
    if taches:
        # En-têtes du tableau pour une meilleure lisibilité
        col_h_n, col_h_q, col_h_i, col_h_t, col_h_s, col_h_act = st.columns([1, 2, 4, 2, 2, 2])
        col_h_n.write("**N°**")
        col_h_q.write("**Assigné à**")
        col_h_i.write("**Mission**")
        col_h_t.write("**Temps prévu**")
        col_h_s.write("**Statut / Réalisation**")
        col_h_act.write("**Action**")
        st.write("---")

        # Boucle pour afficher chaque ligne
        for t in taches:
            id_t, num, qui, quoi, temps, statut = t
            
            col_n, col_q, col_i, col_t, col_s, col_act = st.columns([1, 2, 4, 2, 2, 2])
            col_n.write(f"**{num}**")
            col_q.write(qui)
            col_i.write(quoi)
            col_t.write(temps)
            
            # Affichage du statut avec couleur adaptée
            if statut == "En cours ⏳":
                col_s.warning(statut)
            else:
                col_s.success(statut)
                
            # Bouton de validation pour l'employé désigné ou l'admin
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
    st.caption("Les messages s'effacent automatiquement au bout de 14 jours.")
    
    # Récupérer dynamiquement la liste des utilisateurs enregistrés pour le tchat privé
    cursor.execute("SELECT DISTINCT assigne_a FROM planning")
    employes = [row[0] for row in cursor.fetchall()]
    if "Admin" not in employes:
        employes.append("Admin")
    if st.session_state.user not in employes:
        employes.append(st.session_state.user)
        
    options_tchat = ["📢 Canal #Général (Tout le monde)"] + [f"🔒 Privé avec {emp}" for emp in employes if emp != st.session_state.user]
    choix_tchat = st.selectbox("Où voulez-vous écrire ?", options_tchat)

    st.write("---")

    # Récupération des messages
    if choix_tchat == "📢 Canal #Général (Tout le monde)":
        st.subheader("📢 Canal #Général")
        cursor.execute("SELECT expediteur, texte, date_envoi FROM tchat WHERE destinataire = 'Tous' ORDER BY id ASC")
        messages = cursor.fetchall()
    else:
        cible = choix_tchat.replace("🔒 Privé avec ", "")
        st.subheader(f"🔒 Discussion privée avec {cible}")
        cursor.execute(
            "SELECT expediteur, texte, date_envoi FROM tchat WHERE (expediteur = ? AND destinataire = ?) OR (expediteur = ? AND destinataire = ?) ORDER BY id ASC",
            (st.session_state.user, cible, cible, st.session_state.user)
        )
        messages = cursor.fetchall()

    # Zone d'affichage des messages sous forme de bulles
    zone_msg = st.container(height=350)
    with zone_msg:
        if messages:
            for m in messages:
                exp, txt, date = m
                if exp == st.session_state.user:
                    st.chat_message("user").write(f"**Vous** ({date}) : {txt}")
                else:
                    st.chat_message("assistant").write(f"**{exp}** ({date}) : {txt}")
        else:
            st.caption("Aucun message dans cette discussion pour le moment...")

    # Formulaire d'envoi du message
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