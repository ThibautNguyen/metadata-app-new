import streamlit as st

# Configuration de la page - DOIT ÊTRE LE PREMIER APPEL STREAMLIT
st.set_page_config(
    page_title="Catalogue des métadonnées",
    page_icon="📊",
    layout="wide"
)

# Importer Catalogue.py
import Catalogue 