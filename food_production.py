from datetime import date

import pandas as pd
import streamlit as st

import database as db
from utils import current_user_role, metric_card, page_header, prepare_table_display, turnos


def format_production_option(row: pd.Series) -> str:
    record_date = pd.to_datetime(row["data"]).strftime("%d/%m/%Y")
    meals = int(row["refeicoes_produzidas"])
    return f"{record_date} - {row['turno']} - {meals} refeições"


def show_delete_production_control(history: pd.DataFrame, school_id: int) -> None:
    if history.empty:
        return

    st.markdown("#### Apagar registro")

    options = {
        format_production_option(row): int(row["id"])
        for _, row in history.iterrows()
    }

    selected_label = st.selectbox(
        "Selecione o registro de produção",
        list(options.keys()),
        key="production_delete_select",
    )

    if st.button("Apagar registro", key="request_delete_production"):
        st.session_state.pending_delete_production_id = options[selected_label]
        st.session_state.pending_delete_production_label = selected_label

    pending_id = st.session_state.get("pending_delete_production_id")
    pending_label = st.session_state.get("pending_delete_production_label")

    if pending_id:
        st.warning(
            f"Tem certeza que deseja apagar o registro **{pending_label}**? "
            "Essa ação não pode ser desfeita."
        )

        confirm_col, cancel_col = st.columns(2)

        with confirm_col:
            if st.button("Sim, apagar", type="primary", key="confirm_delete_production"):
                db.delete_production(int(pending_id), school_id)
                st.session_state.pop("pending_delete_production_id", None)
                st.session_state.pop("pending_delete_production_label", None)
                st.success("Registro de produção apagado com sucesso.")
                st.rerun()

        with cancel_col:
            if st.button("Cancelar", key="cancel_delete_production"):
                st.session_state.pop("pending_delete_production_id", None)
                st.session_state.pop("pending_delete_production_label", None)
                st.rerun()


def show_food_production(school_id: int) -> None:
    page_header(
        "Cadastro da produção",
        "Registre as refeições preparadas, alimentos utilizados e desperdício observado após cada turno.",
        "Produção alimentar",
    )

    left, right = st.columns([0.95, 1.05])

    with left:
        st.subheader("Novo registro")

        with st.form("production_form", clear_on_submit=True):
            data = st.date_input(
                "Data",
                value=date.today(),
                format="DD/MM/YYYY",
            )

            turno = st.selectbox("Turno", turnos())

            refeicoes = st.number_input(
                "Refeições produzidas",
                min_value=0,
                step=1,
                value=180,
            )

            alimentos = st.text_area(
                "Alimentos utilizados",
                placeholder="Ex.: arroz, feijão, frango, legumes",
                height=100,
            )

            desperdicio = st.number_input(
                "Desperdício em kg",
                min_value=0.0,
                step=0.1,
                value=5.0,
            )

            observacoes = st.text_area(
                "Observações",
                placeholder="Ex.: baixa frequência por chuva",
            )

            submitted = st.form_submit_button("Salvar produção")

        if submitted:
            if refeicoes <= 0:
                st.error("Informe uma quantidade de refeições maior que zero.")
            elif not alimentos.strip():
                st.error("Informe os alimentos utilizados.")
            else:
                employee_id = st.session_state.get("employee_id")

                db.insert_production(
                    school_id=school_id,
                    employee_id=employee_id,
                    data=data.isoformat(),
                    turno=turno,
                    refeicoes=int(refeicoes),
                    alimentos=alimentos.strip(),
                    desperdicio_kg=float(desperdicio),
                    observacoes=observacoes.strip(),
                )

                st.success("Produção registrada com sucesso.")
                st.rerun()

    with right:
        history = db.production_df(school_id)

        total_meals = history["refeicoes_produzidas"].sum() if not history.empty else 0
        total_waste = history["desperdicio_kg"].sum() if not history.empty else 0

        c1, c2 = st.columns(2)

        with c1:
            metric_card(
                "Total de refeições",
                f"{int(total_meals):,}".replace(",", "."),
                "Histórico geral",
            )

        with c2:
            metric_card(
                "Desperdício total",
                f"{total_waste:.1f} kg".replace(".", ","),
                "Histórico geral",
            )

        st.subheader("Histórico de produção")

        if current_user_role() == "merendeira":
            st.caption("A merendeira pode registrar produção e consultar os dados operacionais da escola.")

        history_display = prepare_table_display(
            history,
            hidden_columns=["id"],
            date_columns=["data"],
        )

        st.dataframe(
            history_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "data": "Data",
                "turno": "Turno",
                "refeicoes_produzidas": "Refeições",
                "alimentos_utilizados": "Alimentos utilizados",
                "desperdicio_kg": "Desperdício (kg)",
                "observacoes": "Observações",
                "registrado_por": "Registrado por",
            },
        )

        show_delete_production_control(history, school_id)
