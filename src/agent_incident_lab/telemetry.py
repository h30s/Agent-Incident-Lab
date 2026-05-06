from __future__ import annotations

import traceroot
from traceroot import Integration

_initialized = False


def init_traceroot() -> None:
    global _initialized
    if _initialized:
        return
    traceroot.initialize(integrations=[Integration.CREWAI])
    _initialized = True


def flush() -> None:
    traceroot.flush()
