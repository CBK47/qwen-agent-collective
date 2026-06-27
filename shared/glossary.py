class Glossary:
    """Manages a collection of source-target translation pairs."""
    
    def __init__(self) -> None:
        self.entries: dict[str, str] = {}
    
    def add_entry(self, source: str, target: str) -> None:
        """Add a source-target translation pair to the glossary."""
        self.entries[source] = target
    
    def get_translation(self, source: str) -> str | None:
        """Retrieve the translation for a given source term. Returns the target term if found, else None."""
        return self.entries.get(source)
