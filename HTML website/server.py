import base64
import hashlib
import json
import re
import secrets
import gzip
import mimetypes
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

PORT = 5050
DATA_FILE = Path(__file__).with_name("registrations.json")
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class RegistrationHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Set cache headers based on file type
        path = self.path
        if path.endswith(('.html', '.css', '.js')):
            # Cache static assets for 24 hours
            self.send_header("Cache-Control", "public, max-age=86400")
        elif path.endswith(('.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ico')):
            # Cache images for 7 days
            self.send_header("Cache-Control", "public, max-age=604800")
        else:
            # API endpoints and other resources: 5 minutes
            self.send_header("Cache-Control", "public, max-age=300")
        super().end_headers()

    def do_OPTIONS(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/api/register", "/api/registrations"):
            self._send_json(204, None)
            return
        self.send_error(404, "Not found")

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/registrations":
            self._send_json(200, self._load_records())
            return
        # Use parent implementation for static files
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/register":
            self._handle_register()
            return
        self.send_error(404, "Not found")

    def _handle_register(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length) if content_length > 0 else b"{}"
            payload = json.loads(raw_body.decode("utf-8") or "{}")
        except Exception:
            self._send_json(400, {"ok": False, "message": "Invalid JSON body."})
            return

        name = (payload.get("name") or "").strip()
        email = (payload.get("email") or "").strip().lower()
        password = (payload.get("password") or "")

        if not name or not email or not password:
            self._send_json(400, {"ok": False, "message": "Please complete all fields."})
            return

        if not EMAIL_RE.match(email):
            self._send_json(400, {"ok": False, "message": "Please enter a valid email address."})
            return

        if len(password) < 8:
            self._send_json(400, {"ok": False, "message": "Password must be at least 8 characters long."})
            return

        records = self._load_records()
        if any(record.get("email") == email for record in records):
            self._send_json(409, {"ok": False, "message": "An account with this email already exists."})
            return

        salt = secrets.token_bytes(16)
        derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120000)
        record = {
            "name": name,
            "email": email,
            "passwordHash": f"{base64.b64encode(salt).decode('ascii')}:{base64.b64encode(derived).decode('ascii')}",
            "createdAt": __import__("datetime").datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        }
        records.append(record)
        DATA_FILE.write_text(json.dumps(records, indent=2), encoding="utf-8")

        self._send_json(201, {"ok": True, "message": "Registration saved securely."})

    def _load_records(self):
        if not DATA_FILE.exists():
            return []
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _send_json(self, status_code, payload):
        if payload is None:
            body = b""
        else:
            body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        if body:
            self.wfile.write(body)


if __name__ == "__main__":
    # Allow address reuse and enable daemon threads for faster startup
    ThreadingHTTPServer.allow_reuse_address = True
    with ThreadingHTTPServer(("", PORT), RegistrationHandler) as httpd:
        httpd.daemon_threads = True
        print(f"Serving HTTP on http://localhost:{PORT}")
        print("Press Ctrl+C to stop the server.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
