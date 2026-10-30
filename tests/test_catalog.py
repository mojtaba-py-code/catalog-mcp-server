"""Unit tests for the catalog logic (independent of the MCP transport)."""

import pytest

import catalog as cat


def test_search_returns_results():
    assert len(cat.search_products()) > 0


def test_search_by_keyword():
    results = cat.search_products(query="headphones")
    assert results, "expected at least one match for 'headphones'"
    assert all("headphone" in r["title"].lower() for r in results)


def test_search_max_price():
    results = cat.search_products(max_price=50)
    assert results
    assert all(r["price"] <= 50 for r in results)


def test_search_in_stock_only_hides_out_of_stock():
    results = cat.search_products(in_stock_only=True)
    assert all(r["in_stock"] for r in results)
    # p002 (Pulse speaker) is out of stock, so it must not appear
    assert all(r["id"] != "p002" for r in results)


def test_search_category_filter():
    results = cat.search_products(category="Monitors")
    assert results
    assert all(r["category"] == "Monitors" for r in results)


def test_search_limit():
    assert len(cat.search_products(limit=3)) <= 3


def test_get_product_ok():
    p = cat.get_product("p004")
    assert p["id"] == "p004"
    assert len(p["variants"]) == 3


def test_get_product_missing_raises():
    with pytest.raises(cat.ProductNotFound):
        cat.get_product("does-not-exist")


def test_shipping_free_standard_over_50():
    options = cat.get_shipping_options("p001")["options"]  # $129 item
    standard = next(o for o in options if o["name"] == "Standard")
    assert standard["price"] == 0.0


def test_shipping_paid_standard_under_50():
    options = cat.get_shipping_options("p005")["options"]  # $39 mouse
    standard = next(o for o in options if o["name"] == "Standard")
    assert standard["price"] == 4.99


def test_shipping_heavy_item_has_no_overnight():
    options = cat.get_shipping_options("p008")["options"]  # 32kg desk
    assert all(o["name"] != "Overnight" for o in options)


def test_list_categories():
    cats = cat.list_categories()
    assert "Audio" in cats
    assert cats == sorted(cats)
