from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

import pytest

pytest.importorskip("uplink")
from uplink_parse.consumer import Consumer  # noqa: E402


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")


def test_request_accepts_absolute_url_on_another_host() -> None:
    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/page"
        response = Consumer("https://unused.example").request("GET", url)
        assert response.status_code == 200
        assert response.text == "ok"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
