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
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Configuration de la page pour qu'elle apparaisse comme "Catalogue" dans le menu
st.set_page_config(
    page_title="Catalogue des métadonnées",
    page_icon="📊",
    layout="wide"
)

# Masquer "app" du menu latéral et remplacer par "Catalogue"
hide_app_style = """
<style>
    span[data-testid="stSidebarNavLinkText"]:nth-child(1) {
        display: none;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Ajouter "Catalogue" comme premier élément */
    div[data-testid="stSidebarNav"] > ul {
        padding-top: 2rem;
    }
    div[data-testid="stSidebarNav"] > ul::before {
        content: "Catalogue";
        margin-left: 25px;
        font-size: 14px;
        font-weight: 600;
        color: rgba(49, 51, 63, 0.6);
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }
</style>
"""
st.markdown(hide_app_style, unsafe_allow_html=True)

# Titre et description
st.title("Catalogue des métadonnées")
st.write("Recherchez et explorez les métadonnées disponibles pour vos analyses et projets.")

# Configuration GitHub
GITHUB_REPO = "ThibautNguyen/DOCS"
GITHUB_BRANCH = "main"
GITHUB_PATH = "SGBD/Metadata"

# Fonction pour charger toutes les métadonnées
def load_all_metadata():
    """Charge toutes les métadonnées disponibles"""
    metadata_files = []
    
    # Chargement depuis le système de fichiers local
    base_dir = os.path.join(parent_dir, "SGBD", "Metadata")
    
    # Vérifier si le répertoire existe
    if not os.path.exists(base_dir):
        st.warning(f"Le répertoire {base_dir} n'existe pas. Aucune métadonnée n'a été trouvée.")
        return []
    
    # Utiliser un motif plus profond pour explorer tous les sous-dossiers
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                producer = os.path.basename(os.path.dirname(file_path))
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                        # Extraire les informations de métadonnées
                        table_name = os.path.basename(file_path).replace('.json', '')
                        
                        # Déterminer le producteur à partir de l'arborescence
                        rel_path = os.path.relpath(file_path, base_dir)
                        path_parts = rel_path.split(os.sep)
                        producer = path_parts[0] if len(path_parts) > 1 else "Autre"
                        
                        # Créer une structure de métadonnées standard
                        meta_info = {
                            "table_name": table_name,
                            "producer": producer,
                            "file_path": file_path,
                            "title": data.get("title", table_name),
                            "description": data.get("description", ""),
                            "last_updated": data.get("last_updated", "N/A")
                        }
                        
                        metadata_files.append(meta_info)
                except Exception as e:
                    st.warning(f"Erreur lors du chargement de {file_path}: {str(e)}")
    
    # Si aucun fichier n'a été trouvé, essayons d'accéder directement au dossier Metadata
    if not metadata_files:
        st.warning(f"Aucune métadonnée trouvée dans {base_dir}. Vérifiez le chemin du dossier.")
        # Afficher les chemins explorés pour le diagnostic
        st.write(f"Chemin absolu: {os.path.abspath(base_dir)}")
        st.write(f"Dossiers trouvés: {os.listdir(parent_dir) if os.path.exists(parent_dir) else 'Aucun'}")
    
    return metadata_files

# Fonction pour rechercher dans les métadonnées avec filtres
def search_metadata(metadata_list, search_text="", producer=None):
    """Filtre les métadonnées selon les critères de recherche"""
    results = []
    
    search_text = search_text.lower()
    
    for meta in metadata_list:
        # Filtrer par producteur si spécifié
        if producer and producer != "Tous" and meta.get("producer") != producer:
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
def load_metadata_content(file_path):
    """Charge le contenu complet d'un fichier de métadonnées"""
    try:
        # Chargement depuis le système de fichiers local
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier: {str(e)}")
        return None

# Chargement des métadonnées
metadata_list = load_all_metadata()

# Extraire les producteurs uniques
producers = ["Tous"] + sorted(list(set([meta.get("producer", "Autre") for meta in metadata_list])))

# Interface de recherche
st.markdown("## Recherche")

col1, col2 = st.columns([3, 1])

with col1:
    search_text = st.text_input("Rechercher par mot-clé", placeholder="Entrez un terme à rechercher...")

with col2:
    selected_producer = st.selectbox("Filtrer par producteur", producers)

# Afficher le nombre total de métadonnées
st.info(f"Nombre total de métadonnées disponibles : {len(metadata_list)}")

# Appliquer les filtres
filtered_metadata = search_metadata(metadata_list, search_text, selected_producer)

# Affichage des résultats
st.markdown("## Résultats")

