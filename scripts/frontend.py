import streamlit as st
import os

# Fonction pour injecter le HTML personnalisé
def inject_custom_html():
    """Injecte du HTML personnalisé dans l'application Streamlit."""
    # Emplacement du fichier HTML personnalisé
    html_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                 '.streamlit', 'custom.html')
    
    # Vérifier si le fichier existe
    if os.path.exists(html_file_path):
        try:
            with open(html_file_path, 'r', encoding='utf-8') as f:
                custom_html = f.read()
                
            # Injecter le HTML personnalisé
            st.markdown(custom_html, unsafe_allow_html=True)
            return True
        except Exception as e:
            st.warning(f"Erreur lors du chargement du HTML personnalisé: {str(e)}")
            return False
    else:
        return False

# Fonction pour renommer "app" en "Catalogue" dans le menu latéral via JavaScript
def rename_app_to_catalogue():
    """Renomme "app" en "Catalogue" dans le menu latéral via JavaScript."""
    js = """
    <script>
        // Fonction pour renommer le menu
        function renameAppToCatalogue() {
            // Tous les textes possibles dans le menu
            const elements = document.querySelectorAll('[data-testid="stSidebarNav"] span, [data-testid="stSidebarNav"] p, [data-testid="stSidebarNav"] a, [data-testid="stSidebarNav"] div');
            
            elements.forEach(el => {
                // Si l'élément contient exactement "app"
                if (el.textContent === "app") {
                    el.textContent = "Catalogue";
                    console.log("Menu renamed: app -> Catalogue");
                }
            });
        }
        
        // Exécuter après le chargement initial
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(renameAppToCatalogue, 200);
        });
        
        // Continuer à vérifier périodiquement
        setInterval(renameAppToCatalogue, 1000);
    </script>
    """
    st.markdown(js, unsafe_allow_html=True)

# Injecter le CSS personnalisé pour styler le menu
def inject_css():
    """Injecte du CSS personnalisé pour styler le menu latéral."""
    css = """
    <style>
        /* Style pour masquer "app" et afficher "Catalogue" */
        [data-testid="stSidebarNav"] span:contains("app") {
            color: transparent;
            position: relative;
        }
        
        [data-testid="stSidebarNav"] span:contains("app")::after {
            content: 'Catalogue';
            position: absolute;
            left: 0;
            top: 0;
            color: rgb(49, 51, 63);
            visibility: visible;
        }
        
        /* Style pour le menu latéral */
        section[data-testid="stSidebar"] {
            background-color: #f8f9fa;
            border-right: 1px solid #e9ecef;
        }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# Exécuter toutes les personnalisations
inject_custom_html()
rename_app_to_catalogue()
inject_css() 