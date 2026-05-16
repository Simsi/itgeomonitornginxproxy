import gzip
import http.client
import os
import socketserver
import zlib
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Iterable, Tuple

LISTEN_HOST = os.getenv("LISTEN_HOST", "127.0.0.1")
LISTEN_PORT = int(os.getenv("LISTEN_PORT", "18050"))

TARGET_HOST = os.getenv("TARGET_HOST", "127.0.0.1")
TARGET_PORT = int(os.getenv("TARGET_PORT", "8050"))

OLD_WS_PORT = os.getenv("OLD_WS_PORT", "8765")
NEW_WS_PORT = os.getenv("NEW_WS_PORT", "4014")
PUBLIC_HOST = os.getenv("PUBLIC_HOST", "84.237.52.214")
PUBLIC_HTTP_PORT = os.getenv("PUBLIC_HTTP_PORT", "4015")

TEXT_CONTENT_MARKERS = (
    "text/",
    "javascript",
    "json",
    "xml",
    "wasm",
)

HOP_BY_HOP_RESPONSE_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
    "content-length",
    "content-encoding",
}

HOP_BY_HOP_REQUEST_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}


def should_rewrite(content_type: str) -> bool:
    content_type = (content_type or "").lower()
    return any(marker in content_type for marker in TEXT_CONTENT_MARKERS)


def decode_body(data: bytes, content_encoding: str) -> Tuple[bytes, bool]:
    encoding = (content_encoding or "").lower().strip()
    if not encoding:
        return data, False

    try:
        if encoding == "gzip":
            return gzip.decompress(data), True
        if encoding == "deflate":
            return zlib.decompress(data), True
    except Exception:
        return data, False

    return data, False


def rewrite_body(data: bytes) -> bytes:
    replacements = [
        (f"ws://{PUBLIC_HOST}:{OLD_WS_PORT}".encode(), f"ws://{PUBLIC_HOST}:{NEW_WS_PORT}".encode()),
        (f"wss://{PUBLIC_HOST}:{OLD_WS_PORT}".encode(), f"wss://{PUBLIC_HOST}:{NEW_WS_PORT}".encode()),
        (f"{PUBLIC_HOST}:{OLD_WS_PORT}".encode(), f"{PUBLIC_HOST}:{NEW_WS_PORT}".encode()),
        (f":{OLD_WS_PORT}".encode(), f":{NEW_WS_PORT}".encode()),
    ]

    for old, new in replacements:
        data = data.replace(old, new)
    return data


def copy_request_headers(source_headers) -> dict:
    headers = {}
    for key, value in source_headers.items():
        if key.lower() in HOP_BY_HOP_REQUEST_HEADERS:
            continue
        headers[key] = value

    # Не просим gzip/br у локального приложения, чтобы переписывание HTML/JS было простым.
    headers.pop("Accept-Encoding", None)

    # Обычно Dash/Flask не требует конкретного Host. Передаём локальный Host, чтобы backend видел
    # ожидаемый адрес. Адреса для браузера исправляются rewrite-слоем в ответе.
    headers["Host"] = f"{TARGET_HOST}:{TARGET_PORT}"
    headers["X-Forwarded-Host"] = source_headers.get("Host", f"{PUBLIC_HOST}:{PUBLIC_HTTP_PORT}")
    headers["X-Forwarded-Proto"] = "http"
    return headers


class RewriteProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args) -> None:
        print(f"{self.client_address[0]} - {fmt % args}", flush=True)

    def do_GET(self):
        self.proxy()

    def do_POST(self):
        self.proxy()

    def do_PUT(self):
        self.proxy()

    def do_PATCH(self):
        self.proxy()

    def do_DELETE(self):
        self.proxy()

    def do_OPTIONS(self):
        self.proxy()

    def do_HEAD(self):
        self.proxy(send_body=False)

    def proxy(self, send_body: bool = True) -> None:
        request_body = None
        content_length = self.headers.get("Content-Length")
        if content_length:
            request_body = self.rfile.read(int(content_length))

        headers = copy_request_headers(self.headers)
        conn = http.client.HTTPConnection(TARGET_HOST, TARGET_PORT, timeout=120)

        try:
            conn.request(self.command, self.path, body=request_body, headers=headers)
            resp = conn.getresponse()
            raw_body = resp.read()

            content_type = resp.getheader("Content-Type", "")
            content_encoding = resp.getheader("Content-Encoding", "")

            body = raw_body
            if should_rewrite(content_type):
                decoded, decoded_ok = decode_body(raw_body, content_encoding)
                body = rewrite_body(decoded)
                # После переписывания отдаём без сжатия.
                if content_encoding and not decoded_ok:
                    body = raw_body

            self.send_response(resp.status, resp.reason)

            for key, value in resp.getheaders():
                if key.lower() not in HOP_BY_HOP_RESPONSE_HEADERS:
                    self.send_header(key, value)

            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()

            if send_body:
                self.wfile.write(body)

        except Exception as exc:
            message = f"rewrite proxy error: {exc}\n".encode()
            self.send_response(502, "Bad Gateway")
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(message)))
            self.send_header("Connection", "close")
            self.end_headers()
            if send_body:
                self.wfile.write(message)
        finally:
            conn.close()


class ThreadingHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


if __name__ == "__main__":
    print(f"rewrite-proxy listening on http://{LISTEN_HOST}:{LISTEN_PORT}", flush=True)
    print(f"proxying to http://{TARGET_HOST}:{TARGET_PORT}", flush=True)
    print(f"rewriting :{OLD_WS_PORT} -> :{NEW_WS_PORT}", flush=True)

    server = ThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), RewriteProxyHandler)
    server.serve_forever()
