"""Neon Postgres helpers for the lead automation. One job: read/write leads."""
import os
from typing import Optional

import psycopg2
import psycopg2.extras


def get_connection():
    dsn = os.environ["NEON_CONNECTION_STRING"]
    return psycopg2.connect(dsn)


def init_schema():
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path) as f:
        schema_sql = f.read()
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(schema_sql)
        conn.commit()


def insert_leads(leads):
    """Insert leads, skipping duplicates by place_id. Returns the newly inserted rows (with id)."""
    if not leads:
        return []
    with get_connection() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        new_rows = []
        for lead in leads:
            cur.execute(
                """
                INSERT INTO leads (company_name, category, address, city, phone, website,
                                   email, contact_name, contact_role, source, place_id)
                VALUES (%(company_name)s, %(category)s, %(address)s, %(city)s, %(phone)s,
                        %(website)s, %(email)s, %(contact_name)s, %(contact_role)s,
                        %(source)s, %(place_id)s)
                ON CONFLICT (place_id) DO NOTHING
                RETURNING *
                """,
                lead,
            )
            row = cur.fetchone()
            if row:
                new_rows.append(dict(row))
        conn.commit()
        return new_rows


def save_email_message(lead_id: int, subject: str, body: str):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE leads SET email_subject = %s, email_body = %s WHERE id = %s",
            (subject, body, lead_id),
        )
        conn.commit()


def fetch_leads(status=None, limit=200):
    query = "SELECT * FROM leads"
    params = ()
    if status:
        query += " WHERE status = %s"
        params = (status,)
    query += " ORDER BY scraped_at DESC LIMIT %s"
    params = params + (limit,)
    with get_connection() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]


def update_lead_status(lead_id: int, status: str):
    with get_connection() as conn, conn.cursor() as cur:
        if status == "contacted":
            cur.execute(
                "UPDATE leads SET status = %s, contacted_at = now() WHERE id = %s",
                (status, lead_id),
            )
        else:
            cur.execute("UPDATE leads SET status = %s WHERE id = %s", (status, lead_id))
        conn.commit()
