import streamlit as st
import requests
import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Hub Entreprise Pro", page_icon="📱", layout="wide")

VOTRE_LIEN_ACTUEL = "https://maupu45.streamlit.app"

# --- INJECTION CSS PREMIUM & ULTRA-ADAPTATIVE ---\n
st.markdown("""
<style>
/* Reset et utilitaires */
.mob-only { display: none; }
.pc-only { display: block; }

/* Force le centrage parfait de TOUS les boutons Streamlit dans leurs colonnes respectives */
div[data-testid=\"stHorizontalBlock\"] div[data-testid=\"stButton\"] {
    display: flex !important;
    justify-content: center !important;
    width: 100% !important;
}

/* --- 🌟 STYLISATION DESIGN PROFESSIONNEL (LOOK SAAS) --- */

/* 1. Le Bouton d'Action Principal (Fait / Annuler) */
div[data-testid=\"stHorizontalBlock\"]:has(.row-marker) div[data-testid=\"column\"] button:has(div:contains(\"Fait\")),
div[data-testid=\"stHorizontalBlock\"]:has(.row-marker) div[data-testid=\"column\"] button:has(div:contains(\"Annuler\")) {
    background: linear-gradient(135deg, #3b82f6, #1d4ed8) !important;
    color: white !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.5rem 1rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2) !important;
}
div[data-testid=\"stHorizontalBlock\"]:has(.row-marker) div[data-testid=\"column\"] button:has(div:contains(\"Fait\")):hover,
div[data-testid=\"stHorizontalBlock\"]:has(.row-marker) div[data-testid=\"column\"] button:has(div:contains(\"Annuler\")):hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 6px rgba(59, 130, 246, 0.3) !important;
}

/* 2. Le Bouton Supprimer (Poubelle) */
div[data-testid=\"stHorizontalBlock\"]:has(.row-marker) div[data-testid=\"column\"] button:has(div:contains(\"🗑️\")) {
    background-color: #fef2f2 !important;
    color: #dc2626 !important;
    border: 1px solid #fee2e2 !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
}
div[data-testid=\"stHorizontalBlock\"]:has(.row-marker) div[data-testid=\"column\"] button:has(div:contains(\"🗑️\")):hover {
    background-color: #fee2e2 !important;
    color: #b91c1c !important;
    transform: scale(1.05) !important;
}

/* 3. Les boutons Popover (Missions, Commentaires) */
div[data-testid=\"stPopover\"] button {
    background-color: #f8fafc !important;
    color: #334155 !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}
div[data-testid=\"stPopover\"] button:hover {
    background-color: #f1f5f9 !important;
    border-color: #cbd5e1 !important;
}

/* 4. Cartes Métriques Premium */
.custom-card {
    background: white;
    padding: 1.25rem;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    margin-bottom: 1rem;
}
.card-title {
    color: #64748b;
    font-size: 0.875rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.5rem;
}
.card-value {
    color: #0f172a;
    font-size: 1.75rem;
    font-weight: 700;
}

/* 5. Séparateurs de lignes discrets */
.row-divider {
    border-bottom: 1px solid #f1f5f9;
    margin: 0.5rem 0;
}

/* Media Queries pour la réactivité mobile */
@media (max-width: 768px) {
    .pc-only { display: none !important; }
    .mob-only { display: block !important; }
    
    /* Optimisation des formulaires sur mobile */
    div[data-testid=\"column\"] {
        margin-bottom: 0.5rem;
    }
}
</style>
""", unsafe_allow_html=True)

# --- INITIALISATION DE LA BASE DE DONNÉES ---
conn = sqlite3.connect("entreprise.db", check_same_thread=False)
cursor = conn.cursor()

# Table des tâches actives
cursor.execute("""
CREATE TABLE IF NOT EXISTS taches (
    id TEXT PRIMARY KEY,
    assigne TEXT,
    mission TEXT,
    urgence TEXT,
    temps TEXT,
    statut TEXT
)
""")

# SÉCURITÉ : Ajout automatique de la colonne commentaire si elle n'existe pas encore dans la BDD existante
try:
    cursor.execute("ALTER TABLE taches ADD COLUMN commentaire TEXT DEFAULT ''")
    conn.commit()
