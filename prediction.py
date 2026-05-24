from datetime import date, timedelta

import pandas as pd
import streamlit as st

import database as db
from utils import format_int, format_percent, metric_card, page_header


PORTION_KG = 0.45
MAX_FORECAST_ROWS = 14
LOOKAHEAD_DAYS = 21

WEEKDAYS = {
    0: "Segunda-feira",
    1: "Terça-feira",
    2: "Quarta-feira",
    3: "Quinta-feira",
    4: "Sexta-feira",
    5: "Sábado",
    6: "Domingo",
}

TURN_ORDER = {
    "Manhã": 1,
    "Tarde": 2,
    "Noite": 3,
}


def prepare_history(production: pd.DataFrame) -> pd.DataFrame:
    df = production.copy()

    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df = df.dropna(subset=["data"])

    df["refeicoes_produzidas"] = pd.to_numeric(
        df["refeicoes_produzidas"], errors="coerce"
    ).fillna(0)

    df["desperdicio_kg"] = pd.to_numeric(
        df["desperdicio_kg"], errors="coerce"
    ).fillna(0)

    df["turno"] = df["turno"].fillna("Não informado").astype(str)
    df["alimentos_utilizados"] = (
        df["alimentos_utilizados"]
        .fillna("Cardápio não informado")
        .astype(str)
    )

    df["data_date"] = df["data"].dt.date
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


def sort_turns(turns: list[str]) -> list[str]:
    return sorted(turns, key=lambda turn: (TURN_ORDER.get(turn, 99), turn))


def choose_food_suggestion(primary_history: pd.DataFrame, fallback_history: pd.DataFrame) -> str:
    valid_primary = primary_history[
        primary_history["alimentos_utilizados"].str.strip() != ""
    ]

    if not valid_primary.empty:
        return valid_primary.sort_values("data", ascending=False).iloc[0][
            "alimentos_utilizados"
        ]

    valid_fallback = fallback_history[
        fallback_history["alimentos_utilizados"].str.strip() != ""
    ]

    if not valid_fallback.empty:
        return valid_fallback.sort_values("data", ascending=False).iloc[0][
            "alimentos_utilizados"
        ]

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


def build_forecast_table(df: pd.DataFrame) -> pd.DataFrame:
    recent_history = df[df["data"] >= df["data"].max() - pd.Timedelta(days=30)]

    if recent_history.empty:
        recent_history = df

    forecast_rows = []

    for day_offset in range(1, LOOKAHEAD_DAYS + 1):
        if len(forecast_rows) >= MAX_FORECAST_ROWS:
            break

        target_date = date.today() + timedelta(days=day_offset)
        weekday_number = target_date.weekday()

        if weekday_number == 6:
            continue

        previous_week_date = target_date - timedelta(days=7)
        previous_week_records = df[df["data_date"] == previous_week_date]

        if previous_week_records.empty:
            continue

        turns = sort_turns(previous_week_records["turno"].dropna().unique().tolist())

        for turn in turns:
            if len(forecast_rows) >= MAX_FORECAST_ROWS:
                break

            previous_week_turn = previous_week_records[
                previous_week_records["turno"] == turn
            ]

            if previous_week_turn.empty:
                continue

            same_weekday_turn_history = df[
                (df["dia_semana"] == weekday_number) & (df["turno"] == turn)
            ].tail(6)

            previous_meals = previous_week_turn["refeicoes_produzidas"].mean()
            previous_waste_rate = previous_week_turn["taxa_desperdicio"].mean()

            historical_meals = same_weekday_turn_history["refeicoes_produzidas"].mean()
            historical_waste_rate = same_weekday_turn_history["taxa_desperdicio"].mean()

            if pd.isna(historical_meals):
                historical_meals = previous_meals

            if pd.isna(historical_waste_rate):
                historical_waste_rate = previous_waste_rate

            base_meals = (previous_meals * 0.70) + (historical_meals * 0.30)
            base_waste_rate = (previous_waste_rate * 0.70) + (historical_waste_rate * 0.30)

            recommended_plates, success_rate, waste_rate = calculate_recommendation(
                base_meals,
                base_waste_rate,
            )

            recommended_kg = recommended_plates * PORTION_KG
            food_suggestion = choose_food_suggestion(
                previous_week_turn,
                same_weekday_turn_history,
            )

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
                    "Base usada": previous_week_date.strftime("%d/%m/%Y"),
                }
            )

    return pd.DataFrame(forecast_rows)


