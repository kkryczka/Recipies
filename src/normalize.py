from difflib import get_close_matches

# Small synonyms map: variant -> canonical
SYNONYMS = {
    "aubergine": "eggplant",
    "eggplants": "eggplant",
    "courgette": "zucchini",
    "capsicum": "bell pepper",
    "scallion": "green onion",
    "scallions": "green onion",
    "cilantro": "coriander",
    "tomatoes": "tomato",
    "eggs": "egg",
}


def _singularize(word: str) -> str:
    w = word
    if w.endswith("ies") and len(w) > 3:
        return w[:-3] + "y"
    if w.endswith("es") and len(w) > 3:
        return w[:-2]
    if w.endswith("s") and len(w) > 3:
        return w[:-1]
    return w


def normalize_ingredient(s: str) -> str:
    if not s:
        return ""
    w = s.strip().lower()
    w = _singularize(w)
    # map synonyms
    if w in SYNONYMS:
        return SYNONYMS[w]
    return w


def is_ingredient_match(recipe_ing: str, have_set: set, cutoff: float = 0.8) -> bool:
    # normalize recipe ingredient
    r = normalize_ingredient(recipe_ing)
    if not r:
        return False
    if r in have_set:
        return True
    # fuzzy match against have_set
    if not have_set:
        return False
    matches = get_close_matches(r, list(have_set), n=1, cutoff=cutoff)
    return len(matches) > 0
