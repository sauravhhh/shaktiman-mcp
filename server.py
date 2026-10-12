#!/usr/bin/env python3
"""Shaktiman MCP server — text your AI assistant from anywhere.

Exposes tools over SSE (and streamable HTTP) so remote MCP clients
like Poke can reach them:
  - text_shaktiman: send Shaktiman a text message (via email inbox).
  - send_telegram_message: send a Telegram message via the bot.
  - get_telegram_updates: check for new incoming Telegram messages.

Configuration (environment variables):
  SENDMUX_API_KEY    API key for Sendmux (email sending)
  TEXTS_INBOX        Inbox address texts are sent to (default: owner sets it)
  TELEGRAM_BOT_TOKEN Telegram bot token (optional, enables Telegram tools)
  TELEGRAM_CHAT_ID   Chat ID to send Telegram messages to (optional)
  PORT               Port to listen on (default: 8765)
  HOST               Host to bind (default: 0.0.0.0)

Run:
  pip install -r requirements.txt
  python server.py
"""

import html
import json
import os
import urllib.parse
import urllib.request

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("shaktiman")

SENDMUX_API_KEY = os.environ.get("SENDMUX_API_KEY", "")
TEXTS_INBOX = os.environ.get("TEXTS_INBOX", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
TG_API = "https://api.telegram.org"


def _sendmux_send(to_email: str, subject: str, message: str) -> str:
    """Send via Sendmux HTTP API directly."""
    if not SENDMUX_API_KEY or not TEXTS_INBOX:
        return "Email not configured (SENDMUX_API_KEY / TEXTS_INBOX)."
    body = {
        "from": {"email": TEXTS_INBOX, "name": "via MCP"},
        "to": {"email": to_email},
        "subject": subject,
        "html_body": f"<p>{html.escape(message)}</p>",
        "text_body": message,
    }
    req = urllib.request.Request(
        "https://api.sendmux.com/v1/sending/send",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {SENDMUX_API_KEY}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            json.load(r)
    except Exception as e:
        return f"Failed to send: {e}"
    return "Sent."


def _tg_api(method: str, **params):
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(
        f"{TG_API}/bot{TELEGRAM_BOT_TOKEN}/{method}", data=data
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


@mcp.tool()
def text_shaktiman(message: str) -> str:
    """Send a text message to Shaktiman, the AI assistant.

    He picks it up and replies. Keep messages short — this is texting.
    """
    message = message.strip()
    if not message:
        return "Message is empty — nothing sent."
    result = _sendmux_send(TEXTS_INBOX, "Text for Shaktiman", message)
    if result == "Sent.":
        return "Sent to Shaktiman."
    return result


@mcp.tool()
def send_telegram_message(message: str) -> str:
    """Send a message on Telegram via the bot. Keep messages short."""
    message = message.strip()
    if not message:
        return "Message is empty — nothing sent."
    if not TELEGRAM_BOT_TOKEN:
        return "Telegram bot not configured."
    if not TELEGRAM_CHAT_ID:
        return "No chat ID configured."
    try:
        res = _tg_api("sendMessage", chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as e:
        return f"Failed to send: {e}"
    if not res.get("ok"):
        return f"Telegram error: {res.get('description', res)}"
    return "Sent on Telegram."


@mcp.tool()
def get_telegram_updates() -> str:
    """Check for new incoming Telegram messages."""
    if not TELEGRAM_BOT_TOKEN:
        return "Telegram bot not configured."
    try:
        res = _tg_api("getUpdates", timeout=0)
    except Exception as e:
        return f"Failed to check: {e}"
    if not res.get("ok"):
        return f"Telegram error: {res.get('description', res)}"
    updates = res.get("result", [])
    texts = [
        u.get("message", {}).get("text", "")
        for u in updates
        if u.get("message", {}).get("text")
    ]
    if not texts:
        return "No new messages."
    return "\n".join(f"- {t}" for t in texts)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8765"))
    host = os.environ.get("HOST", "0.0.0.0")
    mcp.run(transport="sse", port=port, host=host)
