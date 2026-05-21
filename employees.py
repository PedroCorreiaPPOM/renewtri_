import streamlit as st

import database as db
from auth import valid_email
from utils import metric_card, page_header, prepare_table_display


def show_employees(school_id: int) -> None:
    school = db.get_school(school_id)

    page_header(
        "Gerenciamento de merendeiras",
        "Cadastre, visualize e controle o acesso das profissionais responsáveis pelos registros da merenda.",
        "Administração",
    )

    c1, c2 = st.columns([0.72, 0.28])

    with c1:
        st.subheader("Cadastrar merendeira")

        with st.form("employee_form", clear_on_submit=True):
            nome = st.text_input("Nome completo")
            email = st.text_input("Email")
            senha = st.text_input("Senha inicial", type="password")
            submitted = st.form_submit_button("Cadastrar merendeira")

        if submitted:
            if not nome.strip() or not email.strip() or not senha:
                st.error("Preencha todos os campos.")
            elif not valid_email(email):
                st.error("Informe um email válido.")
            elif db.employee_by_email(email):
                st.error("Este email já está cadastrado para uma merendeira.")
            elif len(senha) < 6:
                st.error("A senha deve ter pelo menos 6 caracteres.")
            else:
                db.create_employee(
                    school_id,
                    nome.strip(),
                    email.strip().lower(),
                    senha,
                )

                st.success("Merendeira cadastrada com sucesso.")
                st.rerun()

    with c2:
        metric_card(
            "Código da escola",
            school["codigo_escola"],
            "Use no login da merendeira",
        )

    employees = db.employees_df(school_id)

    st.subheader("Merendeiras cadastradas")

    if employees.empty:
        st.info("Nenhuma merendeira cadastrada ainda.")
        return

    for _, row in employees.iterrows():
        col_name, col_status, col_action = st.columns([0.58, 0.18, 0.24])

        with col_name:
            st.markdown(f"**{row['nome']}**")
            st.caption(row["email"])

        with col_status:
            status = "Ativa" if row["ativo"] else "Desativada"
            st.markdown(
                f"<span class='badge'>{status}</span>",
                unsafe_allow_html=True,
            )

        with col_action:
            if row["ativo"]:
                if st.button("Desativar", key=f"disable_{row['id']}"):
                    db.set_employee_status(int(row["id"]), False, school_id)
                    st.rerun()
            else:
                if st.button("Ativar", key=f"enable_{row['id']}"):
                    db.set_employee_status(int(row["id"]), True, school_id)
                    st.rerun()

    employees_display = prepare_table_display(
        employees,
        hidden_columns=["id"],
        date_columns=["created_at"],
    )

    st.dataframe(
        employees_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "nome": "Nome",
            "email": "Email",
            "ativo": "Ativo",
            "created_at": "Criada em",
        },
    )