from datetime import date, timedelta

import pandas as pd
import streamlit as st

import database as db
from utils import format_int, format_percent, metric_card, page_header


PORTION_KG = 0.45

WEEKDAYS = {
    0: "Segunda-feira",
    1: "Terça-feira",
    2: "Quarta-feira",
    3: "Quinta-feira",
    4: "Sexta-feira",
    5: "Sábado",
    6: "Domingo",
}


DEFAULT_TURNS = ["Manhã", "Tarde"]


def prepare_history(production: pd.DataFrame) -> pd.DataFrame:
    df = production.copy()

    df["data"] = pd.to_datetime(df["data"])
    df["refeicoes_produzidas"] = pd.to_numeric(
        df["refeicoes_produzidas"], errors="coerce"
    ).fillna(0)
    df["desperdicio_kg"] = pd.to_numeric(
        df["desperdicio_kg"], errors="coerce"
    ).fillna(0)

    df["turno"] = df["turno"].fillna("Não informado")
    df["alimentos_utilizados"] = df["alimentos_utilizados"].fillna("Cardápio não informado")
    df["dia_semana"] = df["data"].dt.weekday

    df["taxa_desperdicio"] = (
        df["desperdicio_kg"] / df["refeicoes_produzidas"].replace(0, pd.NA) * 100
    ).fillna(0)

    return df.sort_values("data")


def calculate_general_metrics(df: pd.DataFrame) -> dict[str, float]:
    last_30_days = df[df["data"] >= df["data"].max() - pd.Timedelta(days=30)]

    if last_30_days.empty:
        last_30_days = df

    total_meals = last_30_days["refeicoes_produzidas"].sum()
    total_waste = last_30_days["desperdicio_kg"].sum()

    avg_meals = last_30_days["refeicoes_produzidas"].mean()
    waste_rate = (total_waste / total_meals * 100) if total_meals else 0
    success_rate = max(0, 100 - waste_rate)

    return {
        "avg_meals": avg_meals,
        "waste_rate": waste_rate,
        "success_rate": success_rate,
    }


def get_forecast_turns(df: pd.DataFrame) -> list[str]:
    turns = df["turno"].dropna().astype(str).unique().tolist()

    if not turns:
        return DEFAULT_TURNS

    ordered_turns = [turn for turn in DEFAULT_TURNS if turn in turns]
    other_turns = sorted([turn for turn in turns if turn not in ordered_turns])

    return ordered_turns + other_turns


def choose_food_suggestion(history: pd.DataFrame, fallback: pd.DataFrame) -> str:
    valid_history = history[
        history["alimentos_utilizados"].notna()
        & (history["alimentos_utilizados"].str.strip() != "")
    ]

    if not valid_history.empty:
        return valid_history.sort_values("data", ascending=False).iloc[0]["alimentos_utilizados"]

    valid_fallback = fallback[
        fallback["alimentos_utilizados"].notna()
        & (fallback["alimentos_utilizados"].str.strip() != "")
    ]

    if not valid_fallback.empty:
        return valid_fallback.sort_values("data", ascending=False).iloc[0]["alimentos_utilizados"]

    return "Cardápio a definir"


def calculate_recommendation(base_meals: float, base_waste_rate: float) -> tuple[int, float, float]:
    if base_waste_rate > 10:
        reduction_factor = 0.08
    elif base_waste_rate > 6:
        reduction_factor = 0.05
    else:
        reduction_factor = 0.03

    recommended_plates = int(round(base_meals * (1 - reduction_factor)))
    recommended_plates = max(recommended_plates, 1)

    predicted_waste_rate = max(base_waste_rate - (reduction_factor * 35), 2)
    predicted_success_rate = min(100, 100 - predicted_waste_rate)

    return recommended_plates, predicted_success_rate, predicted_waste_rate


