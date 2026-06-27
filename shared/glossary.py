class Glossary:
    def __init__(self):
        self.entries = {}

    def add_entry(self, source, target):
        self.entries[source] = target

    def get_translation(self, source):
        return self.entries.get(source)
