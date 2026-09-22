"""Stage 8, serve. Serves run/dashboard/ on http://localhost:8765.

Standard library only. `/` serves index.html. `/messages/<id>.txt` serves the raw
message as text/plain. Everything else is a static file under run/dashboard/.

Usage:
    uv run python -m pipeline.serve
    uv run python -m pipeline.serve --port 8765 --dir run/dashboard
"""

from __future__ import annotations

import argparse
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DEFAULT_PORT = 8765
DEFAULT_DIR = Path("run") / "dashboard"


class DashboardHandler(SimpleHTTPRequestHandler):
    """Static file handler with explicit content types and a quiet log."""

    extensions_map = {
        ".html": "text/html; charset=utf-8",
        ".htm": "text/html; charset=utf-8",
        ".js": "text/javascript; charset=utf-8",
        ".mjs": "text/javascript; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".txt": "text/plain; charset=utf-8",
        ".md": "text/markdown; charset=utf-8",
        ".svg": "image/svg+xml",
        ".png": "image/png",
        ".ico": "image/x-icon",
        "": "application/octet-stream",
    }

    def end_headers(self) -> None:
        # The dashboard is rebuilt in place. Never let the browser cache stale data.
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        sys.stdout.write("%s %s\n" % (self.address_string(), format % args))
        sys.stdout.flush()


def make_server(directory: Path, port: int) -> ThreadingHTTPServer:
    handler = partial(DashboardHandler, directory=str(directory))
    return ThreadingHTTPServer(("127.0.0.1", port), handler)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Serve the built dashboard")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--dir", default=str(DEFAULT_DIR), help="directory to serve")
    args = parser.parse_args(argv)

    directory = Path(args.dir)
    if not directory.is_dir() or not (directory / "index.html").is_file():
        print(
            f"serve: {directory} has no index.html. Run `uv run python -m pipeline.build` "
            "first, then serve.",
            file=sys.stderr,
        )
        return 1

    try:
        server = make_server(directory, args.port)
    except OSError as exc:
        print(f"serve: could not bind port {args.port}: {exc}", file=sys.stderr)
        return 1

    url = f"http://localhost:{args.port}/"
    print(f"serve: dashboard at {url} (serving {directory}, Ctrl-C to stop)")
    sys.stdout.flush()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