def build_forecast_table(df: pd.DataFrame, days: int = 7) -> pd.DataFrame:
    max_date = df["data"].max()
    recent_history = df[df["data"] >= max_date - pd.Timedelta(days=30)]

    if recent_history.empty:
        recent_history = df

    recent_avg_meals = recent_history["refeicoes_produzidas"].mean()
    recent_waste_rate = recent_history["taxa_desperdicio"].mean()
    turns = get_forecast_turns(df)

    forecast_rows = []

    for day_offset in range(1, days + 1):
        target_date = date.today() + timedelta(days=day_offset)
        weekday_number = target_date.weekday()

        for turn in turns:
            same_weekday_turn_history = df[
                (df["dia_semana"] == weekday_number) & (df["turno"] == turn)
            ].tail(8)

            same_turn_history = df[df["turno"] == turn].tail(12)
            same_weekday_history = df[df["dia_semana"] == weekday_number].tail(8)

            if not same_weekday_turn_history.empty:
                turn_avg_meals = same_weekday_turn_history["refeicoes_produzidas"].mean()
                turn_waste_rate = same_weekday_turn_history["taxa_desperdicio"].mean()

                base_meals = (turn_avg_meals * 0.75) + (recent_avg_meals * 0.25)
                base_waste_rate = (turn_waste_rate * 0.75) + (recent_waste_rate * 0.25)
                food_suggestion = choose_food_suggestion(
                    same_weekday_turn_history,
                    recent_history,
                )

            elif not same_turn_history.empty:
                turn_avg_meals = same_turn_history["refeicoes_produzidas"].mean()
                turn_waste_rate = same_turn_history["taxa_desperdicio"].mean()

                base_meals = (turn_avg_meals * 0.65) + (recent_avg_meals * 0.35)
                base_waste_rate = (turn_waste_rate * 0.65) + (recent_waste_rate * 0.35)
                food_suggestion = choose_food_suggestion(
                    same_turn_history,
                    recent_history,
                )

            elif not same_weekday_history.empty:
                weekday_avg_meals = same_weekday_history["refeicoes_produzidas"].mean()
                weekday_waste_rate = same_weekday_history["taxa_desperdicio"].mean()

                base_meals = (weekday_avg_meals * 0.65) + (recent_avg_meals * 0.35)
                base_waste_rate = (weekday_waste_rate * 0.65) + (recent_waste_rate * 0.35)
                food_suggestion = choose_food_suggestion(
                    same_weekday_history,
                    recent_history,
                )

            else:
                base_meals = recent_avg_meals
                base_waste_rate = recent_waste_rate
                food_suggestion = choose_food_suggestion(recent_history, df)

            recommended_plates, success_rate, waste_rate = calculate_recommendation(
                base_meals,
                base_waste_rate,
            )

            recommended_kg = recommended_plates * PORTION_KG

            forecast_rows.append(
                {
                    "Dia da semana": WEEKDAYS[weekday_number],
                    "Data": target_date.strftime("%d/%m/%Y"),
                    "Turno": turn,
                    "Alimentos sugeridos": food_suggestion,
                    "Pratos": recommended_plates,
                    "Kg": recommended_kg,
                    "Sucesso": success_rate,
                    "Desperdício": waste_rate,
                }
            )

    return pd.DataFrame(forecast_rows)


