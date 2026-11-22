"""Bilingual guides available on the public site."""
from guide_copy import GUIDES as KITCHEN_GUIDES
from inventory_field_guide import INVENTORY_GUIDE
from recipe_field_guide import RECIPE_GUIDE
from shop_field_guide import SHOP_GUIDE

GUIDES = {**KITCHEN_GUIDES, "shop": SHOP_GUIDE, "inventory": INVENTORY_GUIDE, "recipes": RECIPE_GUIDE}

# Each pair answers a natural next question for this reader.
RELATED = {
    "budget": ("shop", "pantry"),
    "pantry": ("recipes", "inventory"),
    "receipt": ("inventory", "pantry"),
    "shop": ("budget", "receipt"),
    "inventory": ("pantry", "receipt"),
    "recipes": ("pantry", "shop"),
}
