"""
serve.py — start a tiny local web server for browsing the notes.

Run from this folder:
    python serve.py

Then open http://localhost:8000/ in your browser.
Ctrl+C to stop.
"""

from __future__ import annotations

import http.server
import socketserver
import webbrowser
from pathlib import Path

PORT = 8000
HERE = Path(__file__).resolve().parent


def main() -> None:
    handler = http.server.SimpleHTTPRequestHandler
    # serve files relative to this folder
    import os
    os.chdir(HERE)
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        url = f"http://localhost:{PORT}/"
        print(f"Serving {HERE}")
        print(f"Open {url}  (Ctrl+C to stop)")
        try:
            webbrowser.open(url)
        except Exception:
            pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    main()