def show_prediction(school_id: int) -> None:
    page_header(
        "Previsão Inteligente",
        "Recomendações de preparo com base no histórico da escola, taxa de desperdício, turno e alimentos utilizados.",
        "Planejamento alimentar",
    )

    production = db.production_df(school_id)

    if production.empty:
        st.info("Ainda não há dados suficientes para gerar previsões. Registre produções alimentares primeiro.")
        return

    df = prepare_history(production)

    if len(df) < 3:
        st.warning("Cadastre pelo menos três registros de produção para melhorar a qualidade da previsão.")

    metrics = calculate_general_metrics(df)

    col1, col2, col3 = st.columns(3)

    with col1:
        metric_card(
            "Média de refeições",
            format_int(metrics["avg_meals"]),
            "Base dos últimos registros",
        )

    with col2:
        metric_card(
            "Taxa de desperdício",
            format_percent(metrics["waste_rate"]),
            "Média recente",
        )

    with col3:
        metric_card(
            "Taxa de sucesso",
            format_percent(metrics["success_rate"]),
            "Aproveitamento estimado",
        )

    st.markdown("---")

    if metrics["waste_rate"] > 10:
        st.warning(
            "Alerta: a taxa de desperdício está acima de 10%. "
            "O sistema recomenda reduzir levemente a produção inicial e acompanhar a aceitação do cardápio."
        )
    else:
        st.success(
            "Desperdício controlado. O histórico indica bom aproveitamento da merenda escolar."
        )

    forecast_df = build_forecast_table(df)

    tomorrow_rows = forecast_df[forecast_df["Data"] == forecast_df.iloc[0]["Data"]]
    tomorrow_total_plates = tomorrow_rows["Pratos"].sum()
    tomorrow_total_kg = tomorrow_rows["Kg"].sum()
    tomorrow_avg_success = tomorrow_rows["Sucesso"].mean()

    st.info(
        f"Recomendação para amanhã: preparar **{int(tomorrow_total_plates)} pratos**, "
        f"aproximadamente **{tomorrow_total_kg:.1f} kg**, considerando os turnos cadastrados. "
        f"Sucesso médio previsto: **{tomorrow_avg_success:.1f}%**."
    )

    st.subheader("Tabela inteligente de previsão")

    table_df = forecast_df.copy()
    table_df["Kg"] = table_df["Kg"].map(lambda value: f"{value:.1f} kg")
    table_df["Sucesso"] = table_df["Sucesso"].map(lambda value: f"{value:.1f}%")
    table_df["Desperdício"] = table_df["Desperdício"].map(lambda value: f"{value:.1f}%")

    st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Dia da semana": st.column_config.TextColumn("Dia"),
            "Data": st.column_config.TextColumn("Data"),
            "Turno": st.column_config.TextColumn("Turno"),
            "Alimentos sugeridos": st.column_config.TextColumn("Alimentos sugeridos"),
            "Pratos": st.column_config.NumberColumn("Pratos recomendados"),
            "Kg": st.column_config.TextColumn("Quantidade em kg"),
            "Sucesso": st.column_config.TextColumn("Sucesso previsto"),
            "Desperdício": st.column_config.TextColumn("Desperdício previsto"),
        },
    )

    st.markdown("---")

    st.subheader("Recomendações automáticas")

    best_day = forecast_df.sort_values("Desperdício").iloc[0]
    attention_day = forecast_df.sort_values("Desperdício", ascending=False).iloc[0]

    col1, col2 = st.columns(2)

    with col1:
        st.success(
            f"Melhor cenário previsto: **{best_day['Dia da semana']} - {best_day['Turno']}**, "
            f"com desperdício estimado de **{best_day['Desperdício']:.1f}%**."
        )

    with col2:
        st.warning(
            f"Dia que exige mais atenção: **{attention_day['Dia da semana']} - {attention_day['Turno']}**, "
            f"com desperdício estimado de **{attention_day['Desperdício']:.1f}%**."
        )

    st.markdown("---")

    st.subheader("Como o sistema calcula a previsão")

    st.markdown(
        """
        <div class="info-card">
            <p>
                A previsão do Renewtri utiliza os registros salvos no banco de dados da escola.
                O sistema analisa a média recente de refeições produzidas, a média de desperdício,
                o comportamento histórico do mesmo dia da semana e o turno em que a produção foi registrada.
            </p>
            <p>
                Para sugerir os alimentos, o sistema consulta os cardápios registrados anteriormente.
                Quando existe histórico do mesmo dia e turno, ele prioriza esse padrão. Quando não existe,
                utiliza os alimentos mais recentes como referência.
            </p>
            <p>
                Para evitar desperdício, a recomendação aplica uma redução leve na quantidade prevista
                quando a taxa de desperdício está alta. A quantidade em kg considera uma porção média de
                <strong>0,45 kg por prato</strong>.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )