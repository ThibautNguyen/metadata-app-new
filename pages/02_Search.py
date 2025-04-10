import streamlit as st
import pandas as pd
import json
import os
import glob
import re
import sys
import requests
import base64
from io import StringIO, BytesIO

# Ajout du chemin pour les modules personnalisés
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Configuration de la page
st.set_page_config(
    page_title="Recherche de métadonnées",
    page_icon="🔍",
    layout="wide"
)

# Titre et description
st.title("Recherche de métadonnées")
st.write("Recherchez et explorez les métadonnées disponibles.")

# Configuration GitHub (à placer dans le fichier .streamlit/secrets.toml pour le déploiement)
try:
    # Essayer de charger depuis les secrets (pour le déploiement)
    GITHUB_REPO = st.secrets["github"]["repo"]
    GITHUB_BRANCH = st.secrets["github"]["branch"]
    GITHUB_PATH = st.secrets["github"]["metadata_path"]
except Exception:
    # Fallback vers les valeurs par défaut (pour le développement local)
    GITHUB_REPO = "ThibautNguyen/DOCS"
    GITHUB_BRANCH = "main"
    GITHUB_PATH = "SGBD/Metadata"

# Fonction pour charger toutes les métadonnées
def load_all_metadata(source="local"):
    """Charge toutes les métadonnées disponibles"""
    metadata_files = []
    
    if source == "local":
        # Chargement depuis le système de fichiers local
        base_dir = os.path.join(parent_dir, "SGBD", "Metadata")
        metadata_files_paths = glob.glob(f"{base_dir}/**/*.json", recursive=True)
        
        for file_path in metadata_files_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Extraire les informations de métadonnées
                    if "_metadata" in data:
                        meta_info = data["_metadata"]
                        
                        # Ajouter le chemin du fichier
                        meta_info["file_path"] = file_path
                        
                        # Extraire la catégorie du chemin si non disponible
                        if "category" not in meta_info:
                            parts = file_path.split(os.sep)
                            if len(parts) > 1:
                                meta_info["category"] = parts[-2]
                        
                        metadata_files.append(meta_info)
                    else:
                        # Format de l'ancienne version
                        schema = os.path.basename(os.path.dirname(file_path))
                        table_name = os.path.basename(file_path).replace('.json', '')
                        
                        meta_info = {
                            "name": table_name,
                            "category": schema,
                            "file_path": file_path,
                            "last_modified": "N/A"
                        }
                        metadata_files.append(meta_info)
            except Exception as e:
                st.warning(f"Erreur lors du chargement de {file_path}: {str(e)}")
    
    elif source == "github":
        # Chargement depuis GitHub
        try:
            # Obtenir la liste des fichiers dans le dépôt
            repo_api_url = f"https://api.github.com/repos/{GITHUB_REPO}/git/trees/{GITHUB_BRANCH}?recursive=1"
            response = requests.get(repo_api_url)
            if response.status_code == 200:
                files_data = response.json()
                # Filtrer uniquement les fichiers JSON dans le dossier Metadata
                json_files = [item for item in files_data.get('tree', []) if 
                            item.get('path', '').startswith(GITHUB_PATH) and 
                            item.get('path', '').endswith('.json')]
                
                # Charger chaque fichier JSON
                for file_info in json_files:
                    file_path = file_info.get('path')
                    file_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{file_path}"
                    
                    try:
                        file_response = requests.get(file_url)
                        if file_response.status_code == 200:
                            # Extraire le schéma à partir du chemin
                            path_parts = file_path.split('/')
                            if len(path_parts) > 2:
                                schema = path_parts[-2]
                                table_name = path_parts[-1].replace('.json', '')
                                
                                try:
                                    metadata = file_response.json()
                                    
                                    # Extraire les informations de métadonnées
                                    if "_metadata" in metadata:
                                        meta_info = metadata["_metadata"]
                                    else:
                                        # Format de l'ancienne version
                                        meta_info = {
                                            "name": table_name,
                                            "category": schema,
                                            "last_modified": "N/A"
                                        }
                                    
                                    meta_info["file_path"] = file_path
                                    meta_info["github_url"] = file_url
                                    metadata_files.append(meta_info)
                                except Exception as e:
                                    st.warning(f"Erreur lors de l'analyse du fichier JSON {file_path}: {str(e)}")
                    except Exception as e:
                        st.warning(f"Erreur lors de la lecture du fichier GitHub {file_path}: {str(e)}")
            else:
                st.error(f"Erreur lors de l'accès à GitHub: {response.status_code} - {response.text}")
        except Exception as e:
            st.error(f"Erreur lors de la connexion à GitHub: {str(e)}")
    
    return metadata_files

