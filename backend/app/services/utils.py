"""Utility functions for signal validation used in P0‑B.

Provides a single source of truth for assessing whether a ``TraceableSignal``
can be safely used by the policy engine.
"""

from datetime import datetime, timezone, timedelta
from ..domain.farm_decision_context import TraceableSignal, SignalQuality

# Freshness threshold – configurable via environment variable if needed
_FRESHNESS_THRESHOLD = timedelta(hours=2)

def is_signal_trustworthy(signal: TraceableSignal) -> bool:
    """Return ``True`` if the signal is considered reliable.

    Criteria:
    * Signal and its value must not be None.
    * ``quality`` must not be MISSING or STALE.
    * If a ``timestamp`` is present, it must be no older than the freshness threshold.
    """
    if signal is None or signal.value is None:
        return False
    if signal.quality in (SignalQuality.MISSING, SignalQuality.STALE):
        return False
    if getattr(signal, "timestamp", None):
        try:
            ts_str = str(signal.timestamp).replace("Z", "+00:00")
            ts = datetime.fromisoformat(ts_str)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            if now - ts > _FRESHNESS_THRESHOLD:
                return False
            if ts - now > timedelta(minutes=5):
                return False
        except Exception:
            # If parsing fails, be conservative
            return False
    return True

