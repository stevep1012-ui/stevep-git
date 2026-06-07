from __future__ import annotations

import threading
import time
import webbrowser
from pathlib import Path

from .dashboard_server import DashboardHandler, ThreadingHTTPServer


def main() -> None:
    host = "127.0.0.1"
    port = 8787
    DashboardHandler.multi_user_root = Path("data/users")
    url = f"http://{host}:{port}/"

    def open_browser() -> None:
        time.sleep(1)
        webbrowser.open(url)

    threading.Thread(target=open_browser, daemon=True).start()
    server = ThreadingHTTPServer((host, port), DashboardHandler)
    print(f"YouTube Bird Studio: {url}")
    server.serve_forever()


if __name__ == "__main__":
    main()
