import streamlit as st
import pandas as pd
import json
import os
import datetime
import re
from io import StringIO
import csv
import sys
import git

# Ajout du chemin pour les modules personnalisés
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

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

# Fonction pour détecter automatiquement les colonnes depuis un aperçu des données
def detect_columns_from_data(data_preview):
    try:
        # Essayer de détecter le format (CSV, TSV, etc.)
        if ";" in data_preview:
            delimiter = ";"
        elif "\t" in data_preview:
            delimiter = "\t"
        else:
            delimiter = ","
        
        # Lire les données
        df = pd.read_csv(StringIO(data_preview), delimiter=delimiter)
        
        # Créer un dictionnaire pour chaque colonne
        columns = []
        for col in df.columns:
            col_type = "varchar"
            # Déterminer le type de données
            if pd.api.types.is_numeric_dtype(df[col]):
                if all(df[col].dropna().apply(lambda x: int(x) == x if pd.notnull(x) else True)):
                    col_type = "integer"
                else:
                    col_type = "numeric"
            elif pd.api.types.is_datetime64_dtype(df[col]):
                col_type = "timestamp"
            elif pd.api.types.is_bool_dtype(df[col]):
                col_type = "boolean"
            
            columns.append({
                "name": col,
                "type": col_type,
                "description": ""
            })
        
        return columns
    except Exception as e:
        st.error(f"Erreur lors de la détection des colonnes: {str(e)}")
        return []

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
    """Sauvegarde les métadonnées dans les dossiers appropriés et synchronise avec Git"""
    # Créer le chemin de dossier si nécessaire
    base_dir = os.path.join(parent_dir, "SGBD", "Metadata")
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
    
    # Créer aussi un fichier TXT pour une lecture rapide
    txt_path = os.path.join(category_dir, safe_name)
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(f"Nom: {name}\n")
        f.write(f"Catégorie: {category}\n")
        f.write(f"Dernière modification: {metadata['_metadata']['last_modified']}\n\n")
        
        # Écriture des autres métadonnées
        for key, value in metadata.items():
            if key != "_metadata":
                if isinstance(value, dict):
                    f.write(f"{key}:\n")
                    for k, v in value.items():
                        f.write(f"  {k}: {v}\n")
                elif isinstance(value, list):
                    f.write(f"{key}:\n")
                    for item in value:
                        if isinstance(item, dict):
                            for k, v in item.items():
                                f.write(f"  {k}: {v}\n")
                        else:
                            f.write(f"  - {item}\n")
                else:
                    f.write(f"{key}: {value}\n")
    
    # Synchroniser avec Git si disponible
    try:
        repo = git.Repo(parent_dir)
        repo.git.add(file_path)
        repo.git.add(txt_path)
        commit_message = f"Ajout/Mise à jour des métadonnées pour {category}/{name}"
        repo.git.commit('-m', commit_message)
        st.success(f"Métadonnées sauvegardées et ajoutées à Git. N'oubliez pas de faire un 'git push' pour synchroniser.")
    except Exception as e:
        st.success(f"Métadonnées sauvegardées avec succès dans {file_path} et {txt_path}")
        st.warning(f"Note: La synchronisation Git n'a pas fonctionné. Erreur: {str(e)}")
    
    return file_path

# Initialisation des variables de session
if "columns" not in st.session_state:
    st.session_state["columns"] = []

# Onglets pour les différentes méthodes d'entrée
tab1, tab2, tab3 = st.tabs(["Saisie manuelle", "Aperçu des données", "Télécharger un fichier"])

