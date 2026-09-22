"""
Lab "bank" login server used for the SSL/TLS classroom exercise.

Serves the SAME login form on both:
  - plain HTTP  (port 80)  -> intentionally insecure, for the sniffing demo
  - HTTPS       (port 443) -> self-signed certificate, for the TLS/cert demo

DO NOT use this code as-is for anything real. It exists purely to make
submitted credentials visible in `docker compose logs web` so students can
see what an attacker (or, on port 80, anyone on the network) would capture.
"""

import http.server
import ssl
import threading
from urllib.parse import parse_qs

HSTS_ENABLED = False  # flip to True for the advanced HSTS exercise


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        if HSTS_ENABLED and self.server.server_port == 443:
            # Advanced exercise: uncomment / set HSTS_ENABLED = True and rebuild
            self.send_header(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )
        self.end_headers()
        self.wfile.write(
            """<!doctype html>
            <html><body>
            <h2>Lab-pank login</h2>
            <form method="POST">
                Username: <input name="user"><br>
                Password: <input name="pass" type="password"><br>
                <input type="submit" value="Log in">
            </form>
            </body></html>""".encode("utf-8")
        )

    def do_POST(self):
        length = int(self.headers["Content-Length"])
        body = self.rfile.read(length).decode()
        data = parse_qs(body)
        print(f"[{self.server.server_port}] SERVER RECEIVED DATA: {data}", flush=True)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Login received (lab demo, not a real bank).")

    def log_message(self, fmt, *args):
        # Keep default access logging; override if you want it quieter.
        super().log_message(fmt, *args)


def run_http():
    http.server.HTTPServer(("0.0.0.0", 80), Handler).serve_forever()


def run_https():
    server = http.server.HTTPServer(("0.0.0.0", 443), Handler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain("cert.pem", "key.pem")
    server.socket = ctx.wrap_socket(server.socket, server_side=True)
    server.serve_forever()


if __name__ == "__main__":
    threading.Thread(target=run_http, daemon=True).start()
    run_https()