except sqlite3.OperationalError:
    pass

# Table du tchat en temps réel
cursor.execute("""
CREATE TABLE IF NOT EXISTS tchat (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expediteur TEXT,
    destinataire TEXT,
    texte TEXT,
    date_creation TEXT
)
""")

# Table des archives de tâches
cursor.execute("""
CREATE TABLE IF NOT EXISTS archives_taches (
    id TEXT PRIMARY KEY,
    assigne TEXT,
    mission TEXT,
    urgence TEXT,
    temps TEXT,
    date_archive TEXT
)
""")
conn.commit()

# --- GESTION DU TEMPS (FUSEAU HORAIRE PARIS) ---
tz_paris = ZoneInfo("Europe/Paris")
maintenant_paris = datetime.now(tz_paris)

# --- SÉCURITÉ & ROLES DE L'ÉQUIPE ---
EQUIPE = {
    "Christophe": {"role": "Admin", "code": "Admin45"},
    "Lucas": {"role": "Employé", "code": "Lucas45"},
    "Yanis": {"role": "Employé", "code": "Yanis45"},
    "Mathys": {"role": "Employé", "code": "Mathys45"},
    "Chantal": {"role": "Employé", "code": "Chantal45"},
    "Inès": {"role": "Employé", "code": "Ines45"},
    "Matthieu": {"role": "Employé", "code": "Matthieu45"},
    "Sébastien": {"role": "Employé", "code": "Sebastien45"},
    "Damien": {"role": "Employé", "code": "Damien45"},
    "Jérôme": {"role": "Employé", "code": "Jerome45"}
}

if "authentifie" not in st.session_state:
    st.session_state.authentifie = False
    st.session_state.utilisateur = None
    st.session_state.role = None

# --- ÉCRAN DE CONNEXION ---
if not st.session_state.authentifie:
    st.title("🗂️ Hub Entreprise Connecté")
    st.subheader("Veuillez vous identifier pour accéder aux outils.")
    
    with st.form("form_connexion"):
        nom_saisi = st.selectbox("Sélectionnez votre Prénom", list(EQUIPE.keys()))
        code_saisi = st.text_input("Code Secret d'accès", type="password", help="4 caractères fournis par l'admin")
        bouton_valider = st.form_submit_button("Se connecter au Hub 🚀")
        
        if bouton_valider:
            if EQUIPE[nom_saisi]["code"] == code_saisi:
                st.session_state.authentifie = True
                st.session_state.utilisateur = nom_saisi
                st.session_state.role = EQUIPE[nom_saisi]["role"]
                st.success(f"🔓 Connexion réussie ! Bienvenue {nom_saisi}.")
                st.rerun()
            else:
                st.error("❌ Code secret incorrect. Veuillez réessayer.")
    st.stop()

# --- BARRE LATÉRALE (SIDEBAR) CONTROLES ---
st.sidebar.markdown(f"### 👤 {st.session_state.utilisateur}")
st.sidebar.markdown(f"**Rôle :** `{st.session_state.role}`")

if st.sidebar.button("Se déconnecter 🚪", use_container_width=True):
    st.session_state.authentifie = False
    st.session_state.utilisateur = None
    st.session_state.role = None
    st.rerun()

st.sidebar.markdown("---")

# --- INTERFACE PRINCIPALE : LES ONGLETS ---
onglet_planning, onglet_tchat, onglet_archives = st.tabs([
    "🗓️ Planning Équipe", 
    "💬 Tchat en Direct", 
    "📦 Archives des Tâches"
])

