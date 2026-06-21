"""Trust & observability — Arize Phoenix tracing + consent self-check evals.

Replaces Logfire. Exports OpenTelemetry traces to Phoenix and runs a continuous
evaluator that verifies every ``Tool_Executed`` span was preceded by a valid
``Ledger_Appended`` span (see docs/consent-architecture/03-observability-and-ledger.md).
"""

from observability.phoenix import setup_observability

__all__ = ["setup_observability"]
