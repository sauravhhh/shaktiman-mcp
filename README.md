# Shaktiman MCP Server

A remote MCP server that lets AI clients (like Poke) text Shaktiman, an AI assistant — via email and Telegram.

## Tools

- `text_shaktiman` — send the assistant a text message (delivered via email inbox)
- `send_telegram_message` — send a message on Telegram via bot
- `get_telegram_updates` — check for new incoming Telegram messages

## Quick deploy (Render)

1. Fork/clone this repo
2. Create a new **Web Service** on [Render](https://render.com) from this repo
3. Set environment variables (see below)
4. Render gives you a public URL like `https://shaktiman-mcp.onrender.com`
5. Add `https://shaktiman-mcp.onrender.com/sse` as a custom MCP server in Poke (Integrations → New)

## Configuration

| Variable | Required | Description |
|---|---|---|
| `SENDMUX_API_KEY` | Yes | Sendmux mailbox API key (email sending) |
| `TEXTS_INBOX` | Yes | Email inbox texts are sent to |
| `TELEGRAM_BOT_TOKEN` | No | Telegram bot token (enables Telegram tools) |
| `TELEGRAM_CHAT_ID` | No | Chat ID for outgoing Telegram messages |
| `PORT` | No | Port to listen on (default `8765`) |

## Local run

```bash
pip install -r requirements.txt
SENDMUX_API_KEY=... TEXTS_INBOX=... python server.py
```

The SSE endpoint is at `/sse`.
