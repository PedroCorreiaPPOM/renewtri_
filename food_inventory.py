from datetime import date, timedelta

import pandas as pd
import streamlit as st

import database as db
from utils import metric_card, page_header, prepare_table_display


def format_inventory_option(row: pd.Series) -> str:
    record_date = pd.to_datetime(row["data"]).strftime("%d/%m/%Y")
    quantity = float(row["quantidade_kg"])
    return f"{record_date} - {row['alimento']} - {quantity:.1f} kg"


def show_delete_inventory_control(inventory: pd.DataFrame, school_id: int) -> None:
    if inventory.empty:
        return

    st.markdown("#### Apagar registro")

    options = {
        format_inventory_option(row): int(row["id"])
        for _, row in inventory.iterrows()
    }

    selected_label = st.selectbox(
        "Selecione o alimento recebido",
        list(options.keys()),
        key="inventory_delete_select",
    )

    if st.button("Apagar registro", key="request_delete_inventory"):
        st.session_state.pending_delete_inventory_id = options[selected_label]
        st.session_state.pending_delete_inventory_label = selected_label

    pending_id = st.session_state.get("pending_delete_inventory_id")
    pending_label = st.session_state.get("pending_delete_inventory_label")

    if pending_id:
        st.warning(
            f"Tem certeza que deseja apagar o registro **{pending_label}**? "
            "Essa ação não pode ser desfeita."
        )

        confirm_col, cancel_col = st.columns(2)

        with confirm_col:
            if st.button("Sim, apagar", type="primary", key="confirm_delete_inventory"):
                db.delete_inventory(int(pending_id), school_id)
                st.session_state.pop("pending_delete_inventory_id", None)
                st.session_state.pop("pending_delete_inventory_label", None)
                st.success("Registro de alimento recebido apagado com sucesso.")
                st.rerun()

        with cancel_col:
            if st.button("Cancelar", key="cancel_delete_inventory"):
                st.session_state.pop("pending_delete_inventory_id", None)
                st.session_state.pop("pending_delete_inventory_label", None)
                st.rerun()


def show_food_inventory(school_id: int) -> None:
    page_header(
        "Alimentos recebidos",
        "Controle entradas de fornecedores, quantidades em kg, validade e observações importantes.",
        "Estoque da merenda",
    )

    left, right = st.columns([0.95, 1.05])

    with left:
        st.subheader("Nova entrada")

        with st.form("inventory_form", clear_on_submit=True):
            data = st.date_input(
                "Data de recebimento",
                value=date.today(),
                format="DD/MM/YYYY",
            )

            fornecedor = st.text_input(
                "Fornecedor",
                placeholder="Ex.: Cooperativa Sertão Verde",
            )

            alimento = st.text_input(
                "Alimento",
                placeholder="Ex.: arroz",
            )

            quantidade = st.number_input(
                "Quantidade em kg",
                min_value=0.0,
                value=20.0,
                step=0.5,
            )

            validade = st.date_input(
                "Validade",
                value=date.today() + timedelta(days=30),
                format="DD/MM/YYYY",
            )

            observacoes = st.text_area(
                "Observações",
                placeholder="Ex.: entrega conferida pela coordenação",
            )

            submitted = st.form_submit_button("Salvar alimento")

        if submitted:
            if not fornecedor.strip() or not alimento.strip():
                st.error("Informe fornecedor e alimento.")
            elif quantidade <= 0:
                st.error("A quantidade precisa ser maior que zero.")
            elif validade < data:
                st.error("A validade não pode ser anterior à data de recebimento.")
            else:
                db.insert_inventory(
                    school_id,
                    data.isoformat(),
                    fornecedor.strip(),
                    alimento.strip(),
                    float(quantidade),
                    validade.isoformat(),
                    observacoes.strip(),
                )

                st.success("Entrada registrada com sucesso.")
                st.rerun()

    with right:
        inventory = db.inventory_df(school_id)

        total = inventory["quantidade_kg"].sum() if not inventory.empty else 0
        suppliers = inventory["fornecedor"].nunique() if not inventory.empty else 0

        c1, c2 = st.columns(2)

        with c1:
            metric_card(
                "Alimentos recebidos",
                f"{total:.1f} kg".replace(".", ","),
                "Total no histórico",
            )

        with c2:
            metric_card(
                "Fornecedores",
                str(suppliers),
                "Cadastrados no MVP",
            )

        st.subheader("Histórico de recebimentos")

        inventory_display = prepare_table_display(
            inventory,
            hidden_columns=["id"],
            date_columns=["data", "validade"],
        )

        st.dataframe(
            inventory_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "data": "Data",
                "fornecedor": "Fornecedor",
                "alimento": "Alimento",
                "quantidade_kg": "Quantidade (kg)",
                "validade": "Validade",
                "observacoes": "Observações",
            },
        )

        show_delete_inventory_control(inventory, school_id)
