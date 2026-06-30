import os
import dashscope
from dashscope import Translation
import brain

dashscope.api_key = os.getenv('DASHSCOPE_API_KEY')

def translate(text: str, source_lang: str, target_lang: str) -> str:
    """
    Translates the given text from source language to target language using a predefined glossary for specific terms.

    This function first replaces any terms found in the glossary from brain's storage with their corresponding translations (sorted by term length descending to avoid partial matches). Then, it uses the Dashscope translation API to translate the processed text.

    Args:
        text (str): The input text to translate.
        source_lang (str): The source language code (e.g., 'en', 'ja').
        target_lang (str): The target language code (e.g., 'zh', 'fr').

    Returns:
        str: The translated text in the target language.
    """
    glossary = brain.get_glossary()
    new_terms = []
    words = text.split()
    for word in words:
        if word not in glossary:
            new_terms.append(word)
    
    if new_terms:
        brain.add_to_review_queue(new_terms)
    
    sorted_terms = sorted(glossary.items(), key=lambda x: len(x[0]), reverse=True)
    unapproved_terms = []
    for term, entry in sorted_terms:
        if isinstance(entry, dict) and entry.get('approved', False):
            text = text.replace(term, entry['translation'])
        else:
            unapproved_terms.append(term)
    
    if unapproved_terms:
        return f"Approval needed for terms: {', '.join(unapproved_terms)}"
    
    response = Translation.call(
        model='qwen-turbo',
        source_text=text,
        source_lang=source_lang,
        target_lang=target_lang
    )
    return response.output.translations[0].translation