if not filtered_metadata:
    st.info("Aucune métadonnée ne correspond à votre recherche.")
else:
    st.success(f"{len(filtered_metadata)} résultat(s) trouvé(s).")
    
    # Tableau des résultats
    results_df = pd.DataFrame([
        {
            "Nom": meta.get("table_name", ""),
            "Producteur": meta.get("producer", ""),
            "Titre": meta.get("title", ""),
            "Dernière mise à jour": meta.get("last_updated", "")
        }
        for meta in filtered_metadata
    ])
    
    # Afficher le tableau avec sélection
    selection = st.dataframe(
        results_df,
        use_container_width=True,
        column_config={
            "Nom": st.column_config.TextColumn("Nom", help="Nom de la table de données"),
            "Producteur": st.column_config.TextColumn("Producteur", help="Organisation qui a produit les données"),
            "Titre": st.column_config.TextColumn("Titre", help="Description courte de la table"),
            "Dernière mise à jour": st.column_config.TextColumn("Dernière mise à jour", help="Date de dernière mise à jour")
        }
    )
    
    # Affichage des détails d'une métadonnée sélectionnée
    st.markdown("## Détails")
    
    metadata_index = st.selectbox("Sélectionnez une métadonnée pour voir les détails", 
                               range(len(filtered_metadata)),
                               format_func=lambda i: filtered_metadata[i].get("title", filtered_metadata[i].get("table_name", "")))
    
    if metadata_index is not None:
        selected_meta = filtered_metadata[metadata_index]
        file_path = selected_meta.get("file_path")
        
        meta_content = load_metadata_content(file_path)
        
        if meta_content:
            st.markdown(f"### {selected_meta.get('title', selected_meta.get('table_name', ''))}")
            
            # Affichage des informations générales
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Informations générales")
                st.markdown(f"**Nom de la table:** {selected_meta.get('table_name', '')}")
                st.markdown(f"**Producteur:** {selected_meta.get('producer', '')}")
                st.markdown(f"**Dernière mise à jour:** {selected_meta.get('last_updated', 'N/A')}")
                
                if meta_content.get("description"):
                    st.markdown("#### Description")
                    st.markdown(meta_content.get("description"))
            
            with col2:
                # Champs supplémentaires
                st.markdown("#### Champs supplémentaires")
                for key, value in meta_content.items():
                    if key not in ["producer", "table_name", "title", "description", "last_updated", "columns", "custom_fields", "data_sample"]:
                        st.markdown(f"**{key}:** {value}")
                
                # Champs personnalisés
                if "custom_fields" in meta_content and meta_content["custom_fields"]:
                    st.markdown("#### Champs personnalisés")
                    for key, value in meta_content["custom_fields"].items():
                        st.markdown(f"**{key}:** {value}")
            
            # Affichage des colonnes si disponibles
            if "columns" in meta_content and meta_content["columns"]:
                st.markdown("#### Structure de la table")
                
                columns_df = pd.DataFrame([
                    {
                        "Nom": col.get("name", ""),
                        "Type": col.get("type", ""),
                        "Description": col.get("description", "")
                    }
                    for col in meta_content["columns"]
                ])
                
                st.dataframe(columns_df, use_container_width=True)
            
            # Affichage d'un échantillon de données si disponible
            if "data_sample" in meta_content and meta_content["data_sample"]:
                st.markdown("#### Échantillon de données")
                
                if isinstance(meta_content["data_sample"], list) and len(meta_content["data_sample"]) > 0:
                    st.dataframe(pd.DataFrame(meta_content["data_sample"]), use_container_width=True)
                elif isinstance(meta_content["data_sample"], dict):
                    st.json(meta_content["data_sample"])

# Section d'aide et informations
with st.expander("Aide et informations"):
    st.markdown("""
    ### Comment utiliser ce catalogue
    
    - **Recherche par mot-clé** : Saisissez un terme dans le champ de recherche pour filtrer les métadonnées.
    - **Filtre par producteur** : Utilisez le menu déroulant pour filtrer par organisation productrice de données.
    - **Consulter les détails** : Cliquez sur une ligne dans le tableau ou utilisez le menu déroulant pour voir les détails.
    
    ### Structure des métadonnées
    
    Les métadonnées sont structurées avec les informations suivantes :
    - **Nom** : Identifiant unique de la table de données
    - **Producteur** : Organisation qui a produit les données
    - **Description** : Explication détaillée des données
    - **Colonnes** : Structure des champs de la table avec types et descriptions
    - **Informations supplémentaires** : Contacts, années, sources, etc.
    """)

# Pied de page
st.markdown("---")
st.markdown("© 2025 - Système de Gestion des Métadonnées v1.0")