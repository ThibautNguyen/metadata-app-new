import streamlit as st
import os
import sys

# Fonction pour assurer que le menu est cohérent sur toutes les pages
def init_menu():
    """Initialise un menu latéral cohérent sur toutes les pages."""
    # Style général pour le menu latéral
    st.markdown("""
    <style>
        /* Masquer les éléments de navigation inutiles */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Style pour que le menu latéral soit plus propre */
        section[data-testid="stSidebar"] {
            background-color: #f8f9fa;
            border-right: 1px solid #e9ecef;
        }
        
        /* Style pour les liens de pages dans le menu */
        div[data-testid="stSidebarNav"] a {
            display: block;
            padding: 0.5rem 1rem;
            margin-bottom: 0.2rem;
            border-radius: 4px;
            text-decoration: none;
            font-weight: 500;
        }
        
        div[data-testid="stSidebarNav"] a:hover {
            background-color: rgba(49, 51, 63, 0.1);
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Ajouter systématiquement un bouton pour retourner au catalogue
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
            Catalogue
        </a>
    </div>
    """, unsafe_allow_html=True)

# Ajouter une séparation visuelle dans le menu latéral
def add_sidebar_separator():
    """Ajoute une ligne de séparation dans le menu latéral."""
    st.sidebar.markdown("<hr style='margin: 1rem 0; border: 0; border-top: 1px solid #e9ecef;'>", 
                        unsafe_allow_html=True)

# Initialiser le menu sur chaque page, en capturant les erreurs si elles se produisent
try:
    init_menu()
except Exception as e:
    # Afficher une alerte en cas d'erreur, mais ne pas bloquer l'application
    st.sidebar.warning("Menu personnalisé indisponible")
    
    # Essayer d'ajouter un bouton de secours minimal
    try:
        st.sidebar.markdown("""
        <div style="margin: 1rem 0;">
            <a href="/" style="text-decoration: none; display: block; text-align: center;">
                Retour au Catalogue
            </a>
        </div>
        """, unsafe_allow_html=True)
    except:
        # Si tout échoue, ne rien faire - l'interface standard de Streamlit sera utilisée
        pass 