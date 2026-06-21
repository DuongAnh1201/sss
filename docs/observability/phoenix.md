# Phoenix observability — local and cloud

MoneyPenny exports OpenTelemetry traces to [Arize Phoenix](https://arize.com/docs/phoenix) for consent-gate auditing. The in-process bypass evaluator runs regardless of whether Phoenix is reachable.

## Local (default)

Best for development — traces stay on your machine, no API key.

```bash
# Terminal 1 — collector + UI
uv run phoenix serve
# UI: http://localhost:6006

# Terminal 2 — app
uv run python server.py
# or: uv run python run_text.py "Email Priya the deck is ready"
```

`.env`:

```env
PHOENIX_ENABLED=1
PHOENIX_COLLECTOR_ENDPOINT=http://127.0.0.1:6006/v1/traces
PHOENIX_PROJECT_NAME=moneypenny
# PHOENIX_API_KEY=   ← leave empty for local
```

## Phoenix Cloud

Best for shared debugging, staging, and production — durable traces with team access.

### 1. Create a space

1. Sign up at [app.phoenix.arize.com](https://app.phoenix.arize.com).
2. **Create a Space** and note the **Hostname** from Settings (e.g. `https://app.phoenix.arize.com/s/my-space`).
3. Create an **API key** in the same Settings page.

### 2. Configure `.env`

```env
PHOENIX_ENABLED=1
PHOENIX_COLLECTOR_ENDPOINT=https://app.phoenix.arize.com/s/<your-space>
PHOENIX_API_KEY=<your-api-key>
PHOENIX_PROJECT_NAME=sss
```

The app appends `/v1/traces` automatically if omitted. `PHOENIX_API_KEY` is sent as a Bearer token on every OTLP export.

### 3. Verify traces

Run any orchestrator session, then open your Phoenix Cloud space → **Traces**. Filter by project `sss`.

## Environment reference

| Variable | Local | Cloud |
|---|---|---|
| `PHOENIX_ENABLED` | `1` | `1` |
| `PHOENIX_COLLECTOR_ENDPOINT` | `http://127.0.0.1:6006/v1/traces` | Space hostname from dashboard |
| `PHOENIX_API_KEY` | *(empty)* | Required |
| `PHOENIX_PROJECT_NAME` | `sss` | `sss` |
| `CONSENT_EVAL_ENABLED` | `1` | `1` |
| `KILL_SWITCH_ON_BYPASS` | `1` | `1` |

## Privacy note

Cloud traces may contain prompts, tool payloads, and consent decisions. Use local Phoenix when working with real user data during development, or redact sensitive span attributes before enabling cloud export in production.

## Tests

```bash
# Unit tests (no Phoenix server required)
uv run pytest tests/observability tests/ws_server -q

# Optional — export a probe span to your Phoenix Cloud space
PHOENIX_COLLECTOR_ENDPOINT=https://app.phoenix.arize.com/s/<your-space> \
PHOENIX_API_KEY=<key> \
uv run pytest tests/observability/test_phoenix_setup.py -m phoenix_integration -q
```

## Not Arize AX

This project uses **Phoenix** (`PHOENIX_API_KEY` + `PHOENIX_COLLECTOR_ENDPOINT`), not the separate **Arize AX** product (`ARIZE_SPACE_ID` + `ARIZE_API_KEY`). See [Arize docs](https://arize.com/docs/phoenix) if you need AX instead.
