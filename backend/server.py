"""
REST API & Web Server
Step 1: Base ThreadingHTTPServer setup on port 8000
"""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = "0.0.0.0"
PORT = 8000


class ESGRequestHandler(BaseHTTPRequestHandler):
    """Handles incoming HTTP requests for the ESG platform API."""

    def do_GET(self):
        # Placeholder response; real routes are registered in the next step
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ESG server is running")

    def do_POST(self):
        # Placeholder response; real routes are registered in the next step
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"POST received")


def run_server(host: str = HOST, port: int = PORT):
    """
    Start the server using ThreadingHTTPServer so each request is handled
    on its own thread, allowing multiple clients to connect concurrently.
    """
    server = ThreadingHTTPServer((host, port), ESGRequestHandler)
    print(f"ESG server listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()


if __name__ == "__main__":
    run_server()