with tab1:
    # Interface utilisateur pour la saisie des métadonnées
    st.subheader("Informations générales")
    col1, col2 = st.columns(2)

    with col1:
        metadata_name = st.text_input("Nom du jeu de données", help="Nom unique pour identifier ce jeu de données")
        
    with col2:
        # Catégories disponibles (à adapter selon vos besoins)
        categories = ["Clients", "Produits", "Ventes", "Finance", "Ressources", "Autre"]
        metadata_category = st.selectbox("Catégorie", categories)

    # Interface dynamique pour la saisie manuelle
    manual_data = {}
    
    # Champs prédéfinis
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
    
    # Bouton de sauvegarde pour l'onglet saisie manuelle
    if st.button("Sauvegarder les métadonnées (saisie manuelle)"):
        if not metadata_name:
            st.error("Veuillez spécifier un nom pour ce jeu de données")
        elif not manual_data:
            st.error("Aucune donnée à sauvegarder")
        else:
            try:
                file_path = save_metadata(manual_data, metadata_name, metadata_category)
                st.success(f"Métadonnées sauvegardées avec succès dans {file_path}")
            except Exception as e:
                st.error(f"Erreur lors de la sauvegarde: {str(e)}")

with tab2:
    st.subheader("Détection depuis un aperçu des données")
    
    # Champs pour les informations de base
    preview_name = st.text_input("Nom du jeu de données (aperçu)", help="Nom unique pour identifier ce jeu de données")
    preview_category = st.selectbox("Catégorie (aperçu)", categories)
    
    data_content = st.text_area("Collez vos données ici (CSV, JSON, texte tabulé, etc.)", height=200)
    
    preview_metadata = {}
    
    if data_content:
        data_type = detect_data_type(data_content)
        st.info(f"Format détecté: {data_type.upper()}")
        
        try:
            # Détecter les colonnes si format tabulaire
            if data_type in ["csv", "tsv"]:
                detected_columns = detect_columns_from_data(data_content)
                if detected_columns:
                    st.success(f"{len(detected_columns)} colonnes détectées!")
                    st.subheader("Structure détectée:")
                    
                    # Afficher les colonnes en tableau
                    col_data = []
                    for col in detected_columns:
                        col_data.append({"Nom": col["name"], "Type": col["type"], "Description": col["description"]})
                    
                    st.table(pd.DataFrame(col_data))
                    
                    # Ajouter les colonnes aux métadonnées
                    preview_metadata["columns"] = detected_columns
            
            # Convertir et afficher un aperçu
            metadata_content = convert_data(data_content, data_type)
            st.success("Données analysées avec succès!")
            
            # Aperçu des données
            st.subheader("Aperçu")
            if isinstance(metadata_content, list) and len(metadata_content) > 0:
                st.dataframe(pd.DataFrame(metadata_content).head(5))
                preview_metadata["data_sample"] = metadata_content[:5]  # Garder un échantillon
            elif isinstance(metadata_content, dict):
                st.json(metadata_content)
                preview_metadata = {**preview_metadata, **metadata_content}
            
            # Bouton de sauvegarde pour l'aperçu
            if st.button("Sauvegarder les métadonnées (aperçu)"):
                if not preview_name:
                    st.error("Veuillez spécifier un nom pour ce jeu de données")
                else:
                    try:
                        file_path = save_metadata(preview_metadata, preview_name, preview_category)
                        st.success(f"Métadonnées depuis l'aperçu sauvegardées avec succès dans {file_path}")
                    except Exception as e:
                        st.error(f"Erreur lors de la sauvegarde: {str(e)}")
                
        except Exception as e:
            st.error(f"Erreur lors de l'analyse des données: {str(e)}")

