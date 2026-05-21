import hashlib
import random
import re
import string
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st


APP_NAME = "Renewtri"
PRIMARY = "#0f9f6e"
SECONDARY = "#0b6fb8"
LIGHT_BG = "#f5fbfa"


def apply_custom_css() -> None:
    st.markdown(
        f"""
        <style>
        :root {{
            --renewtri-green: {PRIMARY};
            --renewtri-blue: {SECONDARY};
            --renewtri-bg: {LIGHT_BG};
            --renewtri-text: #102a43;
            --renewtri-muted: #60768a;
            --renewtri-border: #d9e8e4;
        }}

        .stApp {{
            background: linear-gradient(180deg, rgba(245,251,250,.96), rgba(255,255,255,.98) 38%);
            color: var(--renewtri-text);
        }}

        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #073b4c, #095a63 55%, #0f766e);
        }}

        [data-testid="stSidebar"] * {{
            color: #eefdf8;
        }}

        h1, h2, h3 {{
            letter-spacing: 0;
            color: #0b2f3a;
        }}

        .renewtri-hero {{
            padding: 1.25rem 1.35rem;
            border: 1px solid rgba(15,159,110,.18);
            background: linear-gradient(135deg, rgba(255,255,255,.98), rgba(235,249,245,.96));
            border-radius: 8px;
            box-shadow: 0 16px 36px rgba(7,59,76,.08);
            margin-bottom: 1rem;
        }}

        .renewtri-hero .eyebrow {{
            color: var(--renewtri-green);
            font-size: .75rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: .08em;
            margin-bottom: .35rem;
        }}

        .renewtri-hero .subtitle {{
            color: var(--renewtri-muted);
            max-width: 840px;
            margin-top: .35rem;
            line-height: 1.55;
        }}

        .metric-card {{
            padding: 1rem;
            border-radius: 8px;
            background: rgba(255,255,255,.96);
            border: 1px solid var(--renewtri-border);
            box-shadow: 0 10px 28px rgba(7,59,76,.07);
            min-height: 112px;
        }}

        .metric-card .label {{
            color: var(--renewtri-muted);
            font-size: .8rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: .04em;
        }}

        .metric-card .value {{
            color: #063b46;
            font-size: 1.75rem;
            font-weight: 820;
            line-height: 1.15;
            margin-top: .35rem;
            word-break: break-word;
        }}

        .metric-card .help {{
            color: var(--renewtri-muted);
            font-size: .84rem;
            margin-top: .25rem;
        }}

        .info-card {{
            height: 100%;
            padding: 1rem;
            border-radius: 8px;
            background: #ffffff;
            border: 1px solid var(--renewtri-border);
            box-shadow: 0 10px 26px rgba(7,59,76,.06);
        }}

        .badge {{
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: .2rem .65rem;
            background: rgba(15,159,110,.12);
            color: #076447;
            font-size: .78rem;
            font-weight: 750;
            border: 1px solid rgba(15,159,110,.2);
        }}

        .stButton > button {{
            border-radius: 8px;
            border: 1px solid rgba(15,159,110,.25);
            background: linear-gradient(135deg, var(--renewtri-green), var(--renewtri-blue));
            color: white;
            font-weight: 750;
            min-height: 2.6rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str, eyebrow: str = "Renewtri") -> None:
    st.markdown(
        f"""
        <section class="renewtri-hero">
            <div class="eyebrow">{eyebrow}</div>
            <h1>{title}</h1>
            <div class="subtitle">{subtitle}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, help_text: str = "") -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="label">{label}</div>
            <div class="value">{value}</div>
            <div class="help">{help_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def validate_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


def normalize_cnpj(cnpj: str) -> str:
    return re.sub(r"\D", "", cnpj or "")


def format_cnpj(cnpj: str) -> str:
    digits = normalize_cnpj(cnpj)

    if len(digits) != 14:
        return cnpj

    return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"


def validate_cnpj(cnpj: str) -> bool:
    digits = normalize_cnpj(cnpj)

    if len(digits) != 14 or digits == digits[0] * 14:
        return False

    def calc_digit(base: str, weights: list[int]) -> str:
        total = sum(int(num) * weight for num, weight in zip(base, weights))
        remainder = total % 11
        return "0" if remainder < 2 else str(11 - remainder)

    first_weights = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    second_weights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    first_digit = calc_digit(digits[:12], first_weights)
    second_digit = calc_digit(digits[:12] + first_digit, second_weights)

    return digits[-2:] == first_digit + second_digit


def generate_school_code(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]", "", name.upper())[:3].ljust(3, "R")
    suffix = "".join(random.choices(string.digits, k=4))
    return f"{cleaned}-{suffix}"


def today_iso() -> str:
    return date.today().isoformat()


def as_date(value: str | date | datetime) -> date:
    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    return datetime.strptime(str(value), "%Y-%m-%d").date()


def default_date_range(days: int = 30) -> tuple[date, date]:
    end = date.today()
    start = end - timedelta(days=days)
    return start, end


def format_kg(value: float) -> str:
    return f"{value:,.1f} kg".replace(",", "X").replace(".", ",").replace("X", ".")


def format_int(value: float) -> str:
    return f"{int(round(value)):,.0f}".replace(",", ".")


def format_percent(value: float) -> str:
    return f"{value:.1f}%".replace(".", ",")


def turnos() -> list[str]:
    return ["Manhã", "Tarde", "Noite", "Integral"]


def plotly_layout(fig, title: str | None = None):
    fig.update_layout(
        title=title,
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=55 if title else 25, b=25),
        font=dict(family="Inter, Segoe UI, Arial", color="#102a43"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#e8f1ef")

    return fig


def current_school_id() -> int | None:
    return st.session_state.get("school_id")


def current_user_role() -> str | None:
    return st.session_state.get("role")


def prepare_table_display(
    df: pd.DataFrame,
    hidden_columns: list[str] | None = None,
    date_columns: list[str] | None = None,
) -> pd.DataFrame:
    display_df = df.copy()

    for column in hidden_columns or []:
        if column in display_df.columns:
            display_df = display_df.drop(columns=[column])

    for column in date_columns or []:
        if column in display_df.columns:
            display_df[column] = pd.to_datetime(
                display_df[column],
                errors="coerce",
            ).dt.strftime("%d/%m/%Y")

    return display_df