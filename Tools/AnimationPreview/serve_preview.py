from __future__ import annotations

import functools
import http.server
import threading
import webbrowser
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
HOST = "127.0.0.1"


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        if self.path == "/AnimationPreview.html" or self.path.endswith(".png"):
            super().log_message(format, *args)


def main() -> None:
    handler = functools.partial(QuietHandler, directory=str(PROJECT_ROOT))
    server = http.server.ThreadingHTTPServer((HOST, 0), handler)
    port = server.server_address[1]
    url = f"http://{HOST}:{port}/AnimationPreview.html"

    print("Animal animation preview server is running.")
    print(f"URL: {url}")
    print("Close this window or press Ctrl+C to stop the server.")
    print()

    threading.Timer(0.4, webbrowser.open_new_tab, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
