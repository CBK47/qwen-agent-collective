from shared import namespaces

def translate_with_glossary(text):
    sorted_terms = sorted(namespaces.items(), key=lambda x: len(x[0]), reverse=True)
    for term, translation in sorted_terms:
        text = text.replace(term, translation)
    return text
