import streamlit as st
import pandas as pd
import json
import os
import datetime
import re
from io import StringIO
import csv

# Configuration de la page
st.set_page_config(
    page_title="Saisie des métadonnées",
    page_icon="📝",
    layout="wide"
)

# Titre et description
st.title("Saisie des métadonnées")
st.write("Utilisez ce formulaire pour ajouter ou modifier des métadonnées.")

# Fonction pour détecter automatiquement le type de données
def detect_data_type(data_content):
    """Détecte automatiquement le type de données (CSV, JSON, etc.)"""
    data_content = data_content.strip()
    
    # Détection JSON
    if (data_content.startswith('{') and data_content.endswith('}')) or \
       (data_content.startswith('[') and data_content.endswith(']')):
        try:
            json.loads(data_content)
            return "json"
        except:
            pass
    
    # Détection CSV
    try:
        df = pd.read_csv(StringIO(data_content), sep=None, engine='python')
        if len(df.columns) > 1:
            return "csv"
    except:
        pass
    
    # Détection texte tabulé
    if '\t' in data_content:
        lines = data_content.split('\n')
        if len(lines) > 1 and '\t' in lines[0]:
            return "tsv"
    
    # Par défaut, format texte
    return "text"

# Fonction pour convertir les données en format standard
def convert_data(data_content, data_type):
    """Convertit les données au format standard pour le stockage"""
    if data_type == "json":
        return json.loads(data_content)
    
    elif data_type in ["csv", "tsv"]:
        separator = ',' if data_type == "csv" else '\t'
        df = pd.read_csv(StringIO(data_content), sep=separator)
        return df.to_dict(orient="records")
    
    else:  # format texte
        lines = data_content.strip().split('\n')
        return {"content": lines}

# Fonction pour sauvegarder les métadonnées
def save_metadata(metadata, name, category):
    """Sauvegarde les métadonnées dans les dossiers appropriés"""
    # Créer le chemin de dossier si nécessaire
    base_dir = "SGBD/Metadata"
    category_dir = os.path.join(base_dir, category)
    
    os.makedirs(category_dir, exist_ok=True)
    
    # Créer nom de fichier sécurisé
    safe_name = re.sub(r'[^\w\-\.]', '_', name)
    file_path = os.path.join(category_dir, f"{safe_name}.json")
    
    # Ajouter date et heure de création/modification
    metadata["_metadata"] = {
        "name": name,
        "category": category,
        "last_modified": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Sauvegarder en format JSON
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    return file_path

# Interface utilisateur pour la saisie des métadonnées
st.subheader("Informations générales")
col1, col2 = st.columns(2)

with col1:
    metadata_name = st.text_input("Nom du jeu de données", help="Nom unique pour identifier ce jeu de données")
    
with col2:
    # Catégories disponibles (à adapter selon vos besoins)
    categories = ["Clients", "Produits", "Ventes", "Finance", "Ressources", "Autre"]
    metadata_category = st.selectbox("Catégorie", categories)

# Section pour la saisie des données
st.subheader("Données")
input_method = st.radio(
    "Méthode de saisie",
    ["Coller du texte", "Télécharger un fichier", "Saisie manuelle"],
    horizontal=True
)

metadata_content = {}

if input_method == "Coller du texte":
    data_content = st.text_area("Collez vos données ici (CSV, JSON, texte tabulé, etc.)", height=200)
    
    if data_content:
        data_type = detect_data_type(data_content)
        st.info(f"Format détecté: {data_type.upper()}")
        
        try:
            metadata_content = convert_data(data_content, data_type)
            st.success("Données analysées avec succès!")
            
            # Aperçu des données
            st.subheader("Aperçu")
            if isinstance(metadata_content, list) and len(metadata_content) > 0:
                st.dataframe(pd.DataFrame(metadata_content).head(5))
            elif isinstance(metadata_content, dict):
                st.json(metadata_content)
        except Exception as e:
            st.error(f"Erreur lors de l'analyse des données: {str(e)}")

elif input_method == "Télécharger un fichier":
    uploaded_file = st.file_uploader("Choisissez un fichier", type=["csv", "json", "txt", "tsv"])
    
    if uploaded_file is not None:
        try:
            # Déterminer le type de fichier
            file_type = uploaded_file.name.split('.')[-1].lower()
            
            if file_type == "json":
                metadata_content = json.load(uploaded_file)
                st.success("Fichier JSON chargé avec succès!")
                
            elif file_type in ["csv", "tsv"]:
                separator = ',' if file_type == "csv" else '\t'
                df = pd.read_csv(uploaded_file, sep=separator)
                metadata_content = df.to_dict(orient="records")
                st.success(f"Fichier {file_type.upper()} chargé avec succès!")
                
                # Aperçu des données
                st.subheader("Aperçu")
                st.dataframe(df.head(5))
                
            elif file_type == "txt":
                content = uploaded_file.read().decode("utf-8")
                data_type = detect_data_type(content)
                metadata_content = convert_data(content, data_type)
                st.success(f"Fichier texte chargé et interprété comme {data_type.upper()}")
            
        except Exception as e:
            st.error(f"Erreur lors du chargement du fichier: {str(e)}")

elif input_method == "Saisie manuelle":
    st.write("Entrez vos données manuellement:")
    
    # Interface dynamique pour la saisie manuelle
    manual_data = {}
    
    # Champs prédéfinis (à adapter selon vos besoins)
    manual_data["title"] = st.text_input("Titre")
    manual_data["description"] = st.text_area("Description")
    
    # Champs dynamiques
    st.subheader("Champs supplémentaires")
    
    col1, col2 = st.columns(2)
    custom_fields = {}
    
    # Option pour ajouter des champs personnalisés
    add_field = st.checkbox("Ajouter des champs personnalisés")
    
    if add_field:
        with st.container():
            field_name = st.text_input("Nom du champ")
            field_value = st.text_input("Valeur")
            
            if st.button("Ajouter ce champ"):
                if field_name and field_name not in manual_data:
                    custom_fields[field_name] = field_value
                    st.success(f"Champ '{field_name}' ajouté!")
    
    # Afficher les champs personnalisés
    if custom_fields:
        st.subheader("Champs personnalisés ajoutés")
        for name, value in custom_fields.items():
            st.text(f"{name}: {value}")
    
    # Combiner les données
    manual_data.update(custom_fields)
    metadata_content = manual_data

# Bouton de sauvegarde
if st.button("Sauvegarder les métadonnées"):
    if not metadata_name:
        st.error("Veuillez spécifier un nom pour ce jeu de données")
    elif not metadata_content:
        st.error("Aucune donnée à sauvegarder")
    else:
        try:
            file_path = save_metadata(metadata_content, metadata_name, metadata_category)
            st.success(f"Métadonnées sauvegardées avec succès dans {file_path}")
        except Exception as e:
            st.error(f"Erreur lors de la sauvegarde: {str(e)}")
