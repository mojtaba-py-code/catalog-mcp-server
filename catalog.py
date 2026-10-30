"""Catalog logic for the MCP server.

Pure, side-effect-free functions over the product catalog. Keeping the logic here
(separate from the MCP transport in server.py) makes it easy to unit-test and reuse.
Everything is READ-ONLY: nothing in this module ever changes stock, price or orders.
"""

import json
from pathlib import Path

_CATALOG_PATH = Path(__file__).with_name("catalog.json")


class ProductNotFound(Exception):
    """Raised when a product id does not exist in the catalog."""


def load_catalog():
    """Load the product catalog from catalog.json."""
    with open(_CATALOG_PATH, encoding="utf-8") as f:
        return json.load(f)


_PRODUCTS = load_catalog()
_BY_ID = {p["id"]: p for p in _PRODUCTS}


def _summary(p):
    """A compact view of a product, for search results."""
    return {
        "id": p["id"],
        "title": p["title"],
        "brand": p["brand"],
        "category": p["category"],
        "price": p["price"],
        "currency": p["currency"],
        "in_stock": p["stock"] > 0,
        "stock": p["stock"],
        "rating": p["rating"],
    }


def search_products(query="", category=None, max_price=None, in_stock_only=False, limit=10):
    """Search the catalog.

    - query: matched against title, brand, category and description (case-insensitive).
    - category: exact category filter (case-insensitive).
    - max_price: only products at or below this price.
    - in_stock_only: hide out-of-stock products.
    Results are ordered: in-stock first, then by price ascending.
    """
    q = (query or "").lower().strip()
    results = []
    for p in _PRODUCTS:
        haystack = f"{p['title']} {p['brand']} {p['category']} {p.get('description', '')}".lower()
        if q and q not in haystack:
            continue
        if category and p["category"].lower() != category.lower():
            continue
        if max_price is not None and p["price"] > max_price:
            continue
        if in_stock_only and p["stock"] <= 0:
            continue
        results.append(_summary(p))
    results.sort(key=lambda r: (not r["in_stock"], r["price"]))
    limit = max(1, min(int(limit), 50))
    return results[:limit]


def get_product(product_id):
    """Return the full record for one product, or raise ProductNotFound."""
    p = _BY_ID.get(product_id)
    if p is None:
        raise ProductNotFound(f"No product with id '{product_id}'")
    return p


def get_shipping_options(product_id, destination="US"):
    """Return available shipping options for a product.

    Options are computed from the product's weight and price:
    - Standard: free when the item is $50 or more, otherwise $4.99.
    - Express: $9.99 for light items (<2kg), $19.99 otherwise.
    - Overnight: $24.99, only for items under 10kg.
    """
    p = get_product(product_id)
    weight = p["weight_kg"]
    currency = p["currency"]
    options = [
        {
            "name": "Standard",
            "price": 0.0 if p["price"] >= 50 else 4.99,
            "currency": currency,
            "eta_days": "5-7",
        },
        {
            "name": "Express",
            "price": 9.99 if weight < 2 else 19.99,
            "currency": currency,
            "eta_days": "2-3",
        },
    ]
    if weight < 10:
        options.append({"name": "Overnight", "price": 24.99, "currency": currency, "eta_days": "1"})
    return {
        "product_id": product_id,
        "destination": destination,
        "weight_kg": weight,
        "options": options,
    }


def list_categories():
    """Return the sorted list of distinct categories in the catalog."""
    return sorted({p["category"] for p in _PRODUCTS})
