from pathlib import Path
from recipes import load_recipes


def main():
    data_file = Path(__file__).resolve().parent.parent / "data" / "recipes.json"
    recipes = load_recipes(str(data_file))
    print(f"Loaded {len(recipes)} recipe(s).")
    for r in recipes:
        print(f"- {r.get('name')}")


if __name__ == "__main__":
    main()
