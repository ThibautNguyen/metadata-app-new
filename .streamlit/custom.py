import streamlit as st

# Renommer la page "app" en "Catalogue" directement via JavaScript
js = """
<script>
document.addEventListener('DOMContentLoaded', (event) => {
    // Fonction pour remplacer le texte du menu
    function replaceMenuText() {
        const navItems = document.querySelectorAll('[data-testid="stSidebarNav"] ul li');
        if (navItems && navItems.length > 0) {
            // Trouver le premier élément (app.py)
            const appElement = navItems[0];
            const spanElements = appElement.querySelectorAll('span');
            
            for (let span of spanElements) {
                if (span.textContent === 'app') {
                    span.textContent = 'Catalogue';
                    console.log('Menu renamed from app to Catalogue');
                    return true;
                }
            }
        }
        return false;
    }
    
    // Essayer immédiatement, puis réessayer plusieurs fois au cas où le DOM n'est pas encore prêt
    let attempts = 0;
    const maxAttempts = 10;
    
    const tryReplace = setInterval(() => {
        if (replaceMenuText() || attempts >= maxAttempts) {
            clearInterval(tryReplace);
        }
        attempts++;
    }, 300);
});
</script>
"""

# Injecter le JavaScript dans la page
st.markdown(js, unsafe_allow_html=True) 