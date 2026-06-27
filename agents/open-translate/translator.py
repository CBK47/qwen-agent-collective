from shared import namespaces

def translate_with_glossary(text):
    for term, translation in namespaces.items():
        text = text.replace(term, translation)
    return text
