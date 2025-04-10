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

# Configuration de la page - DOIT ÊTRE LE PREMIER APPEL STREAMLIT
st.set_page_config(
    page_title="Catalogue des métadonnées",
    page_icon="📊",
    layout="wide"
)

# Personnaliser le menu latéral - renommer 'app' en 'Catalogue'
st.markdown("""
<style>
    /* Renommer 'app' en 'Catalogue' dans le menu latéral */
    [data-testid="stSidebarNavLinkText"]:contains("app") {
        visibility: hidden;
        position: relative;
    }
    
    [data-testid="stSidebarNavLinkText"]:contains("app")::after {
        content: "Catalogue";
        visibility: visible;
        position: absolute;
        left: 0;
        top: 0;
        color: inherit;
    }
</style>
""", unsafe_allow_html=True)

# Importer le middleware pour la gestion du menu
import middleware

# Titre et description
st.title("Catalogue des métadonnées")
st.write("Recherchez et explorez les métadonnées disponibles pour vos analyses et projets.")

# Déterminer si nous sommes en mode de développement local ou déployé
IS_LOCAL = os.path.exists(os.path.join(os.getcwd(), "SGBD"))

# Fonction pour charger les métadonnées
def load_all_metadata():
    """Charge toutes les métadonnées disponibles"""
    metadata_files = []
    
    # Déterminer le chemin de base
    if IS_LOCAL:
        # Mode développement local
        base_dir = os.path.join(os.getcwd(), "SGBD", "Metadata")
    else:
        # Mode déployé - utiliser des exemples pour démonstration
        st.info("Mode démonstration: certaines métadonnées sont simulées pour présentation.")
        return load_demo_metadata()
    
    # Vérifier si le répertoire existe
    if not os.path.exists(base_dir):
        st.warning(f"Le répertoire {base_dir} n'existe pas. Utilisation du mode démonstration.")
        return load_demo_metadata()
    
    try:
        # Exploration récursive du répertoire
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            
                            # Extraire les informations de métadonnées
                            table_name = os.path.basename(file_path).replace('.json', '')
                            
                            # Déterminer le producteur depuis le chemin
                            rel_path = os.path.relpath(root, base_dir)
                            producer = rel_path.split(os.sep)[0] if os.sep in rel_path else rel_path
                            
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
    except Exception as e:
        st.error(f"Erreur lors de l'exploration des dossiers: {str(e)}")
        return load_demo_metadata()
    
    # Si aucun fichier trouvé, utiliser les données de démonstration
    if not metadata_files:
        st.info("Aucune métadonnée trouvée localement. Utilisation des données de démonstration.")
        return load_demo_metadata()
    
    return metadata_files

# Fonction pour charger des métadonnées de démonstration
def load_demo_metadata():
    """Charge des métadonnées de démonstration pour l'affichage"""
    demo_metadata = [
        {
            "table_name": "emplois_salaries_2016",
            "producer": "INSEE",
            "file_path": "demo_path/INSEE/emplois_salaries_2016.json",
            "title": "Emplois salariés en 2016",
            "description": "Description des emplois salariés en France en 2016 par secteur d'activité.",
            "last_updated": "2023-05-15 14:30:22"
        },
        {
            "table_name": "indicateurs_climat_2022",
            "producer": "Météo France",
            "file_path": "demo_path/Meteo_France/indicateurs_climat_2022.json",
            "title": "Indicateurs climatiques 2022",
            "description": "Relevés des principaux indicateurs climatiques en France pour l'année 2022.",
            "last_updated": "2023-01-10 09:15:45"
        },
        {
            "table_name": "emissions_ges_2021",
            "producer": "Citepa (GES)",
            "file_path": "demo_path/Citepa/emissions_ges_2021.json",
            "title": "Émissions de GES 2021",
            "description": "Inventaire des émissions de gaz à effet de serre en France pour l'année 2021.",
            "last_updated": "2022-11-30 16:45:10"
        },
        {
            "table_name": "permis_construire_2020",
            "producer": "Sit@del (permis de construire)",
            "file_path": "demo_path/Sitadel/permis_construire_2020.json",
            "title": "Permis de construire 2020",
            "description": "Base de données des permis de construire délivrés en 2020.",
            "last_updated": "2021-03-22 11:20:35"
        },
        {
            "table_name": "consommation_energie_2019",
            "producer": "Ministère de la Transition Ecologique",
            "file_path": "demo_path/Ministere_TE/consommation_energie_2019.json",
            "title": "Consommation d'énergie 2019",
            "description": "Données de consommation d'énergie par secteur et par région pour l'année 2019.",
            "last_updated": "2020-09-15 10:05:50"
        }
    ]
    return demo_metadata

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

