"""The ten skills: codes, order, names in Portflow and categories (docs/vaardigheden-openict.md)."""

SKILLS = ["OC", "KO", "JKO", "KPM", "PL", "BD", "SW", "FO", "PH", "RE"]
PRODUCT_SKILLS = ["OC", "KO", "JKO", "KPM"]
COACH_SKILLS = ["PL", "BD", "SW", "FO", "PH", "RE"]

NAMES = {
    "OC": "Overzicht creëren",
    "KO": "Kritisch oordelen",
    "JKO": "Juiste kennis ontwikkelen",
    "KPM": "Kwalitatief product maken",
    "PL": "Plannen",
    "BD": "Boodschap delen",
    "SW": "Samenwerken",
    "FO": "Flexibel opstellen",
    "PH": "Pro-actief handelen",
    "RE": "Reflecteren",
}

# Category per skill, for the column header colours (docs/design-system.md, categories from LEF).
CATEGORY = {code: "product" for code in PRODUCT_SKILLS}
CATEGORY.update({code: "social" for code in ["PL", "BD", "SW"]})
CATEGORY.update({code: "personal" for code in ["FO", "PH", "RE"]})

_BY_NAME = {name.casefold(): code for code, name in NAMES.items()}


def skill_for_goal_name(name: str | None) -> str | None:
    """Portflow goal name -> skill code; names differ in capitals ("Kwalitatief Product Maken")."""
    return _BY_NAME.get(" ".join((name or "").split()).casefold())
