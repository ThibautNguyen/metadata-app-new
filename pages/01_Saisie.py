import streamlit as st
import pandas as pd
import json
import os
import datetime

# Configuration de la page
st.set_page_config(
    page_title="Saisie des métadonnées",
    page_icon="📝",
    layout="wide"
)

# Titre et description
st.title("Saisie des métadonnées")
st.write("Utilisez ce formulaire pour ajouter de nouvelles métadonnées.")

# Fonction pour valider les métadonnées
def validate_metadata(metadata):
    """Vérifie que les métadonnées contiennent les champs obligatoires"""
    required_fields = ["name", "category", "title", "description"]
    for field in required_fields:
        if not metadata.get(field):
            return False, f"Le champ '{field}' est obligatoire."
    return True, "Métadonnées valides."

# Fonction pour enregistrer les métadonnées
def save_metadata(metadata):
    """Simule l'enregistrement des métadonnées"""
    metadata["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Afficher un tableau résumant les métadonnées saisies
    st.success("Métadonnées enregistrées avec succès !")
    st.write("Résumé des métadonnées :")
    
    # Créer un DataFrame pour afficher les informations générales
    summary_data = {
        "Propriété": ["Nom", "Catégorie", "Titre", "Description", "Date de mise à jour"],
        "Valeur": [
            metadata.get("name", ""), 
            metadata.get("category", ""),
            metadata.get("title", ""),
            metadata.get("description", ""),
            metadata.get("last_updated", "")
        ]
    }
    
    st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
    
    # Si des champs personnalisés ont été ajoutés, les afficher dans un tableau séparé
    if metadata.get("custom_fields"):
        st.write("Champs personnalisés :")
        custom_fields_data = {
            "Champ": list(metadata["custom_fields"].keys()),
            "Valeur": list(metadata["custom_fields"].values())
        }
        st.dataframe(pd.DataFrame(custom_fields_data), use_container_width=True)
    
    return True

# Formulaire principal
with st.form("metadata_form"):
    st.markdown("### Informations générales")
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Nom de la table de données *", 
                              help="Un nom unique pour identifier la table, sans espaces (ex: 'emplois_2022')")
        
        category = st.selectbox("Catégorie *", 
                                ["Économie", "Environnement", "Démographie", "Transport", "Énergie", "Autre"],
                                help="La catégorie principale des données")
    
    with col2:
        title = st.text_input("Titre *", 
                             help="Un titre descriptif pour la table de données")
        
        description = st.text_area("Description *", 
                                 help="Une description détaillée du contenu de la table")
    
    # Champs personnalisés
    st.markdown("### Champs personnalisés")
    st.write("Ajoutez des informations supplémentaires spécifiques à ces données.")
    
    # Utilisation d'un conteneur pour les champs personnalisés avec une mise en page en colonnes
    custom_fields_container = st.container()
    
    # Dans le conteneur, nous utilisons des colonnes pour organiser les champs
    num_custom_fields = st.number_input("Nombre de champs personnalisés", min_value=0, max_value=10, value=1)
    
    # Création d'un dictionnaire pour stocker les champs personnalisés
    custom_fields = {}
    
    # Si l'utilisateur a indiqué qu'il souhaite ajouter des champs personnalisés
    if num_custom_fields > 0:
        with custom_fields_container:
            # Nous utilisons des colonnes pour organiser les champs
            cols = st.columns(2)
            
            # Pour chaque champ personnalisé
            for i in range(num_custom_fields):
                # Nom du champ personnalisé (dans la première colonne)
                with cols[0]:
                    custom_field_name = st.text_input(f"Nom du champ {i+1}", key=f"custom_field_name_{i}")
                
                # Valeur du champ personnalisé (dans la seconde colonne)
                with cols[1]:
                    custom_field_value = st.text_input(f"Valeur du champ {i+1}", key=f"custom_field_value_{i}")
                
                # Ajouter le champ personnalisé au dictionnaire si un nom est fourni
                if custom_field_name:
                    custom_fields[custom_field_name] = custom_field_value
    
    # Bouton de soumission
    submit_button = st.form_submit_button("Enregistrer les métadonnées")
    
    # Traitement du formulaire
    if submit_button:
        # Construction du dictionnaire de métadonnées
        metadata = {
            "name": name,
            "category": category,
            "title": title,
            "description": description,
            "custom_fields": custom_fields
        }
        
        # Validation des métadonnées
        is_valid, validation_message = validate_metadata(metadata)
        
        # Si les métadonnées sont valides, les enregistrer
        if is_valid:
            save_metadata(metadata)
        else:
            st.error(validation_message)

# Aide et informations
with st.expander("Aide et instructions"):
    st.markdown("""
    ### Comment remplir le formulaire de métadonnées
    
    1. **Informations générales**
       - **Nom de la table** : Identifiant unique pour la table, sans espaces ni caractères spéciaux
       - **Catégorie** : Catégorie principale à laquelle appartiennent les données
       - **Titre** : Titre descriptif de la table (peut contenir des espaces)
       - **Description** : Description détaillée du contenu des données
       
    2. **Champs personnalisés**
       - Ajoutez autant de champs personnalisés que nécessaire pour décrire vos données
       - Exemples de champs personnalisés : Source, Période, Fréquence, Contact, Méthodologie, etc.
       
    3. **Validation et enregistrement**
       - Tous les champs marqués d'un astérisque (*) sont obligatoires
       - Assurez-vous que le nom de la table est unique
       - Une fois le formulaire soumis, les métadonnées seront validées et enregistrées
    """)

# Pied de page
st.markdown("---")
st.markdown("© 2025 - Système de Gestion des Métadonnées v1.0")
