from typing import List

# Very small built-in translation dictionaries for demo purposes.
# Keys are language codes (ISO 639-1) -> mapping of English phrase -> translated phrase.
TRANSLATIONS = {
    "pl": {
        "Ingredients": "Składniki",
        "Steps": "Kroki",
        "Back": "Wstecz",
        "Edit": "Edytuj",
        "Delete": "Usuń",
        # common ingredients example
        "tomato": "pomidor",
        "salt": "sól",
        "egg": "jajko",
        "flour": "mąka",
        "milk": "mleko",
        "sugar": "cukier",
    },
    "es": {
        "Ingredients": "Ingredientes",
        "Steps": "Pasos",
        "Back": "Atrás",
        "Edit": "Editar",
        "Delete": "Eliminar",
        "tomato": "tomate",
        "salt": "sal",
        "egg": "huevo",
    }
}


def translate_text(text: str, lang: str) -> str:
    if not lang:
        return text
    lang = lang.lower()
    mapping = TRANSLATIONS.get(lang)
    if not mapping:
        return text
    # simple token-based translation: try lowercase lookup, otherwise title-case for headings
    key = text.strip()
    lower = key.lower()
    if lower in mapping:
        return mapping[lower]
    if key in mapping:
        return mapping[key]
    # try capitalized
    cap = key.capitalize()
    if cap in mapping:
        return mapping[cap]
    return text


def translate_list(items: List[str], lang: str) -> List[str]:
    if not lang:
        return items
    return [translate_text(i, lang) for i in items]