# Fonction pour charger le contenu d'un fichier de métadonnées
def load_metadata_content(file_path):
    """Charge le contenu complet d'un fichier de métadonnées"""
    # Si c'est un chemin de démonstration, retourner des données de démonstration
    if file_path.startswith("demo_path/"):
        return generate_demo_content(file_path)
    
    try:
        # Chargement depuis le système de fichiers local
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier: {str(e)}")
        return None

# Fonction pour générer du contenu de démonstration pour un fichier de métadonnées
def generate_demo_content(file_path):
    """Génère un contenu de démonstration pour un fichier de métadonnées"""
    # Extraire le producteur et le nom de la table depuis le chemin
    parts = file_path.split('/')
    producer = parts[1]
    table_name = parts[2].replace('.json', '')
    
    # Générer différentes colonnes selon le type de données
    columns = []
    if "emplois" in table_name:
        columns = [
            {"name": "id_emploi", "type": "integer", "description": "Identifiant unique de l'emploi"},
            {"name": "secteur", "type": "varchar", "description": "Secteur d'activité"},
            {"name": "departement", "type": "varchar", "description": "Code du département"},
            {"name": "effectif", "type": "integer", "description": "Nombre d'employés"},
            {"name": "date_creation", "type": "date", "description": "Date de création du poste"}
        ]
    elif "climat" in table_name:
        columns = [
            {"name": "station", "type": "varchar", "description": "Code de la station météo"},
            {"name": "date", "type": "date", "description": "Date de la mesure"},
            {"name": "temperature_max", "type": "numeric", "description": "Température maximale (°C)"},
            {"name": "temperature_min", "type": "numeric", "description": "Température minimale (°C)"},
            {"name": "precipitation", "type": "numeric", "description": "Précipitations (mm)"}
        ]
    elif "ges" in table_name:
        columns = [
            {"name": "secteur", "type": "varchar", "description": "Secteur d'activité"},
            {"name": "type_gaz", "type": "varchar", "description": "Type de gaz à effet de serre"},
            {"name": "emission", "type": "numeric", "description": "Quantité d'émissions (tonnes)"},
            {"name": "annee", "type": "integer", "description": "Année de référence"},
            {"name": "region", "type": "varchar", "description": "Région administrative"}
        ]
    elif "permis" in table_name:
        columns = [
            {"name": "id_permis", "type": "varchar", "description": "Numéro du permis"},
            {"name": "commune", "type": "varchar", "description": "Commune de délivrance"},
            {"name": "type_projet", "type": "varchar", "description": "Type de projet"},
            {"name": "surface", "type": "numeric", "description": "Surface en m²"},
            {"name": "date_depot", "type": "date", "description": "Date de dépôt de la demande"}
        ]
    elif "energie" in table_name:
        columns = [
            {"name": "region", "type": "varchar", "description": "Région administrative"},
            {"name": "secteur", "type": "varchar", "description": "Secteur de consommation"},
            {"name": "type_energie", "type": "varchar", "description": "Type d'énergie"},
            {"name": "consommation", "type": "numeric", "description": "Consommation en kWh"},
            {"name": "annee", "type": "integer", "description": "Année de référence"}
        ]
    
    # Générer un échantillon de données
    data_sample = []
    if len(columns) > 0:
        sample = {}
        for col in columns:
            if col["type"] == "integer":
                sample[col["name"]] = 12345
            elif col["type"] == "numeric":
                sample[col["name"]] = 123.45
            elif col["type"] == "date":
                sample[col["name"]] = "2022-01-01"
            else:
                sample[col["name"]] = "Exemple de valeur"
        data_sample.append(sample)
    
    # Construire le contenu de démonstration
    return {
        "producer": producer,
        "table_name": table_name,
        "title": table_name.replace("_", " ").title(),
        "description": f"Description de démonstration pour {table_name}",
        "source": "Source de démonstration",
        "year": "2022",
        "frequency": "Annuelle",
        "contact": "contact@exemple.fr",
        "columns": columns,
        "data_sample": data_sample,
        "last_updated": "2023-01-01 12:00:00"
    }

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
st.markdown("© 2025 - Système de Gestion des Métadonnées v1.0")import streamlit as st

