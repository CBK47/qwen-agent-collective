"""Brain namespace contract — single source of truth for collection/table names.

Agents import these constants instead of hard-coding strings. See
shared/README.md for the ownership table. `shared.*` is readable by all agents;
each agent also owns a private namespace.
"""

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
