import sqlite3
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from utils import generate_school_code, hash_password, normalize_cnpj


DB_PATH = Path(__file__).with_name("renewtri.sqlite3")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = MEMORY")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        create_tables(conn)
        seed_demo_data(conn)


def create_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS escolas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            cnpj TEXT NOT NULL UNIQUE,
            codigo_inep TEXT NOT NULL,
            codigo_escola TEXT NOT NULL UNIQUE,
            senha_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS merendeiras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            escola_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha_hash TEXT NOT NULL,
            ativo INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (escola_id) REFERENCES escolas(id)
        );

        CREATE TABLE IF NOT EXISTS producao_alimentar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            escola_id INTEGER NOT NULL,
            merendeira_id INTEGER,
            data TEXT NOT NULL,
            turno TEXT NOT NULL,
            refeicoes_produzidas INTEGER NOT NULL,
            alimentos_utilizados TEXT NOT NULL,
            observacoes TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (escola_id) REFERENCES escolas(id),
            FOREIGN KEY (merendeira_id) REFERENCES merendeiras(id)
        );

        CREATE TABLE IF NOT EXISTS alimentos_recebidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            escola_id INTEGER NOT NULL,
            data TEXT NOT NULL,
            fornecedor TEXT NOT NULL,
            alimento TEXT NOT NULL,
            quantidade_kg REAL NOT NULL,
            validade TEXT NOT NULL,
            observacoes TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (escola_id) REFERENCES escolas(id)
        );

        CREATE TABLE IF NOT EXISTS desperdicio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            escola_id INTEGER NOT NULL,
            producao_id INTEGER,
            data TEXT NOT NULL,
            turno TEXT NOT NULL,
            quantidade_kg REAL NOT NULL,
            observacoes TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (escola_id) REFERENCES escolas(id),
            FOREIGN KEY (producao_id) REFERENCES producao_alimentar(id)
        );

        CREATE TABLE IF NOT EXISTS relatorios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            escola_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            data_inicio TEXT NOT NULL,
            data_fim TEXT NOT NULL,
            resumo TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (escola_id) REFERENCES escolas(id)
        );

        CREATE TABLE IF NOT EXISTS acessos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            escola_id INTEGER,
            usuario_tipo TEXT NOT NULL,
            usuario_email TEXT NOT NULL,
            sucesso INTEGER NOT NULL,
            mensagem TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (escola_id) REFERENCES escolas(id)
        );
        """
    )


def seed_demo_data(conn: sqlite3.Connection) -> None:
    exists = conn.execute("SELECT COUNT(*) FROM escolas").fetchone()[0]
    if exists:
        return

    school_code = generate_school_code("CETI Prefeito Joao Mendes Olimpo de Melo")
    conn.execute(
        """
        INSERT INTO escolas (nome, email, cnpj, codigo_inep, codigo_escola, senha_hash)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "CETI Prefeito João Mendes Olímpio de Melo",
            "escola@renewtri.demo",
            normalize_cnpj("11.222.333/0001-81"),
            "22123456",
            school_code,
            hash_password("renewtri123"),
        ),
    )
    school_id = conn.execute("SELECT id FROM escolas WHERE email = ?", ("escola@renewtri.demo",)).fetchone()[0]

    employees = [
        ("Robertina Alves", "robertina@renewtri.demo"),
        ("Maria do Socorro", "socorro@renewtri.demo"),
        ("Ana Clara Santos", "ana@renewtri.demo"),
    ]
    for name, email in employees:
        conn.execute(
            """
            INSERT INTO merendeiras (escola_id, nome, email, senha_hash, ativo)
            VALUES (?, ?, ?, ?, 1)
            """,
            (school_id, name, email, hash_password("merenda123")),
        )

    merendeira_id = conn.execute(
        "SELECT id FROM merendeiras WHERE email = ?", ("robertina@renewtri.demo",)
    ).fetchone()[0]

    base = date.today() - timedelta(days=80)
    turnos = ["Manhã", "Tarde"]
    meals = [178, 184, 176, 190, 168, 162, 172, 181, 186, 193, 174, 166]
    wastes = [17.5, 14.2, 12.8, 11.4, 10.7, 9.6, 9.2, 8.8, 8.1, 7.4, 7.0, 6.5]
    foods = [
        "Arroz, feijão, frango e salada",
        "Cuscuz, ovos e suco",
        "Macarrão, carne moída e legumes",
        "Baião de dois, frango e frutas",
    ]

    for index in range(72):
        current = base + timedelta(days=index)
        if current.weekday() >= 5:
            continue
        turno = turnos[index % len(turnos)]
        produced = meals[index % len(meals)] + (index % 6) * 3
        waste = max(3.8, wastes[index % len(wastes)] - (index // 12) * 0.8)
        cursor = conn.execute(
            """
            INSERT INTO producao_alimentar
                (escola_id, merendeira_id, data, turno, refeicoes_produzidas, alimentos_utilizados, observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                school_id,
                merendeira_id,
                current.isoformat(),
                turno,
                produced,
                foods[index % len(foods)],
                "Registro demonstrativo para acompanhamento do MVP.",
            ),
        )
        production_id = cursor.lastrowid
        conn.execute(
            """
            INSERT INTO desperdicio (escola_id, producao_id, data, turno, quantidade_kg, observacoes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                school_id,
                production_id,
                current.isoformat(),
                turno,
                round(waste, 2),
                "Sobra registrada após a distribuição.",
            ),
        )

    inventory = [
        ("Cooperativa Sertão Verde", "Arroz", 20, 45),
        ("Frigorífico Boa Mesa", "Carne", 10, 18),
        ("Fornecedor Nordeste", "Cuscuz", 15, 90),
        ("Hortifruti Escolar", "Legumes", 12, 7),
        ("Grãos Piauí", "Feijão", 18, 60),
        ("Laticínios União", "Leite", 25, 10),
    ]
    for index in range(24):
        current = base + timedelta(days=index * 3)
        supplier, food, qty, valid_days = inventory[index % len(inventory)]
        conn.execute(
            """
            INSERT INTO alimentos_recebidos
                (escola_id, data, fornecedor, alimento, quantidade_kg, validade, observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                school_id,
                current.isoformat(),
                supplier,
                food,
                qty + (index % 4) * 2,
                (current + timedelta(days=valid_days)).isoformat(),
                "Entrada demonstrativa para controle de estoque.",
            ),
        )

    conn.commit()


def register_access(
    user_type: str,
    email: str,
    success: bool,
    message: str = "",
    school_id: int | None = None,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO acessos (escola_id, usuario_tipo, usuario_email, sucesso, mensagem)
            VALUES (?, ?, ?, ?, ?)
            """,
            (school_id, user_type, email, int(success), message),
        )


def fetch_one(query: str, params: tuple = ()) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute(query, params).fetchone()


def execute(query: str, params: tuple = ()) -> int:
    with get_connection() as conn:
        cursor = conn.execute(query, params)
        conn.commit()
        return cursor.lastrowid


def read_df(query: str, params: tuple = ()) -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=params)


def school_by_email(email: str):
    return fetch_one("SELECT * FROM escolas WHERE lower(email) = lower(?)", (email,))


def school_by_email_and_cnpj(email: str, cnpj: str):
    return fetch_one(
        "SELECT * FROM escolas WHERE lower(email) = lower(?) AND cnpj = ?",
        (email, normalize_cnpj(cnpj)),
    )


def school_by_code(code: str):
    return fetch_one("SELECT * FROM escolas WHERE upper(codigo_escola) = upper(?)", (code.strip(),))


def employee_by_email(email: str):
    return fetch_one(
        """
        SELECT m.*, e.codigo_escola, e.nome AS escola_nome
        FROM merendeiras m
        JOIN escolas e ON e.id = m.escola_id
        WHERE lower(m.email) = lower(?)
        """,
        (email,),
    )


def get_school(school_id: int):
    return fetch_one("SELECT * FROM escolas WHERE id = ?", (school_id,))


def cnpj_exists(cnpj: str) -> bool:
    row = fetch_one("SELECT id FROM escolas WHERE cnpj = ?", (normalize_cnpj(cnpj),))
    return row is not None


def create_school(nome: str, email: str, cnpj: str, codigo_inep: str, senha: str) -> str:
    code = generate_school_code(nome)
    while school_by_code(code):
        code = generate_school_code(nome)
    execute(
        """
        INSERT INTO escolas (nome, email, cnpj, codigo_inep, codigo_escola, senha_hash)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (nome, email, normalize_cnpj(cnpj), codigo_inep, code, hash_password(senha)),
    )
    return code


def create_employee(school_id: int, nome: str, email: str, senha: str) -> int:
    return execute(
        """
        INSERT INTO merendeiras (escola_id, nome, email, senha_hash, ativo)
        VALUES (?, ?, ?, ?, 1)
        """,
        (school_id, nome, email, hash_password(senha)),
    )


def set_employee_status(employee_id: int, active: bool, school_id: int) -> None:
    execute(
        "UPDATE merendeiras SET ativo = ? WHERE id = ? AND escola_id = ?",
        (int(active), employee_id, school_id),
    )


def employees_df(school_id: int) -> pd.DataFrame:
    return read_df(
        """
        SELECT id, nome, email, ativo, created_at
        FROM merendeiras
        WHERE escola_id = ?
        ORDER BY nome
        """,
        (school_id,),
    )


def insert_production(
    school_id: int,
    employee_id: int | None,
    data: str,
    turno: str,
    refeicoes: int,
    alimentos: str,
    desperdicio_kg: float,
    observacoes: str,
) -> None:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO producao_alimentar
                (escola_id, merendeira_id, data, turno, refeicoes_produzidas, alimentos_utilizados, observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (school_id, employee_id, data, turno, refeicoes, alimentos, observacoes),
        )
        production_id = cursor.lastrowid
        conn.execute(
            """
            INSERT INTO desperdicio (escola_id, producao_id, data, turno, quantidade_kg, observacoes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (school_id, production_id, data, turno, desperdicio_kg, observacoes),
        )
        conn.commit()


def insert_inventory(
    school_id: int,
    data: str,
    fornecedor: str,
    alimento: str,
    quantidade_kg: float,
    validade: str,
    observacoes: str,
) -> None:
    execute(
        """
        INSERT INTO alimentos_recebidos
            (escola_id, data, fornecedor, alimento, quantidade_kg, validade, observacoes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (school_id, data, fornecedor, alimento, quantidade_kg, validade, observacoes),
    )


def production_df(school_id: int, start: str | None = None, end: str | None = None) -> pd.DataFrame:
    query = """
        SELECT
            p.id,
            p.data,
            p.turno,
            p.refeicoes_produzidas,
            p.alimentos_utilizados,
            COALESCE(d.quantidade_kg, 0) AS desperdicio_kg,
            p.observacoes,
            COALESCE(m.nome, 'Instituição') AS registrado_por
        FROM producao_alimentar p
        LEFT JOIN desperdicio d ON d.producao_id = p.id
        LEFT JOIN merendeiras m ON m.id = p.merendeira_id
        WHERE p.escola_id = ?
    """
    params: list = [school_id]
    if start:
        query += " AND p.data >= ?"
        params.append(start)
    if end:
        query += " AND p.data <= ?"
        params.append(end)
    query += " ORDER BY p.data DESC, p.id DESC"
    return read_df(query, tuple(params))


def inventory_df(school_id: int, start: str | None = None, end: str | None = None) -> pd.DataFrame:
    query = """
        SELECT id, data, fornecedor, alimento, quantidade_kg, validade, observacoes
        FROM alimentos_recebidos
        WHERE escola_id = ?
    """
    params: list = [school_id]
    if start:
        query += " AND data >= ?"
        params.append(start)
    if end:
        query += " AND data <= ?"
        params.append(end)
    query += " ORDER BY data DESC, id DESC"
    return read_df(query, tuple(params))


def save_report(school_id: int, tipo: str, start: str, end: str, resumo: str) -> None:
    execute(
        """
        INSERT INTO relatorios (escola_id, tipo, data_inicio, data_fim, resumo)
        VALUES (?, ?, ?, ?, ?)
        """,
        (school_id, tipo, start, end, resumo),
    )