# Configuration de la page - DOIT ÃŠTRE LE PREMIER APPEL STREAMLIT
st.set_page_config(
    page_title="Catalogue des mÃ©tadonnÃ©es",
    page_icon="ðŸ“Š",
    layout="wide"
)

import pandas as pd
import json
import os
import glob
import re
import sys
import requests
import base64
from io import StringIO, BytesIO

# Importer le middleware pour la gestion du menu
import middleware

# Titre et description
st.title("Catalogue des mÃ©tadonnÃ©es")
st.write("Recherchez et explorez les mÃ©tadonnÃ©es disponibles pour vos analyses et projets.")

# DÃ©terminer si nous sommes en mode de dÃ©veloppement local ou dÃ©ployÃ©
IS_LOCAL = os.path.exists(os.path.join(os.getcwd(), "SGBD"))

# Fonction pour charger les mÃ©tadonnÃ©es
def load_all_metadata():
    """Charge toutes les mÃ©tadonnÃ©es disponibles"""
    metadata_files = []
    
    # DÃ©terminer le chemin de base
    if IS_LOCAL:
        # Mode dÃ©veloppement local
        base_dir = os.path.join(os.getcwd(), "SGBD", "Metadata")
    else:
        # Mode dÃ©ployÃ© - utiliser des exemples pour dÃ©monstration
        st.info("Mode dÃ©monstration: certaines mÃ©tadonnÃ©es sont simulÃ©es pour prÃ©sentation.")
        return load_demo_metadata()
    
    # VÃ©rifier si le rÃ©pertoire existe
    if not os.path.exists(base_dir):
        st.warning(f"Le rÃ©pertoire {base_dir} n'existe pas. Utilisation du mode dÃ©monstration.")
        return load_demo_metadata()
    
    try:
        # Exploration rÃ©cursive du rÃ©pertoire
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            
                            # Extraire les informations de mÃ©tadonnÃ©es
                            table_name = os.path.basename(file_path).replace('.json', '')
                            
                            # DÃ©terminer le producteur depuis le chemin
                            rel_path = os.path.relpath(root, base_dir)
                            producer = rel_path.split(os.sep)[0] if os.sep in rel_path else rel_path
                            
                            # CrÃ©er une structure de mÃ©tadonnÃ©es standard
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
    except Exception as e:
        st.error(f"Erreur lors de l'exploration des dossiers: {str(e)}")
        return load_demo_metadata()
    
    # Si aucun fichier trouvÃ©, utiliser les donnÃ©es de dÃ©monstration
    if not metadata_files:
        st.info("Aucune mÃ©tadonnÃ©e trouvÃ©e localement. Utilisation des donnÃ©es de dÃ©monstration.")
        return load_demo_metadata()
    
    return metadata_files

# Fonction pour charger des mÃ©tadonnÃ©es de dÃ©monstration
def load_demo_metadata():
    """Charge des mÃ©tadonnÃ©es de dÃ©monstration pour l'affichage"""
    demo_metadata = [
        {
            "table_name": "emplois_salaries_2016",
            "producer": "INSEE",
            "file_path": "demo_path/INSEE/emplois_salaries_2016.json",
            "title": "Emplois salariÃ©s en 2016",
            "description": "Description des emplois salariÃ©s en France en 2016 par secteur d'activitÃ©.",
            "last_updated": "2023-05-15 14:30:22"
        },
        {
            "table_name": "indicateurs_climat_2022",
            "producer": "MÃ©tÃ©o France",
            "file_path": "demo_path/Meteo_France/indicateurs_climat_2022.json",
            "title": "Indicateurs climatiques 2022",
            "description": "RelevÃ©s des principaux indicateurs climatiques en France pour l'annÃ©e 2022.",
            "last_updated": "2023-01-10 09:15:45"
        },
        {
            "table_name": "emissions_ges_2021",
            "producer": "Citepa (GES)",
            "file_path": "demo_path/Citepa/emissions_ges_2021.json",
            "title": "Ã‰missions de GES 2021",
            "description": "Inventaire des Ã©missions de gaz Ã  effet de serre en France pour l'annÃ©e 2021.",
            "last_updated": "2022-11-30 16:45:10"
        },
        {
            "table_name": "permis_construire_2020",
            "producer": "Sit@del (permis de construire)",
            "file_path": "demo_path/Sitadel/permis_construire_2020.json",
            "title": "Permis de construire 2020",
            "description": "Base de donnÃ©es des permis de construire dÃ©livrÃ©s en 2020.",
            "last_updated": "2021-03-22 11:20:35"
        },
        {
            "table_name": "consommation_energie_2019",
            "producer": "MinistÃ¨re de la Transition Ecologique",
            "file_path": "demo_path/Ministere_TE/consommation_energie_2019.json",
            "title": "Consommation d'Ã©nergie 2019",
            "description": "DonnÃ©es de consommation d'Ã©nergie par secteur et par rÃ©gion pour l'annÃ©e 2019.",
            "last_updated": "2020-09-15 10:05:50"
        }
    ]
    return demo_metadata

# Fonction pour rechercher dans les mÃ©tadonnÃ©es avec filtres
def search_metadata(metadata_list, search_text="", producer=None):
    """Filtre les mÃ©tadonnÃ©es selon les critÃ¨res de recherche"""
    results = []
    
    search_text = search_text.lower()
    
    for meta in metadata_list:
        # Filtrer par producteur si spÃ©cifiÃ©
        if producer and producer != "Tous" and meta.get("producer") != producer:
            continue
        
        # Filtrer par texte de recherche si spÃ©cifiÃ©
        if search_text:
            # Recherche dans tous les champs de mÃ©tadonnÃ©es
            match_found = False
            for key, value in meta.items():
                if isinstance(value, str) and search_text in value.lower():
                    match_found = True
                    break
            
            if not match_found:
                continue
        
        results.append(meta)
    
    return results

# Fonction pour charger le contenu d'un fichier de mÃ©tadonnÃ©es
def load_metadata_content(file_path):
    """Charge le contenu complet d'un fichier de mÃ©tadonnÃ©es"""
    # Si c'est un chemin de dÃ©monstration, retourner des donnÃ©es de dÃ©monstration
    if file_path.startswith("demo_path/"):
        return generate_demo_content(file_path)
    
    try:
        # Chargement depuis le systÃ¨me de fichiers local
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier: {str(e)}")
        return None

