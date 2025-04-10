import streamlit as st

# Configuration de la page - DOIT ÊTRE LE PREMIER APPEL STREAMLIT
st.set_page_config(
    page_title="Catalogue des métadonnées",
    page_icon="📊",
    layout="wide"
)

# Titre et description
st.title("Catalogue des métadonnées")
st.write("Recherchez et explorez les métadonnées disponibles pour vos analyses et projets.")

# Afficher un message d'information
st.info("Version minimale pour test de déploiement")

# Section principale
st.markdown("## Données de démonstration")

# Créer un tableau simple avec quelques données
data = [
    {"Nom": "emplois_salaries_2016", "Producteur": "INSEE", "Titre": "Emplois salariés en 2016"},
    {"Nom": "indicateurs_climat_2022", "Producteur": "Météo France", "Titre": "Indicateurs climatiques 2022"},
    {"Nom": "emissions_ges_2021", "Producteur": "Citepa (GES)", "Titre": "Émissions de GES 2021"}
]

# Afficher le tableau
st.dataframe(data, use_container_width=True)

# Pied de page
st.markdown("---")
st.markdown("© 2025 - Système de Gestion des Métadonnées v1.0") 