# ==========================================
# 1. ONGLET PLANNING (AVEC COLONNE COMMENTAIRE)
# ==========================================
with onglet_planning:
    st.title("📋 Suivi du Planning Général")
    st.caption(f"Dernière synchronisation : {maintenant_paris.strftime('%d/%m/%Y %H:%M:%S')}")
    
    # --- FORMULAIRE D'AJOUT (ADMIN UNIQUEMENT) ---
    if st.session_state.role == "Admin":
        with st.expander("➕ Créer et assigner une nouvelle tâche"):
            with st.form("form_ajout_tache", clear_on_submit=True):
                c1, c2, c3, c4 = st.columns(4)
                id_tache = c1.text_input("ID Unique (Ex: 042)", help="3 chiffres obligatoires")
                qui_tache = c2.selectbox("Assigner à", ["Tout le monde"] + list(EQUIPE.keys()))
                urg_tache = c3.selectbox("Niveau d'urgence", ["🟢 Faible", "🟠 Important", "🔴 Très urgent"])
                tps_tache = c4.text_input("Temps estimé (Ex: 2h30, 45min)")
                
                txt_tache = st.text_area("Description précise de la mission")
                bouton_creer = st.form_submit_button("Ajouter au planning de l'équipe 🚀")
                
                if bouton_creer:
                    if id_tache and txt_tache:
                        try:
                            cursor.execute(
                                "INSERT INTO taches (id, assigne, mission, urgence, temps, statut, commentaire) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                (id_tache, qui_tache, txt_tache, urg_tache, tps_tache, "🟡 En cours ⌛", "")
                            )
                            conn.commit()
                            st.success(f"✅ Tâche {id_tache} ajoutée avec succès !")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("❌ Cet ID existe déjà. Veuillez en choisir un autre unique.")
                    else:
                        st.error("❌ L'ID et la Description sont obligatoires.")

    # --- CALCUL DES MÉTRIQUES EN TEMPS RÉEL ---
    cursor.execute("SELECT statut, temps FROM taches")
    toutes_taches = cursor.fetchall()
    
    total_taches = len(toutes_taches)
    en_cours = sum(1 for t in toutes_taches if "En cours" in t[0])
    terminees = sum(1 for t in toutes_taches if "Terminé" in t[0])
    
    total_minutes = 0
    for t in toutes_taches:
        temps_str = t[1].lower().strip()
        if "h" in temps_str:
            try:
                parties = temps_str.split("h")
                heures = int(parties[0]) if parties[0] else 0
                minutes = int(parties[1].replace("min", "")) if (len(parties) > 1 and parties[1].strip()) else 0
                total_minutes += (heures * 60) + minutes
            except:
                pass
        elif "min" in temps_str:
            try:
                total_minutes += int(temps_str.replace("min", ""))
            except:
                pass
                
    heures_totale = total_minutes // 60
    minutes_totale = total_minutes % 60
    temps_cumule_str = f"{heures_totale}h{minutes_totale:02d}min" if heures_totale > 0 else f"{minutes_totale}min"

    # Affichage des métriques premium
    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(f'<div class="custom-card"><div class="card-title">📋 Missions Actives</div><div class="card-value">{total_taches}</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="custom-card"><div class="card-title">⌛ En Cours</div><div class="card-value" style="color: #eab308;">{en_cours}</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="custom-card"><div class="card-title">✅ Terminées</div><div class="card-value" style="color: #22c55e;">{terminees}</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="custom-card"><div class="card-title">⏱️ Charge Estimée</div><div class="card-value" style="color: #3b82f6;">{temps_cumule_str}</div></div>', unsafe_allow_html=True)

    # --- AFFICHAGE DU PLANNING ---
    cursor.execute("SELECT id, assigne, mission, urgence, temps, statut, commentaire FROM taches ORDER BY id ASC")
    taches_rows = cursor.fetchall()
    
    if not taches_rows:
        st.info("Aucune tâche planifiée pour le moment. Tout est fluide ! ✨")
    else:
        # --- EN-TÊTE VERSION PC ---
        st.markdown('<div class="pc-only">', unsafe_allow_html=True)
        # NOUVELLE RÉPARTITION DES COLONNES POUR INSERER LE COMMENTAIRE
        col_h_id, col_h_qui, col_h_quoi, col_h_urg, col_h_tps, col_h_stat, col_h_comm, col_h_act, col_h_del = st.columns(
            [0.6, 1.5, 3.2, 1.4, 0.9, 1.6, 2.0, 1.2, 0.8], 
            vertical_alignment="center"
        )
        col_h_id.markdown("**ID**")
        col_h_qui.markdown("**ASSIGNÉ À**")
        col_h_quoi.markdown("**MISSION**")
        col_h_urg.markdown("**URGENCE**")
        col_h_tps.markdown("**TEMPS**")
        col_h_stat.markdown("**STATUT**")
        col_h_comm.markdown("💬 **COMMENTAIRE**") # <-- Nouvelle case En-tête
        col_h_act.markdown("<div style='text-align:center;'><b>ACTION</b></div>", unsafe_allow_html=True)
        col_h_del.markdown("<div style='text-align:center;'><b>SUPPR</b></div>", unsafe_allow_html=True)
        st.markdown('<div class="row-divider"></div></div>', unsafe_allow_html=True)
        
        # --- CORPS DU TABLEAU (LIGNES DYNAMIQUES) ---
        for r in taches_rows:
            id_t, qui, quoi, urg, tps, stat, comm = r
            comm = comm if comm else "" # Sécurité si None
            
            # --- CODE VERSION PC ---
            st.markdown('<div class="pc-only"><div class="row-marker">', unsafe_allow_html=True)
            col_id, col_qui, col_quoi, col_urg, col_tps, col_stat, col_comm, col_act, col_del = st.columns(
                [0.6, 1.5, 3.2, 1.4, 0.9, 1.6, 2.0, 1.2, 0.8], 
                vertical_alignment="center"
            )
            
            col_id.write(f"**{id_t}**")
            col_qui.write(f"👤 {qui}")
            
            with col_quoi:
                texte_court = quoi[:25] + "..." if len(quoi) > 25 else quoi
                with st.popover(texte_court, use_container_width=True):
                    st.markdown("**📄 Détails de la mission :**")
                    st.info(quoi)
                    
            col_urg.write(urg)
            col_tps.write(f"⏱️ {tps}" if tps else "—")
            col_stat.write(stat)
            
            # 🆕 CASE COMMENTAIRE POUR LES EMPLOYÉS
            with col_comm:
                label_comm = f"💬 {comm[:15]}..." if comm else "📝 Laisser un avis"
                with st.popover(label_comm, use_container_width=True):
                    st.markdown(f"**✍️ Remarque employé (Tâche {id_t}) :**")
                    nouveau_comm = st.text_area(
                        "La tâche était trop difficile ? Manque de matériel ? Notez-le ici :", 
                        value=comm, 
                        key=f"pc_comm_{id_t}"
                    )
                    if nouveau_comm != comm:
                        cursor.execute("UPDATE taches SET commentaire = ? WHERE id = ?", (nouveau_comm, id_t))
                        conn.commit()
                        st.toast("Commentaire enregistré ! 💾")
                        st.rerun()
            
            # BOUTONS D'ACTION (FAIT / ANNULER)
            with col_act:
                if "En cours" in stat:
                    if st.button("Fait ✅", key=f"pc_fait_{id_t}", use_container_width=True):
                        cursor.execute("UPDATE taches SET statut = '🟢 Terminé ✅' WHERE id = ?", (id_t,))
                        conn.commit()
                        st.rerun()
                else:
                    if st.button("Annuler ↩️", key=f"pc_annuler_{id_t}", use_container_width=True):
                        cursor.execute("UPDATE taches SET statut = '🟡 En cours ⌛' WHERE id = ?", (id_t,))
                        conn.commit()
                        st.rerun()
                        
            # BOUTON SUPPRIMER (ENVOI AUX ARCHIVES DE TÂCHES)
            with col_del:
                if st.button("🗑️", key=f"pc_del_{id_t}", use_container_width=True):
                    cursor.execute(
                        "INSERT INTO archives_taches (id, assigne, mission, urgence, temps, date_archive) VALUES (?, ?, ?, ?, ?, ?)",
                        (id_t, qui, quoi, urg, tps, maintenant_paris.strftime("%d/%m/%Y %H:%M"))
                    )
                    cursor.execute("DELETE FROM taches WHERE id = ?", (id_t,))
                    conn.commit()
                    st.success(f"Tâche {id_t} envoyée aux archives.")
                    st.rerun()
                    
            st.markdown('</div><div class="row-divider"></div></div>', unsafe_allow_html=True)
            
            # --- CODE VERSION MOBILE (CARDS INDIVIDUELLES) ---
            st.markdown('<div class="mob-only">', unsafe_allow_html=True)
            with st.get_container():
                st.markdown(f"**Mission {id_t}** - {urg} - ⏱️ {tps}")
                st.markdown(f"👤 Assigné à : **{qui}**")
                st.markdown(f"**Statut :** {stat}")
                
                with st.expander("👀 Voir la description complète"):
                    st.write(quoi)
                
                # Commentaire sur Mobile
                mob_nouveau_comm = st.text_area(
                    "💬 Commentaire / Difficultés rencontrées :", 
                    value=comm, 
                    key=f"mob_comm_{id_t}"
                )
                if mob_nouveau_comm != comm:
                    cursor.execute("UPDATE taches SET commentaire = ? WHERE id = ?", (mob_nouveau_comm, id_t))
                    conn.commit()
                    st.rerun()
                
                cm1, cm2 = st.columns(2)
                with cm1:
                    if "En cours" in stat:
                        if st.button("Fait ✅", key=f"mob_fait_{id_t}", use_container_width=True):
                            cursor.execute("UPDATE taches SET statut = '🟢 Terminé ✅' WHERE id = ?", (id_t,))
                            conn.commit()
                            st.rerun()
                    else:
                        if st.button("Annuler ↩️", key=f"mob_annuler_{id_t}", use_container_width=True):
                            cursor.execute("UPDATE taches SET statut = '🟡 En cours ⌛' WHERE id = ?", (id_t,))
                            conn.commit()
                            st.rerun()
                with cm2:
                    if st.button("🗑️ Supprimer", key=f"mob_del_{id_t}", use_container_width=True):
                        cursor.execute(
                            "INSERT INTO archives_taches (id, assigne, mission, urgence, temps, date_archive) VALUES (?, ?, ?, ?, ?, ?)",
                            (id_t, qui, quoi, urg, tps, maintenant_paris.strftime("%d/%m/%Y %H:%M"))
                        )
                        cursor.execute("DELETE FROM taches WHERE id = ?", (id_t,))
                        conn.commit()
                        st.rerun()
            st.markdown('<div style="height:15px; border-bottom:2px dashed #e2e8f0; margin-bottom:15px;"></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 2. ONGLET TCHAT (ZONES DE STOCKAGE NETTOYÉES)
# ==========================================
with onglet_tchat:
    st.title("💬 Messagerie instantanée d'équipe")
    st.caption("Échanges opérationnels en temps réel. Pas de spam inutile.")
    
    # Sélection du destinataire pour le ciblage
    liste_destinataires = ["Tout le monde"] + [nom for nom in EQUIPE.keys() if nom != st.session_state.utilisateur]
    destinataire_choisi = st.selectbox("🎯 Envoyer le message à :", liste_destinataires)
    
    # Formulaire de message
    with st.form("form_tchat", clear_on_submit=True):
        texte_message = st.text_input("Votre message...", placeholder="Ex: Matériel reçu / Retard sur la palette 4...")
        bouton_envoyer = st.form_submit_button("Envoyer ⚡")
        
        if bouton_envoyer and texte_message:
            date_str = maintenant_paris.strftime("%H:%M")
            cursor.execute(
                "INSERT INTO tchat (expediteur, destinataire, texte, date_creation) VALUES (?, ?, ?, ?)",
                (st.session_state.utilisateur, destinataire_choisi, texte_message, date_str)
            )
            conn.commit()
            st.rerun()
            
    # Chargement et filtrage intelligent des messages
    cursor.execute("SELECT expediteur, destinataire, texte, date_creation FROM tchat ORDER BY id DESC LIMIT 50")
    messages_bruts = cursor.fetchall()
    
    messages_filtrés = []
    for m in messages_bruts:
        exp, dest, txt, dt = m
        # On affiche si c'est pour tout le monde, ou si l'utilisateur connecté est impliqué
        if dest == "Tout le monde" or exp == st.session_state.utilisateur or dest == st.session_state.utilisateur:
            messages_filtrés.append(m)
            
    if messages_filtrés:
        st.write("---")
        with st.container(height=350):
            for m in messages_filtrés:
                exp, dest, txt, dt = m
                prefixe = f"📢 **[{dest}]** " if dest != "Tout le monde" else "👥 "
                
                if exp == st.session_state.utilisateur:
                    st.markdown(f"{prefixe}*({dt})* **Moi :** {txt}")
                else:
                    st.markdown(f"{prefixe}*({dt})* **{exp} :** {txt}")
    else:
        st.info("Aucun message récent dans votre fil.")

# ==========================================
# 3. ONGLET ARCHIVES DES TÂCHES (CONSERVÉES)
# ==========================================
with onglet_archives:
    st.title("📦 Historique des Tâches Supprimées / Archivées")
    st.caption("Retrouvez ici toutes les anciennes missions sorties du planning principal.")
    
    cursor.execute("SELECT id, assigne, mission, urgence, temps, date_archive FROM archives_taches ORDER BY date_archive DESC")
    tasks_archived = cursor.fetchall()
    
    if tasks_archived:
        # En-tête de l'archive des tâches
        col_ha_id, col_ha_qui, col_ha_quoi, col_ha_urg, col_ha_tps, col_ha_date, col_ha_rest = st.columns([0.6, 1.5, 3.5, 1.5, 1.0, 1.8, 1.2])
        col_ha_id.markdown("**ID**")
        col_ha_qui.markdown("**ASSIGNÉ À**")
        col_ha_quoi.markdown("**MISSION ARCHIVÉE**")
        col_ha_urg.markdown("**URGENCE**")
        col_ha_tps.markdown("**TEMPS**")
        col_ha_date.markdown("**ARCHIVÉ LE**")
        col_ha_rest.markdown("**RESTAURER**")
        st.markdown("---")
        
        for ta in tasks_archived:
            id_a, qui_a, quoi_a, urg_a, tps_a, date_a = ta
            col_a_id, col_a_qui, col_a_quoi, col_a_urg, col_a_tps, col_a_date, col_a_rest = st.columns([0.6, 1.5, 3.5, 1.5, 1.0, 1.8, 1.2], vertical_alignment="center")
            
            col_a_id.write(f"**{id_a}**")
            col_a_qui.write(qui_a)
            
            with col_a_quoi:
                texte_a_court = quoi_a[:25] + "..." if len(quoi_a) > 25 else quoi_a
                with st.popover(texte_a_court, use_container_width=True):
                    st.write(quoi_a)
                    
            col_a_urg.write(urg_a)
            col_a_tps.write(tps_a if tps_a else "—")
            col_a_date.write(f"📅 {date_a}")
            
            with col_a_rest:
                if st.button("↩️ Recharger", key=f"rest_task_{id_a}", use_container_width=True):
                    cursor.execute(
                        "INSERT INTO taches (id, assigne, mission, urgence, temps, statut, commentaire) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (id_a, qui_a, quoi_a, urg_a, tps_a, "🟡 En cours ⌛", "")
                    )
                    cursor.execute("DELETE FROM archives_taches WHERE id = ?", (id_a,))
                    conn.commit()
                    st.success(f"Tâche {id_a} réintégrée au planning !")
                    st.rerun()
    else:
        st.info("Aucune tâche archivée pour le moment.")

# ==========================================
# GESTION DES CODES D'ACCÈS ET DES COMPTES (ADMIN)
# ==========================================
if st.session_state.role == "Admin":
    st.markdown("---")
    with st.expander("⚙️ Panneau d'Administration - Codes d'Accès"):
        st.subheader("Modifier le code secret d'un utilisateur")
        
        col_adm1, col_adm2 = st.columns(2)
        with col_adm1:
            user_a_modifier = st.selectbox("Choisir l'employé", list(EQUIPE.keys()))
        with col_adm2:
            # CORRECTION FAITE ICI : Remplacement du type="text" déprécié par le champ normal sans argument conflictuel
            nv_code = st.text_input("Nouveau Code Secret", help="Saisissez le nouveau code d'accès (ex: 4 chiffres)")
            
        if st.button("Mettre à jour le code secret 🔐"):
            if nv_code:
                EQUIPE[user_a_modifier]["code"] = nv_code
                st.success(f"✨ Le code d'accès de **{user_a_modifier}** a bien été remplacé par `{nv_code}`.")
            else:
                st.error("❌ Veuillez écrire un code valide avant de valider.")
