import os
import dashscope
from dashscope import Translation
import brain

dashscope.api_key = os.getenv('DASHSCOPE_API_KEY')

def translate_with_glossary(text: str) -> str:
    """
    Translates the given text to Chinese using a predefined glossary for specific terms.

    This function first replaces any terms found in the glossary from brain's storage with their corresponding translations (sorted by term length descending to avoid partial matches). Then, it uses the Dashscope translation API to translate the processed text to Chinese.

    Args:
        text (str): The input text to translate.

    Returns:
        str: The translated text in Chinese.
    """
    glossary = brain.get_glossary()
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
        target_lang='zh'
    )
    return response.output.translations[0].translation