# Fonction pour rechercher dans les métadonnées avec filtres avancés
def search_metadata(metadata_list, search_text="", category=None, tags=None, date_range=None):
    """Filtre les métadonnées selon les critères de recherche avancés"""
    results = []
    
    search_text = search_text.lower()
    
    for meta in metadata_list:
        # Filtrer par catégorie si spécifiée
        if category and category != "Toutes" and meta.get("category") != category:
            continue
        
        # Filtrer par tags si spécifiés
        if tags and not any(tag in meta.get("tags", []) for tag in tags):
            continue
        
        # Filtrer par date si spécifiée
        if date_range:
            # Format de date attendu: "YYYY-MM-DD"
            last_modified = meta.get("last_modified", "")
            if last_modified and last_modified.split(" ")[0] < date_range[0]:
                continue
            if last_modified and last_modified.split(" ")[0] > date_range[1]:
                continue
        
        # Filtrer par texte de recherche si spécifié
        if search_text:
            # Recherche dans tous les champs de métadonnées
            match_found = False
            for key, value in meta.items():
                if isinstance(value, str) and search_text in value.lower():
                    match_found = True
                    break
            
            if not match_found:
                continue
        
        results.append(meta)
    
    return results

# Fonction pour charger le contenu complet d'un fichier de métadonnées
def load_metadata_content(file_path, is_github_url=False):
    """Charge le contenu complet d'un fichier de métadonnées"""
    try:
        if is_github_url:
            # Chargement depuis GitHub
            response = requests.get(file_path)
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Erreur lors du chargement depuis GitHub: {response.status_code}")
                return None
        else:
            # Chargement depuis le système de fichiers local
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier: {str(e)}")
        return None

# Sélection de la source des métadonnées
data_source = st.radio(
    "Source des métadonnées",
    ["Local", "GitHub"],
    horizontal=True,
    help="Choisissez entre les métadonnées stockées localement ou celles sur GitHub"
)

# Chargement des métadonnées
if data_source == "Local":
    all_metadata = load_all_metadata(source="local")
    st.success(f"Chargement de {len(all_metadata)} fiches de métadonnées depuis le stockage local.")
else:
    with st.spinner("Chargement des métadonnées depuis GitHub..."):
        all_metadata = load_all_metadata(source="github")
    st.success(f"Chargement de {len(all_metadata)} fiches de métadonnées depuis GitHub.")

# Extraire toutes les catégories uniques
categories = ["Toutes"] + sorted(list(set(m.get("category", "Autre") for m in all_metadata)))

# Interface de recherche avec filtres avancés
st.subheader("Critères de recherche")

# Onglets pour recherche simple/avancée
tab1, tab2 = st.tabs(["Recherche simple", "Recherche avancée"])

with tab1:
    col1, col2 = st.columns(2)

    with col1:
        search_text = st.text_input("Recherche par mot-clé", 
                                placeholder="Entrez un mot-clé à rechercher...")

    with col2:
        selected_category = st.selectbox("Catégorie", categories)

with tab2:
    # Recherche avancée avec plus d'options
    adv_search_text = st.text_input("Recherche par mot-clé (avancée)", 
                               placeholder="Entrez un mot-clé à rechercher...")
    
    col1, col2 = st.columns(2)
    
    with col1:
        adv_selected_category = st.selectbox("Catégorie (avancée)", categories)
    
    with col2:
        # Exemple de filtre supplémentaire: date de modification
        use_date_filter = st.checkbox("Filtrer par date de modification")
        
        if use_date_filter:
            date_from = st.date_input("De", value=None)
            date_to = st.date_input("À", value=None)
            
            if date_from and date_to:
                date_range = [str(date_from), str(date_to)]
            else:
                date_range = None
        else:
            date_range = None

# Décider quels paramètres de recherche utiliser
if tab1 and not tab2:  # Si l'onglet Recherche simple est sélectionné
    final_search_text = search_text
    final_category = selected_category
    final_date_range = None
else:  # Si l'onglet Recherche avancée est sélectionné
    final_search_text = adv_search_text
    final_category = adv_selected_category
    final_date_range = date_range

