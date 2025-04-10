import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx
import os

def ensure_visible_pages():
    """Assure que toutes les pages sont visibles dans le menu latéral, y compris la page principale."""
    # Cette fonction sera appelée à chaque chargement de l'application
    # pour s'assurer que le menu contient toujours toutes les pages
    pass  # Streamlit s'occupe désormais de la gestion des pages

# Ajouter une personnalisation au menu latéral
def add_home_button():
    """Ajoute un bouton 'Catalogue' en haut du menu latéral."""
    ctx = get_script_run_ctx()
    if ctx is not None:
        # Vérifier si nous sommes déjà sur la page principale
        is_home = ctx.main_script_path.endswith('app.py')
        current_page = os.path.basename(ctx.main_script_path)
        
        # Ajouter un bouton HTML pour revenir à la page d'accueil si nous ne sommes pas déjà dessus
        if not is_home:
            st.sidebar.markdown("""
            <div style="margin-bottom: 1rem;">
                <a href="/" target="_self" style="
                    display: block;
                    text-decoration: none;
                    color: #262730;
                    padding: 0.5rem 1rem;
                    border-radius: 0.3rem;
                    background-color: #f8f9fa;
                    border: 1px solid #e9ecef;
                    text-align: center;
                    font-weight: 600;
                    margin-top: 1rem;">
                    Retour au Catalogue
                </a>
            </div>
            """, unsafe_allow_html=True)

# Rendre le menu plus clair
def customize_sidebar():
    """Personnalise l'apparence du menu latéral."""
    st.sidebar.markdown("""
    <style>
        [data-testid="stSidebarNav"] {
            background-color: #f8f9fa;
            padding-top: 2rem;
            padding-bottom: 1rem;
        }
        [data-testid="stSidebarNav"] > ul {
            padding-left: 20px;
        }
        [data-testid="stSidebarNav"] span {
            font-weight: 500;
        }
    </style>
    """, unsafe_allow_html=True)

# Initialisation
def run():
    """Fonction principale exécutée au démarrage de Streamlit."""
    ensure_visible_pages()
    customize_sidebar()
    add_home_button()

# Exécuter le code au démarrage
run() 