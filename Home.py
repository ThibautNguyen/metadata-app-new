import streamlit as st
import importlib

# Rediriger vers Catalogue.py
try:
    # Importer le module Catalogue
    catalogue = importlib.import_module("Catalogue")
except Exception as e:
    st.error(f"Erreur lors du chargement du module Catalogue: {str(e)}")
    st.write("Veuillez vérifier que le fichier Catalogue.py existe dans le répertoire de l'application.") 