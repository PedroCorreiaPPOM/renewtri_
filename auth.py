import re

import streamlit as st

import database as db
from utils import format_cnpj, normalize_cnpj, validate_cnpj, validate_password


def init_session_state() -> None:
    defaults = {
        "authenticated": False,
        "role": None,
        "user_email": None,
        "school_id": None,
        "school_name": None,
        "school_code": None,
        "employee_id": None,
        "employee_name": None,
    }

    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def login_user(
    role: str,
    email: str,
    password: str,
    school_code: str | None = None,
    cnpj: str | None = None,
) -> bool:
    email = email.strip().lower()

    if role == "Instituição de ensino":
        school = db.school_by_email_and_cnpj(email, cnpj or "")

        if not school or not validate_password(password, school["senha_hash"]):
            db.register_access("instituicao", email, False, "Login inválido")
            st.error("E-mail, CNPJ ou senha da instituição estão incorretos.")
            return False

        set_authenticated_school(school)
        db.register_access("instituicao", email, True, "Login realizado", school["id"])
        return True

    employee = db.employee_by_email(email)

    if not employee or not validate_password(password, employee["senha_hash"]):
        db.register_access("merendeira", email, False, "Login inválido")
        st.error("E-mail ou senha da merendeira estão incorretos.")
        return False

    if not employee["ativo"]:
        db.register_access(
            "merendeira",
            email,
            False,
            "Acesso desativado",
            employee["escola_id"],
        )
        st.error("Este acesso está desativado. Procure a instituição.")
        return False

    if employee["codigo_escola"].upper() != (school_code or "").strip().upper():
        db.register_access(
            "merendeira",
            email,
            False,
            "Código da escola inválido",
            employee["escola_id"],
        )
        st.error("Código da escola incorreto para esta merendeira.")
        return False

    st.session_state.authenticated = True
    st.session_state.role = "merendeira"
    st.session_state.user_email = employee["email"]
    st.session_state.school_id = employee["escola_id"]
    st.session_state.school_name = employee["escola_nome"]
    st.session_state.school_code = employee["codigo_escola"]
    st.session_state.employee_id = employee["id"]
    st.session_state.employee_name = employee["nome"]

    db.register_access("merendeira", email, True, "Login realizado", employee["escola_id"])
    return True


def set_authenticated_school(school) -> None:
    st.session_state.authenticated = True
    st.session_state.role = "instituicao"
    st.session_state.user_email = school["email"]
    st.session_state.school_id = school["id"]
    st.session_state.school_name = school["nome"]
    st.session_state.school_code = school["codigo_escola"]
    st.session_state.employee_id = None
    st.session_state.employee_name = None


def logout() -> None:
    for key in [
        "authenticated",
        "role",
        "user_email",
        "school_id",
        "school_name",
        "school_code",
        "employee_id",
        "employee_name",
    ]:
        st.session_state.pop(key, None)

    init_session_state()
    st.rerun()


def valid_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email or ""))


def show_auth_page() -> None:
    st.markdown(
        """
        <div class="renewtri-hero">
            <h1>Renewtri</h1>
            <div class="subtitle">
                Plataforma para gestão da merenda escolar, redução de desperdício
                e sustentabilidade em escolas públicas.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    login_tab, register_tab = st.tabs(["Entrar", "Cadastrar instituição"])

    with login_tab:
        col_left, col_right = st.columns([1.15, 0.85])

        with col_left:
            st.subheader("Acesso à plataforma")

            role = st.radio(
                "Tipo de acesso",
                ["Instituição de ensino", "Merendeira"],
                horizontal=True,
            )

            with st.form("login_form"):
                email = st.text_input("E-mail")

                school_code = None
                cnpj = None

                if role == "Instituição de ensino":
                    cnpj = st.text_input("CNPJ", placeholder="00.000.000/0000-00")

                if role == "Merendeira":
                    school_code = st.text_input("Código da escola")

                password = st.text_input("Senha", type="password")
                submitted = st.form_submit_button("Entrar")

            if submitted:
                if not valid_email(email):
                    st.error("Informe um e-mail válido.")
                elif role == "Instituição de ensino" and len(normalize_cnpj(cnpj or "")) != 14:
                    st.error("Informe um CNPJ válido.")
                elif not password:
                    st.error("Informe a senha.")
                elif login_user(role, email, password, school_code, cnpj):
                    st.success("Login realizado com sucesso.")
                    st.rerun()

        with col_right:
            with st.container(border=True):
                st.markdown("#### Dados de demonstração")

                st.markdown("**Instituição**")
                st.write("E-mail: escola@renewtri.demo")
                st.write("CNPJ: 11.222.333/0001-81")
                st.write("Senha: renewtri123")

                st.markdown("**Merendeira**")
                st.write("E-mail: robertina@renewtri.demo")
                st.write("Senha: merenda123")
                st.write("Código: aparece ao entrar como instituição.")

    with register_tab:
        st.subheader("Cadastro da instituição de ensino")

        with st.form("register_school_form"):
            nome = st.text_input("Nome da instituição")
            email = st.text_input("E-mail institucional")
            cnpj = st.text_input("CNPJ", placeholder="00.000.000/0000-00")
            codigo_inep = st.text_input("Código INEP")
            senha = st.text_input("Senha", type="password")
            confirmar = st.text_input("Confirmar senha", type="password")
            submitted = st.form_submit_button("Criar cadastro")

        if submitted:
            if not all([nome, email, cnpj, codigo_inep, senha, confirmar]):
                st.error("Preencha todos os campos.")
            elif not valid_email(email):
                st.error("Informe um e-mail válido.")
            elif not validate_cnpj(cnpj):
                st.error("CNPJ inválido. Verifique os números informados.")
            elif db.cnpj_exists(cnpj):
                st.error("Este CNPJ já está cadastrado.")
            elif db.school_by_email(email):
                st.error("Este e-mail já está cadastrado.")
            elif senha != confirmar:
                st.error("As senhas não conferem.")
            elif len(senha) < 6:
                st.error("A senha deve ter pelo menos 6 caracteres.")
            else:
                code = db.create_school(nome, email, cnpj, codigo_inep, senha)
                st.success(
                    f"Instituição cadastrada com sucesso. "
                    f"CNPJ: {format_cnpj(cnpj)}. "
                    f"Código da escola: {code}"
                )