with tab3:
    st.subheader("Téléchargement de fichier")
    
    # Champs pour les informations de base
    upload_name = st.text_input("Nom du jeu de données (fichier)", help="Nom unique pour identifier ce jeu de données")
    upload_category = st.selectbox("Catégorie (fichier)", categories)
    
    uploaded_file = st.file_uploader("Choisissez un fichier", type=["csv", "json", "txt", "tsv", "xlsx"])
    
    upload_metadata = {}
    
    if uploaded_file is not None:
        try:
            # Déterminer le type de fichier
            file_type = uploaded_file.name.split('.')[-1].lower()
            
            if file_type == "json":
                upload_metadata = json.load(uploaded_file)
                st.success("Fichier JSON chargé avec succès!")
                st.json(upload_metadata)
                
            elif file_type in ["csv", "tsv"]:
                separator = ',' if file_type == "csv" else '\t'
                df = pd.read_csv(uploaded_file, sep=separator)
                
                # Détecter les types de colonnes
                columns = []
                for col in df.columns:
                    col_type = "varchar"
                    # Déterminer le type de données
                    if pd.api.types.is_numeric_dtype(df[col]):
                        if all(df[col].dropna().apply(lambda x: int(x) == x if pd.notnull(x) else True)):
                            col_type = "integer"
                        else:
                            col_type = "numeric"
                    elif pd.api.types.is_datetime64_dtype(df[col]):
                        col_type = "timestamp"
                    elif pd.api.types.is_bool_dtype(df[col]):
                        col_type = "boolean"
                    
                    columns.append({
                        "name": col,
                        "type": col_type,
                        "description": ""
                    })
                
                upload_metadata["columns"] = columns
                upload_metadata["data_sample"] = df.head(5).to_dict(orient="records")
                
                st.success(f"Fichier {file_type.upper()} chargé avec succès!")
                
                # Aperçu des données
                st.subheader("Aperçu")
                st.dataframe(df.head(5))
                
                # Structure des colonnes
                st.subheader("Structure détectée:")
                col_data = []
                for col in columns:
                    col_data.append({"Nom": col["name"], "Type": col["type"], "Description": col["description"]})
                
                st.table(pd.DataFrame(col_data))
                
            elif file_type == "xlsx":
                df = pd.read_excel(uploaded_file)
                
                # Détecter les types de colonnes (même logique que pour CSV)
                columns = []
                for col in df.columns:
                    col_type = "varchar"
                    if pd.api.types.is_numeric_dtype(df[col]):
                        if all(df[col].dropna().apply(lambda x: int(x) == x if pd.notnull(x) else True)):
                            col_type = "integer"
                        else:
                            col_type = "numeric"
                    elif pd.api.types.is_datetime64_dtype(df[col]):
                        col_type = "timestamp"
                    elif pd.api.types.is_bool_dtype(df[col]):
                        col_type = "boolean"
                    
                    columns.append({
                        "name": col,
                        "type": col_type,
                        "description": ""
                    })
                
                upload_metadata["columns"] = columns
                upload_metadata["data_sample"] = df.head(5).to_dict(orient="records")
                
                st.success("Fichier Excel chargé avec succès!")
                
                # Aperçu des données
                st.subheader("Aperçu")
                st.dataframe(df.head(5))
                
                # Structure des colonnes
                st.subheader("Structure détectée:")
                col_data = []
                for col in columns:
                    col_data.append({"Nom": col["name"], "Type": col["type"], "Description": col["description"]})
                
                st.table(pd.DataFrame(col_data))
                
            elif file_type == "txt":
                content = uploaded_file.read().decode("utf-8")
                data_type = detect_data_type(content)
                upload_metadata = convert_data(content, data_type)
                st.success(f"Fichier texte chargé et interprété comme {data_type.upper()}")
                
                # Aperçu
                if isinstance(upload_metadata, list):
                    st.dataframe(pd.DataFrame(upload_metadata).head(5))
                else:
                    st.json(upload_metadata)
            
            # Bouton de sauvegarde pour le téléchargement
            if st.button("Sauvegarder les métadonnées (fichier)"):
                if not upload_name:
                    st.error("Veuillez spécifier un nom pour ce jeu de données")
                else:
                    try:
                        file_path = save_metadata(upload_metadata, upload_name, upload_category)
                        st.success(f"Métadonnées depuis le fichier sauvegardées avec succès dans {file_path}")
                    except Exception as e:
                        st.error(f"Erreur lors de la sauvegarde: {str(e)}")
                
        except Exception as e:
            st.error(f"Erreur lors du chargement du fichier: {str(e)}")
