import streamlit as st

import database as db
from auth import valid_email
from utils import metric_card, page_header, prepare_table_display


def valid_employee_password(password: str) -> bool:
    has_minimum_length = len(password) >= 8
    has_uppercase = any(char.isupper() for char in password)
    has_lowercase = any(char.islower() for char in password)
    has_number = any(char.isdigit() for char in password)
    has_special = any(not char.isalnum() for char in password)
    return all([has_minimum_length, has_uppercase, has_lowercase, has_number, has_special])


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
            email = st.text_input("E-mail")
            senha = st.text_input("Senha inicial", type="password")
            st.caption(
                "A senha deve ter no mínimo 8 caracteres, com letra maiúscula, "
                "letra minúscula, número e caractere especial."
            )
            submitted = st.form_submit_button("Cadastrar merendeira")

        if submitted:
            if not nome.strip() or not email.strip() or not senha:
                st.error("Preencha todos os campos.")
            elif not valid_email(email):
                st.error("Informe um e-mail válido.")
            elif db.employee_by_email(email):
                st.error("Este e-mail já está cadastrado para uma merendeira.")
            elif not valid_employee_password(senha):
                st.error(
                    "A senha deve ter no mínimo 8 caracteres, com letra maiúscula, "
                    "letra minúscula, número e caractere especial."
                )
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

        is_active = bool(int(row["ativo"]))

        with col_status:
            status = "Ativa" if is_active else "Desativada"
            st.markdown(
                f"<span class='badge'>{status}</span>",
                unsafe_allow_html=True,
            )

        with col_action:
            if is_active:
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
            "email": "E-mail",
            "ativo": "Ativo",
            "created_at": "Criada em",
        },
    )