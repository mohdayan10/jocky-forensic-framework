"""Best-effort WebSocket broadcast from the terminal demo to connected browsers.

Uses Django Channels InMemoryChannelLayer. Works only when the demo runs
inside the same Python process as the daphne server (via management command).
Always silently succeeds so demo never breaks when channels isn't running.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def broadcast(case_id: str, event_type: str, data: dict) -> None:
    """Send a message to all WebSocket clients watching this case."""
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        channel_layer = get_channel_layer()
        if channel_layer is None:
            return

        group_name = f"case_{case_id}"
        handler_type = event_type.lower().replace("-", "_")
        payload = {"type": handler_type, "event_type": event_type}
        payload.update(data)

        async_to_sync(channel_layer.group_send)(group_name, payload)
        logger.debug("Broadcast %s → %s", event_type, group_name)
    except Exception as exc:
        logger.debug("Broadcast skipped (no live server in process): %s", exc)
