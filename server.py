"""Catalog MCP server.

A small, READ-ONLY, rate-limited Model Context Protocol (MCP) server that lets an AI
assistant browse an e-commerce product catalog: search products, look up price and
stock, and get shipping options. It exposes NO tools that change data, so an assistant
can read the catalog but never place an order or edit anything here.

Run it:
    mcp dev server.py              # inspector UI for manual testing
    python server.py               # run over stdio (for a real MCP client)
"""

import time
from collections import deque

from mcp.server.mcpserver import MCPServer

import catalog as cat

mcp = MCPServer("catalog")

# --- simple in-memory rate limit: at most N tool calls per rolling minute ---
_MAX_CALLS_PER_MINUTE = 60
_call_times = deque()


def _rate_limit():
    """Allow at most _MAX_CALLS_PER_MINUTE tool calls in any 60-second window."""
    now = time.monotonic()
    while _call_times and now - _call_times[0] > 60:
        _call_times.popleft()
    if len(_call_times) >= _MAX_CALLS_PER_MINUTE:
        raise RuntimeError(
            f"Rate limit exceeded: at most {_MAX_CALLS_PER_MINUTE} requests per minute."
        )
    _call_times.append(now)


@mcp.tool()
def search_products(
    query: str = "",
    category: str | None = None,
    max_price: float | None = None,
    in_stock_only: bool = False,
    limit: int = 10,
) -> list[dict]:
    """Search the product catalog.

    Use this to find products by keyword, category or price. Returns a compact list
    (id, title, brand, category, price, stock, rating). Call get_product for full details.
    """
    _rate_limit()
    return cat.search_products(
        query=query,
        category=category,
        max_price=max_price,
        in_stock_only=in_stock_only,
        limit=limit,
    )


@mcp.tool()
def get_product(product_id: str) -> dict:
    """Get the full details of one product by its id (price, stock, variants, returns)."""
    _rate_limit()
    try:
        return cat.get_product(product_id)
    except cat.ProductNotFound as e:
        raise ValueError(str(e))


@mcp.tool()
def get_shipping_options(product_id: str, destination: str = "US") -> dict:
    """Get the available shipping options and costs for a product."""
    _rate_limit()
    try:
        return cat.get_shipping_options(product_id, destination)
    except cat.ProductNotFound as e:
        raise ValueError(str(e))


@mcp.tool()
def list_categories() -> list[str]:
    """List the product categories available in the catalog."""
    _rate_limit()
    return cat.list_categories()


if __name__ == "__main__":
    mcp.run()
