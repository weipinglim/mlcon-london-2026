#!/usr/bin/env python3

from __future__ import annotations

import argparse
import http.server
import socketserver
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve the GDPR browser locally.")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind.")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind.")
    parser.add_argument(
        "--root",
        default=str(Path(__file__).resolve().parent.parent / "site"),
        help="Directory to serve.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.root).resolve()
    handler = lambda *handler_args, **handler_kwargs: http.server.SimpleHTTPRequestHandler(  # noqa: E731
        *handler_args,
        directory=str(root),
        **handler_kwargs,
    )

    with socketserver.TCPServer((args.host, args.port), handler) as httpd:
        print(f"Serving {root} at http://{args.host}:{args.port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down.")


if __name__ == "__main__":
    main()