def show_prediction_message(forecast_df: pd.DataFrame) -> None:
    tomorrow = date.today() + timedelta(days=1)
    tomorrow_label = WEEKDAYS[tomorrow.weekday()]
    tomorrow_formatted = tomorrow.strftime("%d/%m/%Y")

    tomorrow_rows = forecast_df[forecast_df["Data"] == tomorrow_formatted]

    if not tomorrow_rows.empty:
        total_plates = tomorrow_rows["Pratos"].sum()
        total_kg = tomorrow_rows["Kg"].sum()
        avg_success = tomorrow_rows["Sucesso"].mean()

        st.info(
            f"Recomendação para **{tomorrow_label} ({tomorrow_formatted})**: "
            f"preparar **{int(total_plates)} pratos**, aproximadamente "
            f"**{total_kg:.1f} kg**, considerando os turnos cadastrados. "
            f"Sucesso médio previsto: **{avg_success:.1f}%**."
        )
        return

    if tomorrow.weekday() == 6:
        st.warning(
            f"Não há previsão para **{tomorrow_label} ({tomorrow_formatted})**, "
            "pois domingo não é considerado dia letivo no planejamento."
        )
        return

    previous_week = tomorrow - timedelta(days=7)

    st.warning(
        f"Ainda não há base suficiente para prever **{tomorrow_label} "
        f"({tomorrow_formatted})**. Para gerar essa previsão, o sistema precisa "
        f"de um registro equivalente na semana anterior, em **{previous_week.strftime('%d/%m/%Y')}**."
    )

    if not forecast_df.empty:
        next_row = forecast_df.iloc[0]
        same_date_rows = forecast_df[forecast_df["Data"] == next_row["Data"]]

        total_plates = same_date_rows["Pratos"].sum()
        total_kg = same_date_rows["Kg"].sum()

        st.info(
            f"Próxima previsão disponível: **{next_row['Dia da semana']} "
            f"({next_row['Data']})**. Recomendação total: **{int(total_plates)} pratos** "
            f"e aproximadamente **{total_kg:.1f} kg**."
        )


def show_prediction(school_id: int) -> None:
    page_header(
        "Previsão Inteligente",
        "Recomendações de preparo com base no histórico real da produção alimentar, turno, cardápio e desperdício.",
        "Planejamento alimentar",
    )

    production = db.production_df(school_id)

    if production.empty:
        st.info(
            "Ainda não há dados suficientes para gerar previsões. "
            "Registre produções alimentares primeiro."
        )
        return

    df = prepare_history(production)

    if df.empty:
        st.info(
            "Ainda não há registros válidos de produção para calcular a previsão."
        )
        return

    if len(df) < 3:
        st.warning(
            "Cadastre mais registros de produção para melhorar a qualidade da previsão."
        )

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

    if forecast_df.empty:
        st.warning(
            "Não há histórico recente suficiente para montar a previsão da próxima semana. "
            "Cadastre registros de produção por dia e turno para que o sistema gere recomendações automáticas."
        )
        return

    show_prediction_message(forecast_df)

    st.subheader("Tabela inteligente de previsão")

    table_df = forecast_df.copy()
    table_df = table_df.drop(columns=["Kg"])
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
            "Sucesso": st.column_config.TextColumn("Sucesso previsto"),
            "Desperdício": st.column_config.TextColumn("Desperdício previsto"),
            "Base usada": st.column_config.TextColumn("Registro usado como base"),
        },
    )

    st.markdown("---")

    st.subheader("Recomendações automáticas")

    best_day = forecast_df.sort_values("Desperdício").iloc[0]
    attention_day = forecast_df.sort_values("Desperdício", ascending=False).iloc[0]

    col1, col2 = st.columns(2)

    with col1:
        st.success(
            f"Melhor cenário previsto: **{best_day['Dia da semana']} "
            f"({best_day['Data']}) - {best_day['Turno']}**, com desperdício estimado de "
            f"**{best_day['Desperdício']:.1f}%**."
        )

    with col2:
        st.warning(
            f"Dia que exige mais atenção: **{attention_day['Dia da semana']} "
            f"({attention_day['Data']}) - {attention_day['Turno']}**, com desperdício estimado de "
            f"**{attention_day['Desperdício']:.1f}%**."
        )

    st.markdown("---")

    st.subheader("Como o sistema calcula a previsão")

    st.markdown(
        """
        <div class="info-card">
            <p>
                A previsão do Renewtri utiliza apenas registros reais da produção alimentar.
                Para prever um dia futuro, o sistema procura o registro equivalente da semana anterior,
                no mesmo dia da semana e no mesmo turno.
            </p>
            <p>
                Por exemplo: para prever uma sexta-feira, o sistema verifica se existe produção registrada
                na sexta-feira anterior. Se não existir, ele não gera uma recomendação artificial para esse dia.
            </p>
            <p>
                Domingos não entram no planejamento. Sábados só aparecem quando existe histórico de aula
                ou produção registrada em sábado. A tabela é limitada a no máximo 14 previsões para manter
                a visualização organizada.
            </p>
            <p>
                A quantidade em kg considera uma porção média de <strong>0,45 kg por prato</strong>.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