# Fonction pour gÃ©nÃ©rer du contenu de dÃ©monstration pour un fichier de mÃ©tadonnÃ©es
def generate_demo_content(file_path):
    """GÃ©nÃ¨re un contenu de dÃ©monstration pour un fichier de mÃ©tadonnÃ©es"""
    # Extraire le producteur et le nom de la table depuis le chemin
    parts = file_path.split('/')
    producer = parts[1]
    table_name = parts[2].replace('.json', '')
    
    # GÃ©nÃ©rer diffÃ©rentes colonnes selon le type de donnÃ©es
    columns = []
    if "emplois" in table_name:
        columns = [
            {"name": "id_emploi", "type": "integer", "description": "Identifiant unique de l'emploi"},
            {"name": "secteur", "type": "varchar", "description": "Secteur d'activitÃ©"},
            {"name": "departement", "type": "varchar", "description": "Code du dÃ©partement"},
            {"name": "effectif", "type": "integer", "description": "Nombre d'employÃ©s"},
            {"name": "date_creation", "type": "date", "description": "Date de crÃ©ation du poste"}
        ]
    elif "climat" in table_name:
        columns = [
            {"name": "station", "type": "varchar", "description": "Code de la station mÃ©tÃ©o"},
            {"name": "date", "type": "date", "description": "Date de la mesure"},
            {"name": "temperature_max", "type": "numeric", "description": "TempÃ©rature maximale (Â°C)"},
            {"name": "temperature_min", "type": "numeric", "description": "TempÃ©rature minimale (Â°C)"},
            {"name": "precipitation", "type": "numeric", "description": "PrÃ©cipitations (mm)"}
        ]
    elif "ges" in table_name:
        columns = [
            {"name": "secteur", "type": "varchar", "description": "Secteur d'activitÃ©"},
            {"name": "type_gaz", "type": "varchar", "description": "Type de gaz Ã  effet de serre"},
            {"name": "emission", "type": "numeric", "description": "QuantitÃ© d'Ã©missions (tonnes)"},
            {"name": "annee", "type": "integer", "description": "AnnÃ©e de rÃ©fÃ©rence"},
            {"name": "region", "type": "varchar", "description": "RÃ©gion administrative"}
        ]
    elif "permis" in table_name:
        columns = [
            {"name": "id_permis", "type": "varchar", "description": "NumÃ©ro du permis"},
            {"name": "commune", "type": "varchar", "description": "Commune de dÃ©livrance"},
            {"name": "type_projet", "type": "varchar", "description": "Type de projet"},
            {"name": "surface", "type": "numeric", "description": "Surface en mÂ²"},
            {"name": "date_depot", "type": "date", "description": "Date de dÃ©pÃ´t de la demande"}
        ]
    elif "energie" in table_name:
        columns = [
            {"name": "region", "type": "varchar", "description": "RÃ©gion administrative"},
            {"name": "secteur", "type": "varchar", "description": "Secteur de consommation"},
            {"name": "type_energie", "type": "varchar", "description": "Type d'Ã©nergie"},
            {"name": "consommation", "type": "numeric", "description": "Consommation en kWh"},
            {"name": "annee", "type": "integer", "description": "AnnÃ©e de rÃ©fÃ©rence"}
        ]
    
    # GÃ©nÃ©rer un Ã©chantillon de donnÃ©es
    data_sample = []
    if len(columns) > 0:
        sample = {}
        for col in columns:
            if col["type"] == "integer":
                sample[col["name"]] = 12345
            elif col["type"] == "numeric":
                sample[col["name"]] = 123.45
            elif col["type"] == "date":
                sample[col["name"]] = "2022-01-01"
            else:
                sample[col["name"]] = "Exemple de valeur"
        data_sample.append(sample)
    
    # Construire le contenu de dÃ©monstration
    return {
        "producer": producer,
        "table_name": table_name,
        "title": table_name.replace("_", " ").title(),
        "description": f"Description de dÃ©monstration pour {table_name}",
        "source": "Source de dÃ©monstration",
        "year": "2022",
        "frequency": "Annuelle",
        "contact": "contact@exemple.fr",
        "columns": columns,
        "data_sample": data_sample,
        "last_updated": "2023-01-01 12:00:00"
    }

# Chargement des mÃ©tadonnÃ©es
metadata_list = load_all_metadata()

# Extraire les producteurs uniques
producers = ["Tous"] + sorted(list(set([meta.get("producer", "Autre") for meta in metadata_list])))

# Interface de recherche
st.markdown("## Recherche")

col1, col2 = st.columns([3, 1])

with col1:
    search_text = st.text_input("Rechercher par mot-clÃ©", placeholder="Entrez un terme Ã  rechercher...")

with col2:
    selected_producer = st.selectbox("Filtrer par producteur", producers)

# Afficher le nombre total de mÃ©tadonnÃ©es
st.info(f"Nombre total de mÃ©tadonnÃ©es disponibles : {len(metadata_list)}")

# Appliquer les filtres
filtered_metadata = search_metadata(metadata_list, search_text, selected_producer)

# Affichage des rÃ©sultats
st.markdown("## RÃ©sultats")

if not filtered_metadata:
    st.info("Aucune mÃ©tadonnÃ©e ne correspond Ã  votre recherche.")
