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
import requests

# Configuration de la page
st.set_page_config(
    page_title="Saisie des Métadonnées",
    page_icon="📝",
    layout="wide"
)

# Titre et description
st.title("Saisie des Métadonnées")
st.markdown("""
Ce formulaire vous permet de créer des fiches de métadonnées pour vos tables de données.
Vous pouvez soit saisir manuellement les informations, soit importer des données pour détection automatique.
""")

# Fonction pour récupérer les dossiers existants dans GitHub
def get_github_producers():
    """Récupère la liste des producteurs de données"""
    try:
        # Liste prédéfinie de producteurs pour éviter les erreurs d'API rate limit
        default_producers = [
            "INSEE", 
            "Météo France", 
            "Ministère de la Transition Ecologique", 
            "Citepa (GES)", 
            "Sit@del (permis de construire)", 
            "Spallian"
        ]
        
        # En local, on peut essayer d'enrichir cette liste avec le contenu du dossier s'il existe
        local_metadata_dir = os.path.join(os.getcwd(), "SGBD", "Metadata")
        if os.path.exists(local_metadata_dir):
            try:
                # Ajouter les dossiers trouvés localement
                local_producers = [d for d in os.listdir(local_metadata_dir) 
                                  if os.path.isdir(os.path.join(local_metadata_dir, d))]
                # Fusionner les deux listes sans doublons
                all_producers = list(set(default_producers + local_producers))
                return sorted(all_producers)
            except Exception:
                pass
        
        return sorted(default_producers)
    except Exception as e:
        st.warning(f"Erreur lors de la récupération des producteurs: {str(e)}")
        return ["INSEE", "Météo France", "Ministère de la Transition Ecologique", 
                "Citepa (GES)", "Sit@del (permis de construire)", "Spallian"]

