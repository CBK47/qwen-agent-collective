"""Brain namespace contract — single source of truth for collection/table names.

Agents import these constants instead of hard-coding strings. See
shared/README.md for the ownership table. `shared.*` is readable by all agents;
each agent also owns a private namespace.
"""

import psycopg2
from psycopg2 import sql

# Shared, readable by all agents (Postgres)
SHARED_GLOSSARY = "shared.glossary"            # owner: open-translate
SHARED_CODE_CONVENTIONS = "shared.code-conventions"  # owner: git-committer

# Private agent namespaces (Qdrant unless noted)
ECHO_PRIVATE = "echo.private"                  # memory-echo
GIT_COMMITTER_PRIVATE = "git-committer.private"  # git-committer
OPEN_TRANSLATE_PRIVATE = "open-translate.private"  # open-translate
SKIPPY_PRIVATE = "skippy.private"              # skippy-concierge
SHOWRUNNER_PRIVATE = "showrunner.private"      # showrunner (Qdrant + Postgres)

# Skippy device data
DEVICES = "devices"                            # Postgres
SKIPPY_DEVICE_MANUALS = "skippy_device_manuals"  # Qdrant

def get_glossary() -> dict[str, str]:
    """Retrieve glossary terms and translations from the database.

    Returns:
        dict[str, str]: A dictionary mapping terms to their translations.
    """
    conn = psycopg2.connect("dbname=translation_db user=app")
    cur = conn.cursor()
    cur.execute(sql.SQL("SELECT term, translation FROM {}").format(sql.Identifier(SHARED_GLOSSARY)))
    rows = cur.fetchall()
    return {term: translation for term, translation in rows}

def update_glossary(term: str, translation: str) -> None:
    """Update or insert a glossary term and translation.

    Args:
        term (str): The term to update or insert.
        translation (str): The new translation for the term.
    """
    conn = psycopg2.connect("dbname=translation_db user=app")
    cur = conn.cursor()
    cur.execute(sql.SQL("INSERT INTO {} (term, translation) VALUES (%s, %s) ON CONFLICT (term) DO UPDATE SET translation = %s").format(sql.Identifier(SHARED_GLOSSARY)), (term, translation, translation))
    conn.commit()
