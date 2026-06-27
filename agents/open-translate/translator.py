from shared import namespaces

import os
import dashscope
from dashscope import Translation

dashscope.api_key = os.getenv('DASHSCOPE_API_KEY')

def translate_with_glossary(text: str) -> str:
    """
    Translates the given text to Chinese using a predefined glossary for specific terms.

    This function first replaces any terms found in the namespaces dictionary with their corresponding translations (sorted by term length descending to avoid partial matches). Then, it uses the Dashscope translation API to translate the processed text to Chinese.

    Args:
        text (str): The input text to translate.

    Returns:
        str: The translated text in Chinese.
    """
    sorted_terms = sorted(namespaces.items(), key=lambda x: len(x[0]), reverse=True)
    for term, translation in sorted_terms:
        text = text.replace(term, translation)
    response = Translation.call(
        model='qwen-turbo',
        source_text=text,
        target_lang='zh'
    )
    return response.output.translations[0].translation
