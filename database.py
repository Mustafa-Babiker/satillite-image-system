import os
import sqlite3
import psycopg2

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.db")


def get_connection():
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        try:
            return psycopg2.connect(database_url, sslmode="require")
        except Exception as exc:
            print(f"Postgres connection via DATABASE_URL failed: {exc}")

    try:
        conn_kwargs = {
            "host": os.environ.get("DB_HOST", "localhost"),
            "database": os.environ.get("DB_NAME", "agriculture_system"),
            "user": os.environ.get("DB_USER", "postgres"),
            "password": os.environ.get("DB_PASSWORD", "كلمة_مرور_PostgreSQL")
        }
        if conn_kwargs["host"] != "localhost":
            conn_kwargs["sslmode"] = "require"
        return psycopg2.connect(**conn_kwargs)
    except Exception as exc:
        print(f"Postgres unavailable, using SQLite fallback: {exc}")
        return sqlite3.connect(DB_PATH)