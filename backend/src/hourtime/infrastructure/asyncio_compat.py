"""Windows event-loop shim.

psycopg's async driver refuses to run on the ProactorEventLoop that Python — and
uvicorn — pick by default on Windows, so anything that opens a connection has to
ask for a selector loop first. Both helpers are no-ops on other platforms.
"""

import asyncio
import sys
from collections.abc import Callable


def event_loop_factory() -> Callable[[], asyncio.AbstractEventLoop] | None:
    """Loop factory to hand to `asyncio.run`, or None to accept the default.

    Preferred over the policy below: `asyncio.run(..., loop_factory=...)` is
    explicit and, unlike the policy, uvicorn cannot ignore it.
    """
    if sys.platform != "win32":
        return None
    return asyncio.SelectorEventLoop


def use_selector_event_loop() -> None:
    """Install the selector policy process-wide.

    Only for runners that create the loop themselves and give no way to pass a
    factory — pytest-asyncio, most notably.
    """
    if sys.platform != "win32":
        return
    policy = getattr(asyncio, "WindowsSelectorEventLoopPolicy", None)
    if policy is not None:
        # Deprecated since 3.12, but still the only lever for third-party runners.
        asyncio.set_event_loop_policy(policy())  # ty: ignore[deprecated]
