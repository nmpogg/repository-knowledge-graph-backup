"""Core HTTP transport for API-RKG-CORE-v1.

Handoff for T-021 / T-024:
- ``create_app(storage, policy, session_token=...)`` serves ``/api/v1``.
- Mutations and ``POST /context`` require header ``X-RKG-Session`` plus a
  loopback ``Host``. A present ``Origin`` must also be loopback.
- The token is ``RKG_SESSION_TOKEN`` when set, otherwise one in-memory token
  created by ``rkg serve``. The CLI does not print it. The UI sends the same
  value as ``X-RKG-Session`` (``VITE_RKG_SESSION``).
- Loopback browser origins on another port are reflected for CORS. Other
  origins are not.
- Entity ``type`` values stay the domain enum (``Endpoint``, ``Callable``, …).
  The UI client maps them onto M0 labels.
- Graph reads take ``snapshot_id``. Omit it and pass ``repository_id`` to use
  the active snapshot (``409 no_active_snapshot`` when none exists).
- Index jobs return ``202`` and ``Retry-After: 1`` until the stage is terminal.
- Conversation create, list, history and grounded turn routes are mounted here.
  Delete returns ``409 conversation_busy`` while a turn is pending. Pass
  ``provider=`` to ``create_app`` for tests; otherwise OpenRouter is used and
  answers ``503 llm_disabled`` when no API key is configured.
"""

from rkg.api.app import create_app

__all__ = ["create_app"]
