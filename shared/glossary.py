import json

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
    
    def load_from_file(self, path: str) -> None:
        """Load glossary entries from a JSON file.

        This method reads a JSON file containing a dictionary of source-target pairs and updates the Glossary's entries with the loaded data, replacing any existing entries.

        Args:
            path (str): Path to the JSON file containing entries.

        Raises:
            FileNotFoundError: If the specified file does not exist.
            json.JSONDecodeError: If the file content is not valid JSON.
        """
        with open(path, 'r') as f:
            self.entries = json.load(f)
    
    def save_to_file(self, path: str) -> None:
        """Save glossary entries to a JSON file.

        Args:
            path (str): Path to the JSON file to save entries.
        """
        with open(path, 'w') as f:
            json.dump(self.entries, f)