else:
    st.success(f"{len(filtered_metadata)} rÃ©sultat(s) trouvÃ©(s).")
    
    # Tableau des rÃ©sultats
    results_df = pd.DataFrame([
        {
            "Nom": meta.get("table_name", ""),
            "Producteur": meta.get("producer", ""),
            "Titre": meta.get("title", ""),
            "DerniÃ¨re mise Ã  jour": meta.get("last_updated", "")
        }
        for meta in filtered_metadata
    ])
    
    # Afficher le tableau avec sÃ©lection
    selection = st.dataframe(
        results_df,
        use_container_width=True,
        column_config={
            "Nom": st.column_config.TextColumn("Nom", help="Nom de la table de donnÃ©es"),
            "Producteur": st.column_config.TextColumn("Producteur", help="Organisation qui a produit les donnÃ©es"),
            "Titre": st.column_config.TextColumn("Titre", help="Description courte de la table"),
            "DerniÃ¨re mise Ã  jour": st.column_config.TextColumn("DerniÃ¨re mise Ã  jour", help="Date de derniÃ¨re mise Ã  jour")
        }
    )
    
    # Affichage des dÃ©tails d'une mÃ©tadonnÃ©e sÃ©lectionnÃ©e
    st.markdown("## DÃ©tails")
    
    metadata_index = st.selectbox("SÃ©lectionnez une mÃ©tadonnÃ©e pour voir les dÃ©tails", 
                               range(len(filtered_metadata)),
                               format_func=lambda i: filtered_metadata[i].get("title", filtered_metadata[i].get("table_name", "")))
    
    if metadata_index is not None:
        selected_meta = filtered_metadata[metadata_index]
        file_path = selected_meta.get("file_path")
        
        meta_content = load_metadata_content(file_path)
        
        if meta_content:
            st.markdown(f"### {selected_meta.get('title', selected_meta.get('table_name', ''))}")
            
            # Affichage des informations gÃ©nÃ©rales
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Informations gÃ©nÃ©rales")
                st.markdown(f"**Nom de la table:** {selected_meta.get('table_name', '')}")
                st.markdown(f"**Producteur:** {selected_meta.get('producer', '')}")
                st.markdown(f"**DerniÃ¨re mise Ã  jour:** {selected_meta.get('last_updated', 'N/A')}")
                
                if meta_content.get("description"):
                    st.markdown("#### Description")
                    st.markdown(meta_content.get("description"))
            
            with col2:
                # Champs supplÃ©mentaires
                st.markdown("#### Champs supplÃ©mentaires")
                for key, value in meta_content.items():
                    if key not in ["producer", "table_name", "title", "description", "last_updated", "columns", "custom_fields", "data_sample"]:
                        st.markdown(f"**{key}:** {value}")
                
                # Champs personnalisÃ©s
                if "custom_fields" in meta_content and meta_content["custom_fields"]:
                    st.markdown("#### Champs personnalisÃ©s")
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
            
            # Affichage d'un Ã©chantillon de donnÃ©es si disponible
            if "data_sample" in meta_content and meta_content["data_sample"]:
                st.markdown("#### Ã‰chantillon de donnÃ©es")
                
                if isinstance(meta_content["data_sample"], list) and len(meta_content["data_sample"]) > 0:
                    st.dataframe(pd.DataFrame(meta_content["data_sample"]), use_container_width=True)
                elif isinstance(meta_content["data_sample"], dict):
                    st.json(meta_content["data_sample"])

# Section d'aide et informations
with st.expander("Aide et informations"):
    st.markdown("""
    ### Comment utiliser ce catalogue
    
    - **Recherche par mot-clÃ©** : Saisissez un terme dans le champ de recherche pour filtrer les mÃ©tadonnÃ©es.
    - **Filtre par producteur** : Utilisez le menu dÃ©roulant pour filtrer par organisation productrice de donnÃ©es.
    - **Consulter les dÃ©tails** : Cliquez sur une ligne dans le tableau ou utilisez le menu dÃ©roulant pour voir les dÃ©tails.
    
    ### Structure des mÃ©tadonnÃ©es
    
    Les mÃ©tadonnÃ©es sont structurÃ©es avec les informations suivantes :
    - **Nom** : Identifiant unique de la table de donnÃ©es
    - **Producteur** : Organisation qui a produit les donnÃ©es
    - **Description** : Explication dÃ©taillÃ©e des donnÃ©es
    - **Colonnes** : Structure des champs de la table avec types et descriptions
    - **Informations supplÃ©mentaires** : Contacts, annÃ©es, sources, etc.
    """)

# Pied de page
st.markdown("---")
st.markdown("Â© 2025 - SystÃ¨me de Gestion des MÃ©tadonnÃ©es v1.0") 
