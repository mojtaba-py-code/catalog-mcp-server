# Catalog MCP Server

A small, **read-only, rate-limited** [Model Context Protocol (MCP)](https://modelcontextprotocol.io)
server that lets an AI assistant browse an e-commerce product catalog: search products,
look up price and stock, and get shipping options.

It is the kind of catalog server an AI shopping assistant (ChatGPT, Claude, Perplexity)
would call to answer questions like *"wireless headphones under $100 that are in stock"* —
built so the assistant can **read** the catalog but never change data or place an order.

## Tools

| Tool | What it does |
|---|---|
| `search_products(query, category, max_price, in_stock_only, limit)` | Find products by keyword / category / price; returns a compact list. |
| `get_product(product_id)` | Full details of one product: price, stock, variants, returns. |
| `get_shipping_options(product_id, destination)` | Shipping options and costs, computed from weight and price. |
| `list_categories()` | The distinct product categories. |

All tools are read-only. There is **no** tool that writes stock, price or orders.

## Design notes

- **Read-only by design** — safe for an untrusted assistant to call.
- **Rate-limited** — at most 60 tool calls per rolling minute (`server.py`), so a
  misbehaving agent cannot hammer the catalog.
- **Logic separated from transport** — all catalog logic lives in `catalog.py` (pure,
  testable functions); `server.py` only wraps it as MCP tools and applies the rate limit.
- **Tested** — the catalog logic is covered by `pytest` (`tests/test_catalog.py`).
- **Sample data** — `catalog.json` holds 15 example products with titles, attributes,
  variants, price, stock, weight and returns. Swap it for a real product feed (e.g. pulled
  from Shopify/WooCommerce) without touching the tool code.

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (use: source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
```

Run the tests:

```bash
pytest
```

Try it interactively in the MCP Inspector:

```bash
mcp dev server.py
```

## Connect it to an MCP client (e.g. Claude Desktop)

Add this to the client's MCP config (adjust the path to this folder):

```json
{
  "mcpServers": {
    "catalog": {
      "command": "python",
      "args": ["server.py"],
      "cwd": "C:/path/to/catalog-mcp-server"
    }
  }
}
```

The assistant can then call `search_products`, `get_product`, `get_shipping_options`
and `list_categories` while answering shopping questions.

## Project layout

```
catalog-mcp-server/
├── catalog.json        # sample product catalog (the data)
├── catalog.py          # read-only catalog logic (search / lookup / shipping)
├── server.py           # the MCP server: wraps the logic as tools + rate limit
├── tests/
│   └── test_catalog.py # unit tests for the logic
├── requirements.txt
├── pyproject.toml
└── README.md
```
