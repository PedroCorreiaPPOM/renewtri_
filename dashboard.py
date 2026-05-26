import pandas as pd
import plotly.express as px
import streamlit as st

import database as db
from utils import format_int, format_kg, format_percent, metric_card, page_header, plotly_layout


def calculate_metrics(production: pd.DataFrame, inventory: pd.DataFrame) -> dict[str, float]:
    meals = float(production["refeicoes_produzidas"].sum()) if not production.empty else 0.0
    waste = float(production["desperdicio_kg"].sum()) if not production.empty else 0.0
    received = float(inventory["quantidade_kg"].sum()) if not inventory.empty else 0.0
    waste_rate = (waste / meals * 100) if meals else 0.0

    if not production.empty:
        production = production.copy()
        production["data"] = pd.to_datetime(production["data"])
        current_month = pd.Timestamp.today().to_period("M")
        previous_month = current_month - 1

        current_waste = production[
            production["data"].dt.to_period("M") == current_month
        ]["desperdicio_kg"].sum()

        previous_waste = production[
            production["data"].dt.to_period("M") == previous_month
        ]["desperdicio_kg"].sum()

        saved = max(float(previous_waste - current_waste), 0.0)
    else:
        saved = 0.0

    return {
        "meals": meals,
        "waste": waste,
        "received": received,
        "waste_rate": waste_rate,
        "saved": saved,
    }


def show_dashboard(school_id: int) -> None:
    page_header(
        "Tela Principal",
        "Acompanhe produção, desperdício, estoque recebido e indicadores de sustentabilidade em tempo real.",
        "Gestão inteligente da merenda",
    )

    production = db.production_df(school_id)
    inventory = db.inventory_df(school_id)
    metrics = calculate_metrics(production, inventory)

    cols = st.columns(5)

    with cols[0]:
        metric_card(
            "Refeições produzidas",
            format_int(metrics["meals"]),
            "Total registrado",
        )

    with cols[1]:
        metric_card(
            "Desperdício registrado",
            format_kg(metrics["waste"]),
            "Soma em kg",
        )

    with cols[2]:
        metric_card(
            "Alimentos recebidos",
            format_kg(metrics["received"]),
            "Entradas no estoque",
        )

    with cols[3]:
        metric_card(
            "Taxa de desperdício",
            format_percent(metrics["waste_rate"]),
            "Kg por refeição",
        )

    with cols[4]:
        metric_card(
            "Quilos economizados",
            format_kg(metrics["saved"]),
            "Comparação mensal",
        )

    if production.empty:
        st.info("Ainda não há produção registrada. Use os cadastros para alimentar o dashboard.")
        return

    chart_df = production.copy()
    chart_df["data"] = pd.to_datetime(chart_df["data"])
    chart_df["mes"] = chart_df["data"].dt.to_period("M").astype(str)

    monthly = chart_df.groupby("mes", as_index=False).agg(
        refeicoes_produzidas=("refeicoes_produzidas", "sum"),
        desperdicio_kg=("desperdicio_kg", "sum"),
    )

    monthly["taxa_desperdicio"] = (
        monthly["desperdicio_kg"] / monthly["refeicoes_produzidas"] * 100
    )

    monthly["tendencia"] = (
        monthly["desperdicio_kg"]
        .rolling(window=2, min_periods=1)
        .mean()
    )

    fig = px.bar(
        monthly,
        x="mes",
        y="desperdicio_kg",
        text=monthly["desperdicio_kg"].map(lambda value: f"{value:.1f} kg"),
        color="taxa_desperdicio",
        color_continuous_scale=["#dff6ef", "#0f9f6e", "#0b6fb8"],
        labels={
            "mes": "Mês de acompanhamento",
            "desperdicio_kg": "Desperdício total (kg)",
            "taxa_desperdicio": "Taxa de desperdício (%)",
        },
    )

    fig.add_scatter(
        x=monthly["mes"],
        y=monthly["tendencia"],
        mode="lines+markers",
        name="Tendência de redução",
        line=dict(
            color="#073b4c",
            width=3,
            shape="spline",
        ),
        marker=dict(
            size=9,
            color="#073b4c",
        ),
    )

    fig.update_traces(
        textposition="outside",
        selector=dict(type="bar"),
        name="Desperdício mensal",
    )

    fig.update_layout(
        coloraxis_colorbar=dict(
            title="Taxa (%)",
        ),
        legend_title_text="Leitura do gráfico",
        uniformtext_minsize=10,
        uniformtext_mode="hide",
    )

    st.plotly_chart(
        plotly_layout(fig, "Desperdício mensal da merenda escolar"),
        use_container_width=True,
    )

    st.caption(
        "Barras mostram o desperdício total de cada mês. "
        "A linha escura mostra a tendência geral, ajudando a banca a visualizar se o desperdício está diminuindo."
    )