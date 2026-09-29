"""Connessione e transazioni del database prenotazioni."""

from contextlib import contextmanager

from config import DATABASE_URL

try:
    import psycopg
    from psycopg.rows import dict_row
except ModuleNotFoundError:  # La chat FAQ locale funziona anche senza Supabase.
    psycopg = None
    dict_row = None


_LOCK_ID = 734512  # serializza le scritture delle prenotazioni


@contextmanager
def db(write: bool = False):
    if psycopg is None:
        raise RuntimeError(
            "Installa psycopg per usare le prenotazioni Supabase."
        )

    if not DATABASE_URL:
        raise RuntimeError(
            "Manca la variabile DATABASE_URL "
            "(stringa di connessione di Supabase)."
        )

    conn = psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row,  # type: ignore[arg-type]
        prepare_threshold=None,
        connect_timeout=10,
    )

    try:
        if write:
            conn.execute(
                "SELECT pg_advisory_xact_lock(%s)",
                (_LOCK_ID,),
            )

        yield conn
        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def init_db():
    with db() as c:
        row = c.execute(
            "SELECT to_regclass('public.bookings') AS table_name"
        ).fetchone()
        table_name = row[0] if row is not None else None

        if not table_name:
            raise RuntimeError(
                "La tabella 'bookings' non esiste: "
                "esegui crea_tabelle.sql nel SQL Editor di Supabase."
            )

