import streamlit as st

# Configuration du menu de navigation
st.set_page_config(
    page_title="Métadonnées",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help": None,
        "Report a bug": None,
        "About": "Application de gestion des métadonnées"
    }
)

# Personnalisation des noms des pages dans le menu latéral
def rename_pages():
    """Force le renommage des pages dans le menu latéral"""
    # Appliquer du CSS personnalisé pour renommer la page principale
    st.markdown("""
    <style>
        /* Renommer la page principale 'app' en 'Catalogue' */
        span[data-testid="stSidebarNavLinkText"]:nth-child(1):contains("app") {
            visibility: hidden;
            position: relative;
        }
        
        span[data-testid="stSidebarNavLinkText"]:nth-child(1):contains("app")::after {
            content: "Catalogue";
            visibility: visible;
            position: absolute;
            left: 0;
            top: 0;
            color: inherit;
        }
        
        /* Assurer que tous les boutons du menu latéral sont visibles */
        section[data-testid="stSidebarUserContent"] {
            padding-top: 1rem;
        }
        
        /* Style pour les boutons du menu latéral */
        div[data-testid="stSidebarNav"] ul {
            padding-left: 0;
        }
        
        div[data-testid="stSidebarNav"] li {
            list-style: none;
            margin-bottom: 0.5rem;
        }
        
        /* Mettre en surbrillance la page active */
        span[data-testid="stSidebarNavLinkText"][aria-current="page"] {
            font-weight: bold;
            color: #1E88E5;
        }
    </style>
    """, unsafe_allow_html=True)

# Exécuter le renommage
rename_pages() 