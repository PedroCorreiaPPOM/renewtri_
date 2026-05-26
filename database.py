import sqlite3
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from utils import generate_school_code, hash_password, normalize_cnpj


DB_PATH = Path(__file__).with_name("renewtri.sqlite3")

DEMO_SCHOOL_EMAIL = "escola@renewtri.demo"
DEMO_EMPLOYEE_EMAIL = "robertina@renewtri.demo"
DEMO_PRODUCTION_NOTE = "Registro demonstrativo para acompanhamento do MVP."
DEMO_INVENTORY_NOTE = "Entrada demonstrativa para controle de estoque."
DEMO_SEED_MARKER = "demo_operational_seed_v2"


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
    school_id = ensure_demo_school(conn)
    employee_id = ensure_demo_employees(conn, school_id)
    if not demo_seed_applied(conn, school_id):
        seed_demo_operational_data(conn, school_id, employee_id)
        mark_demo_seed_applied(conn, school_id)
    conn.commit()


def ensure_demo_school(conn: sqlite3.Connection) -> int:
    school = conn.execute(
        "SELECT id FROM escolas WHERE lower(email) = lower(?)",
        (DEMO_SCHOOL_EMAIL,),
    ).fetchone()

    if school:
        conn.execute(
            """
            UPDATE escolas
            SET nome = ?, cnpj = ?, codigo_inep = ?
            WHERE id = ?
            """,
            (
                "CETI Prefeito João Mendes Olímpio de Melo",
                normalize_cnpj("11.222.333/0001-81"),
                "22123456",
                school["id"],
            ),
        )
        return int(school["id"])

    school_code = generate_school_code("CETI Prefeito Joao Mendes Olimpo de Melo")
    while conn.execute(
        "SELECT id FROM escolas WHERE upper(codigo_escola) = upper(?)",
        (school_code,),
    ).fetchone():
        school_code = generate_school_code("CETI Prefeito Joao Mendes Olimpo de Melo")

    cursor = conn.execute(
        """
        INSERT INTO escolas (nome, email, cnpj, codigo_inep, codigo_escola, senha_hash)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "CETI Prefeito João Mendes Olímpio de Melo",
            DEMO_SCHOOL_EMAIL,
            normalize_cnpj("11.222.333/0001-81"),
            "22123456",
            school_code,
            hash_password("renewtri123"),
        ),
    )
    return int(cursor.lastrowid)


def ensure_demo_employees(conn: sqlite3.Connection, school_id: int) -> int | None:
    employees = [
        ("Robertina Alves", DEMO_EMPLOYEE_EMAIL),
        ("Maria do Socorro", "socorro@renewtri.demo"),
        ("Ana Clara Santos", "ana@renewtri.demo"),
    ]

    for name, email in employees:
        employee = conn.execute(
            "SELECT id FROM merendeiras WHERE lower(email) = lower(?)",
            (email,),
        ).fetchone()

        if employee:
            conn.execute(
                """
                UPDATE merendeiras
                SET escola_id = ?, nome = ?, senha_hash = ?
                WHERE id = ?
                """,
                (school_id, name, hash_password("merenda123"), employee["id"]),
            )
            continue

        conn.execute(
            """
            INSERT INTO merendeiras (escola_id, nome, email, senha_hash, ativo)
            VALUES (?, ?, ?, ?, 1)
            """,
            (school_id, name, email, hash_password("merenda123")),
        )

    employee = conn.execute(
        """
        SELECT id
        FROM merendeiras
        WHERE escola_id = ? AND lower(email) = lower(?)
        """,
        (school_id, DEMO_EMPLOYEE_EMAIL),
    ).fetchone()

    return int(employee["id"]) if employee else None


def recent_school_days(limit: int) -> list[date]:
    days: list[date] = []
    current = date.today()

    while len(days) < limit:
        if current.weekday() < 5:
            days.append(current)
        current -= timedelta(days=1)

    return sorted(days)


def clear_demo_operational_data(conn: sqlite3.Connection, school_id: int) -> None:
    demo_productions = conn.execute(
        """
        SELECT id
        FROM producao_alimentar
        WHERE escola_id = ? AND observacoes = ?
        """,
        (school_id, DEMO_PRODUCTION_NOTE),
    ).fetchall()

    production_ids = [row["id"] for row in demo_productions]
    if production_ids:
        placeholders = ",".join("?" for _ in production_ids)
        conn.execute(
            f"DELETE FROM desperdicio WHERE producao_id IN ({placeholders})",
            tuple(production_ids),
        )
        conn.execute(
            f"DELETE FROM producao_alimentar WHERE id IN ({placeholders})",
            tuple(production_ids),
        )

    conn.execute(
        """
        DELETE FROM alimentos_recebidos
        WHERE escola_id = ? AND observacoes = ?
        """,
        (school_id, DEMO_INVENTORY_NOTE),
    )


def demo_seed_applied(conn: sqlite3.Connection, school_id: int) -> bool:
    marker = conn.execute(
        """
        SELECT id
        FROM acessos
        WHERE escola_id = ?
          AND usuario_tipo = 'sistema'
          AND usuario_email = ?
          AND mensagem = ?
        LIMIT 1
        """,
        (school_id, DEMO_SCHOOL_EMAIL, DEMO_SEED_MARKER),
    ).fetchone()
    return marker is not None


def mark_demo_seed_applied(conn: sqlite3.Connection, school_id: int) -> None:
    conn.execute(
        """
        INSERT INTO acessos (escola_id, usuario_tipo, usuario_email, sucesso, mensagem)
        VALUES (?, 'sistema', ?, 1, ?)
        """,
        (school_id, DEMO_SCHOOL_EMAIL, DEMO_SEED_MARKER),
    )


def seed_demo_operational_data(
    conn: sqlite3.Connection,
    school_id: int,
    employee_id: int | None,
) -> None:
    clear_demo_operational_data(conn, school_id)

    turns = ["Manhã", "Tarde"]
    menus = [
        "Arroz, feijão, frango e salada",
        "Cuscuz, ovos e suco",
        "Macarrão, carne moída e legumes",
        "Baião de dois, frango e frutas",
        "Arroz, carne, abóbora e suco",
        "Feijão tropeiro, arroz e banana",
        "Sopa nutritiva, pão e fruta",
    ]
    meals = [176, 168, 184, 172, 190, 178, 182, 170, 186, 174, 188, 180, 192, 176]
    wastes = [8.4, 7.8, 6.9, 6.4, 8.1, 7.2, 5.9, 5.5, 7.0, 6.1, 6.8, 5.7, 7.4, 6.0]

    for index, current in enumerate(recent_school_days(7)):
        for turn_index, turn in enumerate(turns):
            row_index = (index * len(turns)) + turn_index
            cursor = conn.execute(
                """
                INSERT INTO producao_alimentar
                    (escola_id, merendeira_id, data, turno, refeicoes_produzidas, alimentos_utilizados, observacoes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    school_id,
                    employee_id,
                    current.isoformat(),
                    turn,
                    meals[row_index],
                    menus[row_index % len(menus)],
                    DEMO_PRODUCTION_NOTE,
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
                    turn,
                    wastes[row_index],
                    "Sobra demonstrativa após a distribuição.",
                ),
            )

    inventory = [
        ("Cooperativa Sertão Verde", "Arroz", 22, 45),
        ("Grãos Piauí", "Feijão", 18, 50),
        ("Frigorífico Boa Mesa", "Frango", 14, 12),
        ("Fornecedor Nordeste", "Cuscuz", 16, 80),
        ("Hortifruti Escolar", "Legumes", 12, 7),
        ("Laticínios União", "Leite", 24, 9),
        ("Padaria Escola", "Pão", 10, 5),
    ]

    for index in range(14):
        current = date.today() - timedelta(days=index)
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
                qty + (index % 3) * 2,
                (current + timedelta(days=valid_days)).isoformat(),
                DEMO_INVENTORY_NOTE,
            ),
        )


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
    return fetch_one(
        "SELECT * FROM escolas WHERE upper(codigo_escola) = upper(?)",
        (code.strip(),),
    )


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


def delete_production(production_id: int, school_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            DELETE FROM desperdicio
            WHERE producao_id IN (
                SELECT id
                FROM producao_alimentar
                WHERE id = ? AND escola_id = ?
            )
            """,
            (production_id, school_id),
        )
        conn.execute(
            "DELETE FROM producao_alimentar WHERE id = ? AND escola_id = ?",
            (production_id, school_id),
        )
        conn.commit()


def delete_inventory(inventory_id: int, school_id: int) -> None:
    execute(
        "DELETE FROM alimentos_recebidos WHERE id = ? AND escola_id = ?",
        (inventory_id, school_id),
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
