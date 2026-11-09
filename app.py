"""Start the Portflow coach dashboard.

    python app.py              # http://127.0.0.1:5050
    python app.py --port 8000  # choose another port
    python app.py --no-browser # do not open the browser

Port 5000 is avoided on purpose: on macOS it is taken by the AirPlay receiver.
"""

import argparse
import socket
import sys
import threading
import webbrowser

from dashboard import create_app

HOST = "127.0.0.1"
DEFAULT_PORT = 5050

BANNER = r"""
  ____            _    __ _
 |  _ \ ___  _ __| |_ / _| | _____      __
 | |_) / _ \| '__| __| |_| |/ _ \ \ /\ / /
 |  __/ (_) | |  | |_|  _| | (_) \ V  V /
 |_|   \___/|_|   \__|_| |_|\___/ \_/\_/
      coach dashboard
"""


def port_is_free(port: int, host: str = HOST) -> bool:
    """Return True if nothing is listening on host:port yet."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, port))
        except OSError:
            return False
    # A wildcard listener (such as macOS AirPlay on *:5000) does not always
    # block a bind on 127.0.0.1, so also check whether something answers.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.3)
        return sock.connect_ex((host, port)) != 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Portflow coach dashboard")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"poort (standaard {DEFAULT_PORT})")
    parser.add_argument("--no-browser", action="store_true", help="browser niet automatisch openen")
    args = parser.parse_args()

    if not port_is_free(args.port):
        print(f"Poort {args.port} is al in gebruik. Draait het dashboard al?")
        print(f"Kies een andere poort, bijvoorbeeld: python app.py --port {args.port + 1}")
        sys.exit(1)

    url = f"http://{HOST}:{args.port}"
    print(BANNER)
    print(f"  → {url}")
    print("  Stoppen: Ctrl+C\n")

    app = create_app(start_background=True)  # connects to Portflow (spec 003)
    if not args.no_browser:
        threading.Timer(1.0, webbrowser.open, args=(url,)).start()
    app.run(host=HOST, port=args.port, debug=False)


if __name__ == "__main__":
    main()
