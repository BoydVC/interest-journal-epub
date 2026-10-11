#!/usr/bin/env python3
"""Interest Journal EPUB server — 127.0.0.1:4313."""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("PORT", 4313))


def rd(rel):
    with open(os.path.join(HERE, rel), encoding="utf-8") as f:
        return f.read()


def chapters_js():
    p = os.path.join(HERE, "data", "chapters.json")
    if os.path.isfile(p):
        return open(p, encoding="utf-8").read()
    return "null"


def page():
    html = rd("web/index.html")
    html = html.replace("/*__CSS__*/", rd("web/app.css"))
    html = html.replace("/*__CHAPTERS__*/ null /*__/CHAPTERS__*/", chapters_js())
    html = html.replace(
        "/*__APP__*/", rd("web/app.js").replace("</script", "<\\/script")
    )
    return html


class H(BaseHTTPRequestHandler):
    def send(self, code, body, ctype, extra=None):
        b = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-store")
        if extra:
            for k, v in extra.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        path = self.path.split("?")[0]
        try:
            if path in ("/", "/index.html", "/interest-journal-epub.html"):
                self.send(200, page(), "text/html; charset=utf-8")
            elif path in ("/dist/interest-journal.epub", "/interest-journal.epub"):
                ep = os.path.join(HERE, "dist", "interest-journal.epub")
                if not os.path.isfile(ep):
                    self.send(404, "epub not built", "text/plain")
                    return
                with open(ep, "rb") as f:
                    data = f.read()
                self.send(
                    200,
                    data,
                    "application/epub+zip",
                    {"Content-Disposition": 'attachment; filename="interest-journal.epub"'},
                )
            elif path == "/api/chapters":
                raw = chapters_js()
                if raw == "null":
                    self.send(404, json.dumps({"error": "missing"}), "application/json")
                    return
                self.send(200, raw, "application/json")
            elif path == "/health":
                self.send(
                    200,
                    json.dumps({"ok": True, "port": PORT, "app": "interest-journal-epub"}),
                    "application/json",
                )
            else:
                self.send(404, "not found", "text/plain")
        except Exception as ex:
            self.send(500, f"error: {ex}", "text/plain")

    def log_message(self, fmt, *args):
        print(f"[interest-journal-epub] {args[0]}")


if __name__ == "__main__":
    httpd = ThreadingHTTPServer(("127.0.0.1", PORT), H)
    print(f"Interest Journal EPUB http://127.0.0.1:{PORT}/")
    httpd.serve_forever()
