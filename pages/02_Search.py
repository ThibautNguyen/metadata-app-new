import streamlit as st
import pandas as pd
import json
import os
import glob
import re

# Configuration de la page
st.set_page_config(
    page_title="Recherche de métadonnées",
    page_icon="🔍",
    layout="wide"
)

# Titre et description
st.title("Recherche de métadonnées")
st.write("Recherchez et explorez les métadonnées disponibles.")

# Fonction pour charger toutes les métadonnées
def load_all_metadata(base_dir="SGBD/Metadata"):
    """Charge toutes les métadonnées disponibles"""
    metadata_files = glob.glob(f"{base_dir}/**/*.json", recursive=True)
    all_metadata = []
    
    for file_path in metadata_files:
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
                    
                    all_metadata.append(meta_info)
        except Exception as e:
            st.warning(f"Erreur lors du chargement de {file_path}: {str(e)}")
    
    return all_metadata

# Fonction pour rechercher dans les métadonnées
def search_metadata(metadata_list, search_text="", category=None):
    """Filtre les métadonnées selon les critères de recherche"""
    results = []
    
    search_text = search_text.lower()
    
    for meta in metadata_list:
        # Filtrer par catégorie si spécifiée
        if category and category != "Toutes" and meta.get("category") != category:
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
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier: {str(e)}")
        return None

# Interface utilisateur pour la recherche
st.subheader("Critères de recherche")

# Charger toutes les métadonnées
all_metadata = load_all_metadata()

# Extraire toutes les catégories uniques
categories = ["Toutes"] + sorted(list(set(m.get("category", "Autre") for m in all_metadata)))

# Interface de recherche
col1, col2 = st.columns(2)

with col1:
    search_text = st.text_input("Recherche par mot-clé", 
                              placeholder="Entrez un mot-clé à rechercher...")

with col2:
    selected_category = st.selectbox("Catégorie", categories)

# Bouton de recherche
if st.button("Rechercher") or True:  # Auto-recherche 
    results = search_metadata(all_metadata, search_text, selected_category)
    
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
        
        # Filtrer et renommer les colonnes
        df_display = df_results[columns_to_show].rename(columns=columns_rename)
        
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
            if file_path:
                content = load_metadata_content(file_path)
                
                if content:
                    # Supprimer les métadonnées internes pour l'affichage
                    if "_metadata" in content:
                        content_display = {k: v for k, v in content.items() if k != "_metadata"}
                    else:
                        content_display = content
                    
                    # Déterminer le meilleur format d'affichage
                    if isinstance(content_display, list) and len(content_display) > 0:
                        st.subheader("Contenu (format tableau)")
                        st.dataframe(pd.DataFrame(content_display))
                    else:
                        st.subheader("Contenu (format JSON)")
                        st.json(content_display)
                    
                    # Option pour exporter
                    export_format = st.radio("Exporter sous format:", ["JSON", "CSV"], horizontal=True)
                    
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
                        else:
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
            else:
                st.warning("Chemin de fichier non disponible pour ce résultat.")
