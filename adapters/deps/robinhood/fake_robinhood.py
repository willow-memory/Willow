"""A stand-in for Robinhood's MCP server, on this machine, for the tests.

It offers all twelve of the real server's tool names, the ones that place
and cancel orders and change watchlists among them, answers the read tools
with made-up accounts, and records every call, so a test can say exactly
what the add-on asked for. It never signs anyone in.
"""

from __future__ import annotations

import socket
import threading
import time

import uvicorn
from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

READ = ToolAnnotations(read_only_hint=True)
WRITE = ToolAnnotations(read_only_hint=False, destructive_hint=True)


def make(calls: list, marked_changing: tuple[str, ...] = ()) -> MCPServer:
    s = MCPServer("fake-robinhood")

    def note(name: str, **kw) -> None:
        calls.append((name, kw))

    def mark(name: str) -> ToolAnnotations:
        return WRITE if name in marked_changing else READ

    @s.tool(name="get_accounts", annotations=mark("get_accounts"))
    def get_accounts() -> dict:
        note("get_accounts")
        return {"accounts": [
            {"account_number": "5QR12345678", "type": "individual", "agentic": False},
            {"account_number": "5QR98765432", "type": "individual", "agentic": True},
        ]}  # fmt: skip

    @s.tool(name="get_portfolio", annotations=mark("get_portfolio"))
    def get_portfolio() -> dict:
        note("get_portfolio")
        return {"total_value": "1234.56", "cash": "100.00", "buying_power": "100.00"}

    @s.tool(name="get_equity_positions", annotations=mark("get_equity_positions"))
    def get_equity_positions(account_number: str) -> dict:
        note("get_equity_positions", account_number=account_number)
        held = {
            "5QR12345678": [
                {"symbol": "VTI", "quantity": "3", "average_cost": "212.40"}
            ]
        }
        return {
            "account_number": account_number,
            "positions": held.get(account_number, []),
        }

    @s.tool(name="get_equity_orders", annotations=mark("get_equity_orders"))
    def get_equity_orders() -> dict:
        note("get_equity_orders")
        return {"orders": [{"symbol": "VTI", "side": "buy", "quantity": "1", "state": "filled",
                            "created_at": "2021-03-02T15:01:00Z"}]}  # fmt: skip

    @s.tool(name="get_watchlists", annotations=mark("get_watchlists"))
    def get_watchlists() -> dict:
        note("get_watchlists")
        return {"watchlists": [{"name": "Grocers", "symbols": ["KR", "COST"]}]}

    @s.tool(name="get_equity_quotes", annotations=mark("get_equity_quotes"))
    def get_equity_quotes(symbols: list[str]) -> dict:
        note("get_equity_quotes", symbols=symbols)
        return {
            "quotes": [{"symbol": x, "last_trade_price": "100.00"} for x in symbols]
        }

    @s.tool(name="search", annotations=READ)
    def search(query: str) -> dict:
        note("search", query=query)
        return {"results": []}

    @s.tool(name="review_equity_order", annotations=READ)
    def review_equity_order(symbol: str, quantity: str, side: str) -> dict:
        note("review_equity_order", symbol=symbol)
        return {"warnings": []}

    def acting(name: str):
        def act(order: str = "") -> dict:
            note(name, order=order)
            return {"done": True}

        return act

    for name in (
        "place_equity_order",
        "cancel_equity_order",
        "add_to_watchlist",
        "update_watchlist",
    ):
        s.tool(name=name, annotations=WRITE)(acting(name))
    return s


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def serve(
    calls: list, marked_changing: tuple[str, ...] = ()
) -> tuple[str, uvicorn.Server]:
    """Start one on 127.0.0.1; its URL and the server, to stop with .should_exit."""
    port = free_port()
    app = make(calls, marked_changing).streamable_http_app(host="127.0.0.1")
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    )
    threading.Thread(target=server.run, daemon=True).start()
    for _ in range(200):
        if server.started:
            break
        time.sleep(0.02)
    return f"http://127.0.0.1:{port}/mcp", server
