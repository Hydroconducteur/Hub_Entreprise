import streamlit as st
import requests

# 1. Configuration de la page
st.set_page_config(page_title="Hub Entreprise", layout="centered")

st.title("🚀 Hub Entreprise")

# 2. Paramètres de connexion
# Remplace par l'URL de ta base telle qu'elle apparaît dans ton dashboard Turso
# Exemple: https://nom-de-ta-base.turso.io
DB_URL = "https://hub-entreprise-hydroconducteur.turso.io"

# On récupère le token via les secrets de Streamlit
# Pour le configurer : Settings > Secrets > DB_TOKEN = "ton_token_ici"
if "DB_TOKEN" in st.secrets:
    TOKEN = st.secrets["DB_TOKEN"]
else:
    st.error("Le token de base de données (DB_TOKEN) est manquant dans les secrets.")
    st.stop()

# 3. Fonction pour interroger la base via l'API HTTP Turso
def query_turso(sql):
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    # Turso utilise un système de pipeline pour les requêtes HTTP
    payload = {"statements": [sql]}
    
    try:
        response = requests.post(f"{DB_URL}/v2/pipeline", json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Erreur de connexion à la base : {e}")
        return None

# 4. Interface utilisateur
st.subheader("Consultation des données")

if st.button("Actualiser les données"):
    # Remplace 'ta_table' par le nom réel de ta table
    resultat = query_turso("SELECT * FROM ta_table LIMIT 10")
    
    if resultat:
        # L'API Turso renvoie les résultats dans une structure spécifique
        # On extrait les résultats de la première requête (index 0)
        st.write("Données reçues :")
        st.json(resultat)
    else:
        st.warning("Aucune donnée trouvée ou erreur de requête.")

st.info("Cette méthode est légère et ne nécessite pas de compilation.")
