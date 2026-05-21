import streamlit as st

import auth
import database as db
from dashboard import show_dashboard
from employees import show_employees
from food_inventory import show_food_inventory
from food_production import show_food_production
from prediction import show_prediction
from sustainability import show_sustainability
from utils import apply_custom_css


def sidebar_navigation() -> str:
    st.sidebar.markdown("## Renewtri")
    st.sidebar.caption("Gestão inteligente da merenda escolar")
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Escola:** {st.session_state.school_name}")
    st.sidebar.markdown(f"**Código:** `{st.session_state.school_code}`")
    if st.session_state.role == "merendeira":
        st.sidebar.markdown(f"**Merendeira:** {st.session_state.employee_name}")
    else:
        st.sidebar.markdown("**Perfil:** Instituição")
    st.sidebar.markdown("---")

    pages = [
        "Dashboard",
        "Produção alimentar",
        "Alimentos recebidos",
        "Previsão Inteligente",
        "Sustentabilidade",
    ]
    if st.session_state.role == "instituicao":
        pages.insert(3, "Merendeiras")

    selected = st.sidebar.radio("Navegação", pages, label_visibility="collapsed")
    st.sidebar.markdown("---")
    if st.sidebar.button("Sair"):
        auth.logout()
    return selected


def main() -> None:
    st.set_page_config(
        page_title="Renewtri - Gestão da Merenda Escolar",
        page_icon="R",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_custom_css()
    auth.init_session_state()
    db.init_db()

    if not st.session_state.authenticated:
        auth.show_auth_page()
        return

    selected = sidebar_navigation()
    school_id = int(st.session_state.school_id)

    if selected == "Dashboard":
        show_dashboard(school_id)
    elif selected == "Produção alimentar":
        show_food_production(school_id)
    elif selected == "Alimentos recebidos":
        show_food_inventory(school_id)
    elif selected == "Merendeiras":
        if st.session_state.role != "instituicao":
            st.error("Apenas instituições podem acessar esta área.")
        else:
            show_employees(school_id)
    elif selected == "Previsão Inteligente":
        show_prediction(school_id)
    elif selected == "Sustentabilidade":
        show_sustainability()


if __name__ == "__main__":
    main()