# Récupérer les producteurs existants
existing_producers = get_github_producers()

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
def save_metadata(metadata, producer, table_name):
    """Sauvegarde les métadonnées dans les dossiers appropriés et synchronise avec Git"""
    # Créer le chemin de dossier si nécessaire
    base_dir = os.path.join(os.getcwd(), "SGBD", "Metadata")
    producer_dir = os.path.join(base_dir, producer)
    
    # Vérifier si nous sommes en mode déploiement (Streamlit Cloud)
    is_deployed = not os.path.exists(os.path.dirname(base_dir))
    
    if is_deployed:
        # En mode déploiement, simuler la sauvegarde
        st.success(f"Mode démonstration : les métadonnées seraient sauvegardées dans {producer}/{table_name}.json")
        st.info("Dans un environnement de production, les métadonnées seraient synchronisées avec GitHub.")
        
        # Retourner un chemin fictif
        return f"demo_path/{producer}/{table_name}.json"
    
    # Créer les répertoires nécessaires
    os.makedirs(producer_dir, exist_ok=True)
    
    # Créer nom de fichier sécurisé
    safe_name = re.sub(r'[^\w\-\.]', '_', table_name)
    json_path = os.path.join(producer_dir, f"{safe_name}.json")
    txt_path = os.path.join(producer_dir, f"{safe_name}.txt")
    
    # Sauvegarder en format JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        # Ajouter des métadonnées sur le producteur et la table
        metadata["producer"] = producer
        metadata["table_name"] = table_name
        
        # Ajouter la date de création/modification
        metadata["last_updated"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    # Créer aussi un fichier TXT pour une lecture rapide
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(f"Nom de la table: {table_name}\n")
        f.write(f"Producteur: {producer}\n")
        f.write(f"Description: {metadata.get('description', '')}\n")
        f.write(f"Source: {metadata.get('source', '')}\n")
        f.write(f"Année: {metadata.get('year', '')}\n")
        f.write(f"Contact: {metadata.get('contact', '')}\n")
        f.write(f"Date de création: {metadata.get('last_updated', '')}\n\n")
        
        f.write("Colonnes:\n")
        for col in metadata.get('columns', []):
            f.write(f"- {col['name']} ({col['type']}): {col.get('description', '')}\n")
    
    # Synchroniser avec Git si disponible
    try:
        # Vérifier si nous sommes dans un dépôt Git
        git_dir = os.path.join(os.getcwd(), ".git")
        if not os.path.exists(git_dir):
            st.success(f"Métadonnées sauvegardées avec succès dans {json_path}")
            st.info("Le dossier n'est pas un dépôt Git. Les changements ne seront pas synchronisés automatiquement.")
            return json_path
        
        # Synchroniser avec Git
        repo = git.Repo(os.getcwd())
        repo.git.add(json_path)
        repo.git.add(txt_path)
        commit_message = f"Ajout/Mise à jour des métadonnées pour {producer}/{table_name}"
        repo.git.commit('-m', commit_message)
        
        # Pousser les modifications vers GitHub
        try:
            repo.git.push("origin", "main")
            st.success(f"Métadonnées sauvegardées et synchronisées avec GitHub.")
        except Exception as e:
            st.success(f"Métadonnées sauvegardées localement. La synchronisation vers GitHub a échoué: {str(e)}")
            st.info("N'oubliez pas d'exécuter 'git push' pour synchroniser avec GitHub.")
    except Exception as e:
        st.success(f"Métadonnées sauvegardées avec succès dans {json_path} et {txt_path}")
        st.warning(f"Note: La synchronisation Git n'a pas fonctionné. Erreur: {str(e)}")
    
    return json_path

# Initialisation des variables de session
if "columns" not in st.session_state:
    st.session_state["columns"] = []

# Onglets pour les différentes méthodes d'entrée
tab1, tab2, tab3 = st.tabs(["Saisie manuelle", "Aperçu des données", "Télécharger un fichier"])

with tab1:
    st.markdown("### Saisie manuelle des métadonnées")
    st.info("Remplissez tous les champs pour créer une fiche de métadonnées complète.")
    
    # Informations de base pour la saisie manuelle
    manual_name = st.text_input("Nom de la table", help="Nom de la table dans la base de données")
    
    # Sélection du producteur de données
    producer_options = ["Nouveau producteur"] + existing_producers
    producer_selection = st.selectbox("Producteur de données", producer_options)
    
    if producer_selection == "Nouveau producteur":
        new_producer = st.text_input("Nom du nouveau producteur", 
                              help="Exemple: INSEE, Météo France, Ministère de la Transition Ecologique")
        producer = new_producer
    else:
        producer = producer_selection
    
    # Autres champs de saisie manuelle
    manual_title = st.text_input("Titre", help="Titre descriptif du jeu de données")
    manual_description = st.text_area("Description", help="Description détaillée du jeu de données")
    
    # Informations supplémentaires
    col1, col2 = st.columns(2)
    with col1:
        manual_source = st.text_input("Source", help="Source des données")
        manual_year = st.text_input("Année", help="Année des données")
    with col2:
        manual_contact = st.text_input("Contact", help="Personne à contacter pour ces données")
        manual_frequency = st.selectbox("Fréquence de mise à jour", 
                                     ["Annuelle", "Semestrielle", "Trimestrielle", "Mensuelle", "Hebdomadaire", "Journalière", "Temps réel", "Ponctuelle", "Non déterminée"])
    
    # Gestion des champs personnalisés
    st.subheader("Champs personnalisés")
    
    if "custom_fields" not in st.session_state:
        st.session_state["custom_fields"] = []
    
    if st.button("Ajouter un champ personnalisé"):
        st.session_state["custom_fields"].append({"key": "", "value": ""})
    
    for i, field in enumerate(st.session_state["custom_fields"]):
        col1, col2, col3 = st.columns([3, 6, 1])
        with col1:
            st.session_state["custom_fields"][i]["key"] = st.text_input(f"Nom du champ {i+1}", value=field["key"], key=f"key_{i}")
        with col2:
            st.session_state["custom_fields"][i]["value"] = st.text_input(f"Valeur du champ {i+1}", value=field["value"], key=f"value_{i}")
        with col3:
            if st.button("X", key=f"delete_field_{i}"):
                st.session_state["custom_fields"].pop(i)
                st.rerun()
    
    # Bouton de sauvegarde pour la saisie manuelle
    if st.button("Sauvegarder les métadonnées (saisie manuelle)"):
        if not manual_name:
            st.error("Veuillez spécifier un nom pour ce jeu de données")
        elif not producer:
            st.error("Veuillez sélectionner ou saisir un producteur de données")
        else:
            try:
                # Créer le dictionnaire de métadonnées
                manual_metadata = {
                    "title": manual_title,
                    "description": manual_description,
                    "source": manual_source,
                    "year": manual_year,
                    "contact": manual_contact,
                    "frequency": manual_frequency,
                    "columns": st.session_state["columns"],
                    "custom_fields": {field["key"]: field["value"] for field in st.session_state["custom_fields"] if field["key"]}
                }
                
                # Sauvegarder les métadonnées
                file_path = save_metadata(manual_metadata, producer, manual_name)
                st.success(f"Métadonnées sauvegardées avec succès dans {file_path}")
            except Exception as e:
                st.error(f"Erreur lors de la sauvegarde: {str(e)}")

with tab2:
    st.markdown("### Détection automatique depuis un aperçu")
    st.info("Collez un extrait de vos données pour détecter automatiquement la structure.")
    
    # Informations de base pour l'aperçu
    preview_name = st.text_input("Nom du jeu de données (aperçu)", help="Nom unique pour identifier ce jeu de données")
    
    # Sélection du producteur pour l'aperçu
    preview_producer_options = ["Nouveau producteur"] + existing_producers
    preview_producer_selection = st.selectbox("Producteur de données (aperçu)", preview_producer_options)
    
    if preview_producer_selection == "Nouveau producteur":
        preview_new_producer = st.text_input("Nom du nouveau producteur (aperçu)", 
                                    help="Exemple: INSEE, Météo France, Ministère de la Transition Ecologique")
        preview_producer = preview_new_producer
    else:
        preview_producer = preview_producer_selection
    
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
                elif not preview_producer:
                    st.error("Veuillez sélectionner ou saisir un producteur de données")
                else:
                    try:
                        file_path = save_metadata(preview_metadata, preview_producer, preview_name)
                        st.success(f"Métadonnées depuis l'aperçu sauvegardées avec succès dans {file_path}")
                    except Exception as e:
                        st.error(f"Erreur lors de la sauvegarde: {str(e)}")
                
        except Exception as e:
            st.error(f"Erreur lors de l'analyse des données: {str(e)}")

with tab3:
    st.subheader("Téléchargement de fichier")
    
    # Champs pour les informations de base
    upload_name = st.text_input("Nom du jeu de données (fichier)", help="Nom unique pour identifier ce jeu de données")
    
    # Sélection du producteur pour le téléchargement
    upload_producer_options = ["Nouveau producteur"] + existing_producers
    upload_producer_selection = st.selectbox("Producteur de données (fichier)", upload_producer_options)
    
    if upload_producer_selection == "Nouveau producteur":
        upload_new_producer = st.text_input("Nom du nouveau producteur (fichier)", 
                                   help="Exemple: INSEE, Météo France, Ministère de la Transition Ecologique")
        upload_producer = upload_new_producer
    else:
        upload_producer = upload_producer_selection
    
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
                elif not upload_producer:
                    st.error("Veuillez sélectionner ou saisir un producteur de données")
                else:
                    try:
                        file_path = save_metadata(upload_metadata, upload_producer, upload_name)
                        st.success(f"Métadonnées depuis le fichier sauvegardées avec succès dans {file_path}")
                    except Exception as e:
                        st.error(f"Erreur lors de la sauvegarde: {str(e)}")
                
        except Exception as e:
            st.error(f"Erreur lors du chargement du fichier: {str(e)}")

# Section d'informations générales et formulaire
st.markdown("---")
st.markdown("## Colonnes")
st.info("Ajoutez les colonnes de votre table en précisant leur nom, type et description.")

# Utiliser les colonnes détectées si disponibles
if "detected_columns" in st.session_state and st.session_state["detected_columns"]:
    if st.button("Utiliser les colonnes détectées"):
        st.session_state["columns"] = st.session_state["detected_columns"]
        st.rerun()

# Bouton pour ajouter une nouvelle colonne
if st.button("Ajouter une colonne"):
    st.session_state["columns"].append({
        "name": "",
        "type": "varchar",
        "description": ""
    })
    st.rerun()

# Affichage des colonnes existantes
for i, col in enumerate(st.session_state["columns"]):
    cols = st.columns([3, 2, 8, 1])
    with cols[0]:
        st.session_state["columns"][i]["name"] = st.text_input(
            f"Nom {i}",
            value=col["name"],
            key=f"col_name_{i}"
        )
    with cols[1]:
        st.session_state["columns"][i]["type"] = st.selectbox(
            f"Type {i}",
            ["varchar", "integer", "numeric", "boolean", "date", "timestamp", "geometry"],
            index=["varchar", "integer", "numeric", "boolean", "date", "timestamp", "geometry"].index(col["type"]) if col["type"] in ["varchar", "integer", "numeric", "boolean", "date", "timestamp", "geometry"] else 0,
            key=f"col_type_{i}"
        )
    with cols[2]:
        st.session_state["columns"][i]["description"] = st.text_input(
            f"Description {i}",
            value=col.get("description", ""),
            key=f"col_desc_{i}"
        )
    with cols[3]:
        if st.button("X", key=f"delete_col_{i}"):
            st.session_state["columns"].pop(i)
            st.rerun()
