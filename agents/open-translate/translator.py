from shared import namespaces

import os
import dashscope
from dashscope import Translation

dashscope.api_key = os.getenv('DASHSCOPE_API_KEY')

def translate_with_glossary(text):
    sorted_terms = sorted(namespaces.items(), key=lambda x: len(x[0]), reverse=True)
    for term, translation in sorted_terms:
        text = text.replace(term, translation)
    response = Translation.call(
        model='qwen-turbo',
        source_text=text,
        target_lang='zh'
    )
    return response.output.translations[0].translation
