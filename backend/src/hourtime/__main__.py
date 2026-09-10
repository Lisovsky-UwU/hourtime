"""Development entry point: `uv run python -m hourtime`.

Not the `uvicorn` CLI, because on Windows uvicorn hardcodes a ProactorEventLoop
that psycopg cannot use. Here the loop factory is chosen explicitly.
"""

import argparse
import asyncio

from hourtime.infrastructure.asyncio_compat import event_loop_factory

APP_PATH = "hourtime.presentation.api.app:app"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Hourtime API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    import uvicorn

    if args.reload:
        # The reload supervisor runs the app in a subprocess, which uvicorn
        # already puts on a selector loop.
        uvicorn.run(APP_PATH, host=args.host, port=args.port, reload=True)
        return

    server = uvicorn.Server(uvicorn.Config(APP_PATH, host=args.host, port=args.port))
    asyncio.run(server.serve(), loop_factory=event_loop_factory())


if __name__ == "__main__":
    main()
