"""Simple HTTP server that serves a static HTML page.

Listens on port 8081 inside the container. Uses only the stdlib.
"""

import http.server
import socketserver

PORT = 8081

HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>OpenHost Extra Ports Test</title>
    <style>
        body { font-family: system-ui, sans-serif; max-width: 600px; margin: 4rem auto; padding: 0 1rem; }
        h1 { color: #2563eb; }
        code { background: #f1f5f9; padding: 0.2em 0.4em; border-radius: 4px; }
    </style>
</head>
<body>
    <h1>Static HTTP Server</h1>
    <p>This page is served on an <strong>extra port</strong> declared via <code>[[ports]]</code> in <code>openhost.toml</code>.</p>
    <p>If you can see this, the port mapping is working.</p>
</body>
</html>
"""


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML.encode())

    def log_message(self, fmt, *args):
        print(f"static_http: {fmt % args}", flush=True)


if __name__ == "__main__":
    with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
        print(f"static_http: listening on :{PORT}", flush=True)
        httpd.serve_forever()
