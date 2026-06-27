class Glossary:
    """Manages a collection of source-target translation pairs."""
    
    def __init__(self) -> None:
        """Initialize a new Glossary instance with empty entries."""
        self.entries: dict[str, str] = {}
    
    def add_entry(self, source: str, target: str) -> None:
        """Add a source term and its translation to the glossary.

        Args:
            source (str): The source term to add.
            target (str): The corresponding translation for the source term.
        """
        self.entries[source] = target
    
    def get_translation(self, source: str) -> str | None:
        """Retrieve the translation for a given source term.

        Args:
            source (str): The source term to look up.

        Returns:
            str | None: The target translation if found, otherwise None.
        """
        return self.entries.get(source)
