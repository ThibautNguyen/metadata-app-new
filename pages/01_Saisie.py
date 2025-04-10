import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="Saisie des métadonnées",
    page_icon="📝",
    layout="wide"
)

# Titre et description
st.title("Saisie des métadonnées")
st.write("Utilisez ce formulaire pour ajouter de nouvelles métadonnées.")

# Version simplifiée du formulaire
with st.form("metadata_form"):
    st.markdown("### Informations générales")
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Nom de la table de données *")
        category = st.selectbox("Catégorie *", 
                                ["Économie", "Environnement", "Démographie", "Transport", "Énergie", "Autre"])
    
    with col2:
        title = st.text_input("Titre *")
        description = st.text_area("Description *")
    
    # Bouton de soumission
    submit_button = st.form_submit_button("Enregistrer les métadonnées")
    
    # Traitement du formulaire
    if submit_button:
        st.success("Métadonnées enregistrées avec succès !")
        st.json({
            "name": name,
            "category": category,
            "title": title,
            "description": description,
            "date": "2025-04-10"
        })

# Pied de page
st.markdown("---")
st.markdown("© 2025 - Système de Gestion des Métadonnées v1.0")
