"""Serve the FireTwin Explorer with an allowlisted local file server."""

import argparse
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

REPO_ROOT = Path(__file__).resolve().parents[1]
ALLOWED_FILES = {
    "/data/manifests/firms_next_day_explorer_manifest.json": REPO_ROOT
    / "data/manifests/firms_next_day_explorer_manifest.json",
}
ALLOWED_PREFIXES = {
    "/frontend/": REPO_ROOT / "frontend",
    "/reports/figures/": REPO_ROOT / "reports/figures",
}
ALLOWED_FIGURE_SUFFIXES = (
    "_explorer_forecast_preview.png",
    "_globe_forecast_overlay.png",
    "_globe_observed_overlay.png",
)


def resolve_explorer_request(raw_path: str) -> Path | None:
    """Resolve a request path to an allowlisted local file."""
    parsed_path = unquote(urlparse(raw_path).path)
    if parsed_path == "/":
        parsed_path = "/frontend/"
    if parsed_path == "/frontend/":
        parsed_path = "/frontend/index.html"

    if parsed_path in ALLOWED_FILES:
        return ALLOWED_FILES[parsed_path]

    for prefix, root in ALLOWED_PREFIXES.items():
        if not parsed_path.startswith(prefix):
            continue
        relative = Path(parsed_path.removeprefix(prefix))
        if any(part in {"", ".", ".."} for part in relative.parts):
            return None
        if prefix == "/reports/figures/" and not relative.name.endswith(ALLOWED_FIGURE_SUFFIXES):
            return None
        candidate = (root / relative).resolve()
        try:
            candidate.relative_to(root.resolve())
        except ValueError:
            return None
        return candidate
    return None


class ExplorerRequestHandler(BaseHTTPRequestHandler):
    """HTTP handler that serves only the Explorer and its public assets."""

    def do_GET(self) -> None:
        """Serve an allowlisted file."""
        path = resolve_explorer_request(self.path)
        if path is None or not path.is_file():
            self.send_error(404)
            return

        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_HEAD(self) -> None:
        """Serve headers for an allowlisted file."""
        path = resolve_explorer_request(self.path)
        if path is None or not path.is_file():
            self.send_error(404)
            return

        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(path.stat().st_size))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        """Keep local preview logs compact."""
        print(f"{self.address_string()} - {format % args}")


def main() -> None:
    """Run the allowlisted Explorer server."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), ExplorerRequestHandler)
    print(f"FireTwin Explorer: http://{args.host}:{args.port}/frontend/")
    print("Serving only frontend/, the Explorer manifest and preview figures.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping FireTwin Explorer server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