# Bouton de recherche
if st.button("Rechercher") or True:  # Auto-recherche 
    results = search_metadata(all_metadata, final_search_text, final_category, None, final_date_range)
    
    # Afficher les résultats
    st.subheader(f"Résultats ({len(results)} trouvés)")
    
    if not results:
        st.info("Aucun résultat trouvé. Essayez d'autres critères de recherche.")
    else:
        # Convertir les résultats en DataFrame pour un affichage plus propre
        df_results = pd.DataFrame(results)
        
        # Réorganiser et renommer les colonnes
        columns_to_show = ["name", "category", "last_modified"]
        columns_rename = {
            "name": "Nom",
            "category": "Catégorie",
            "last_modified": "Dernière modification"
        }
        
        # Filtrer et renommer les colonnes disponibles
        available_columns = [col for col in columns_to_show if col in df_results.columns]
        df_display = df_results[available_columns].rename(columns={col: columns_rename.get(col, col) for col in available_columns})
        
        # Ajouter un index pour identifier les lignes
        df_display.insert(0, "#", range(1, len(df_display) + 1))
        
        # Afficher le tableau des résultats
        st.dataframe(df_display, use_container_width=True)
        
        # Sélectionner un résultat pour voir les détails
        st.subheader("Détails")
        selected_idx = st.selectbox("Sélectionnez un résultat pour voir les détails", 
                                  range(len(results)),
                                  format_func=lambda i: f"{i+1}. {results[i]['name']}")
        
        if selected_idx is not None:
            selected_result = results[selected_idx]
            
            # Afficher les informations de base
            st.write(f"**Nom:** {selected_result.get('name', 'N/A')}")
            st.write(f"**Catégorie:** {selected_result.get('category', 'N/A')}")
            st.write(f"**Dernière modification:** {selected_result.get('last_modified', 'N/A')}")
            
            # Charger et afficher le contenu complet
            file_path = selected_result.get("file_path")
            github_url = selected_result.get("github_url")
            
            if github_url:
                content = load_metadata_content(github_url, is_github_url=True)
            elif file_path:
                content = load_metadata_content(file_path)
            else:
                content = None
                st.warning("Chemin de fichier non disponible pour ce résultat.")
                
            if content:
                # Supprimer les métadonnées internes pour l'affichage
                if "_metadata" in content:
                    content_display = {k: v for k, v in content.items() if k != "_metadata"}
                else:
                    content_display = content
                
                # Afficher les données en colonnes
                col1, col2 = st.columns([7, 3])
                
                with col1:
                    # Déterminer le meilleur format d'affichage
                    if "columns" in content_display and isinstance(content_display["columns"], list):
                        st.subheader("Structure des données")
                        col_data = []
                        for col in content_display["columns"]:
                            col_data.append({
                                "Nom": col.get("name", "N/A"),
                                "Type": col.get("type", "N/A"),
                                "Description": col.get("description", "")
                            })
                        st.table(pd.DataFrame(col_data))
                    
                    if "data_sample" in content_display and isinstance(content_display["data_sample"], list):
                        st.subheader("Aperçu des données")
                        st.dataframe(pd.DataFrame(content_display["data_sample"]))
                    
                    # Contenu complet
                    st.subheader("Contenu complet")
                    if isinstance(content_display, list) and len(content_display) > 0:
                        st.dataframe(pd.DataFrame(content_display))
                    else:
                        st.json(content_display)
                
                with col2:
                    # Options d'exportation
                    st.subheader("Exporter")
                    export_format = st.radio("Format:", ["JSON", "CSV", "Excel"], horizontal=True)
                    
                    if st.button("Télécharger"):
                        if export_format == "JSON":
                            # Exporter en JSON
                            json_str = json.dumps(content_display, indent=2, ensure_ascii=False)
                            st.download_button(
                                label="Télécharger JSON",
                                data=json_str,
                                file_name=f"{selected_result.get('name', 'data')}.json",
                                mime="application/json"
                            )
                        elif export_format == "CSV":
                            # Exporter en CSV (si possible)
                            try:
                                if isinstance(content_display, list):
                                    df = pd.DataFrame(content_display)
                                elif isinstance(content_display, dict):
                                    # Convertir le dictionnaire en format plat
                                    df = pd.json_normalize(content_display)
                                else:
                                    df = pd.DataFrame([content_display])
                                
                                csv = df.to_csv(index=False)
                                st.download_button(
                                    label="Télécharger CSV",
                                    data=csv,
                                    file_name=f"{selected_result.get('name', 'data')}.csv",
                                    mime="text/csv"
                                )
                            except Exception as e:
                                st.error(f"Impossible de convertir en CSV: {str(e)}")
                        elif export_format == "Excel":
                            # Exporter en Excel (si possible)
                            try:
                                if isinstance(content_display, list):
                                    df = pd.DataFrame(content_display)
                                elif isinstance(content_display, dict):
                                    # Convertir le dictionnaire en format plat
                                    df = pd.json_normalize(content_display)
                                else:
                                    df = pd.DataFrame([content_display])
                                
                                # Créer un buffer pour le fichier Excel
                                output = BytesIO()
                                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                                    df.to_excel(writer, sheet_name='Métadonnées', index=False)
                                
                                excel_data = output.getvalue()
                                st.download_button(
                                    label="Télécharger Excel",
                                    data=excel_data,
                                    file_name=f"{selected_result.get('name', 'data')}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                            except Exception as e:
                                st.error(f"Impossible de convertir en Excel: {str(e)}")
                    
                    # Lien vers la source
                    if github_url:
                        st.subheader("Lien source")
                        github_view_url = github_url.replace("raw.githubusercontent.com", "github.com").replace(f"/{GITHUB_BRANCH}/", "/blob/{GITHUB_BRANCH}/")
                        st.markdown(f"[Voir sur GitHub]({github_view_url})")
                    
                    # Visualisation si applicable
                    if "columns" in content_display:
                        st.subheader("Visualisation")
                        if st.button("Générer un aperçu visuel"):
                            st.warning("Fonctionnalité en développement. Bientôt disponible!")
                            # TODO: Ajouter des visualisations en fonction du type de données
