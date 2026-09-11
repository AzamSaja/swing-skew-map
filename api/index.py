import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from web.app import app as fastapi_app

class VercelPathRewriter:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = dict(scope.get("headers", []))
            if b"check_headers" in scope.get("query_string", b""):
                raw_headers = {k.decode("latin1"): v.decode("latin1") for k, v in headers.items()}
                body = json.dumps({"headers": raw_headers, "scope_path": scope.get("path")}).encode("utf-8")
                await send({
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [[b"content-type", b"application/json"]]
                })
                await send({
                    "type": "http.response.body",
                    "body": body
                })
                return
            
            for h in [b"x-matched-path", b"x-vercel-matched-path", b"x-forwarded-uri", b"x-original-uri"]:
                if h in headers:
                    val = headers[h].decode("latin1")
                    if val:
                        if "?" in val:
                            path_part, qs_part = val.split("?", 1)
                            scope["path"] = path_part
                            scope["raw_path"] = path_part.encode("latin1")
                            if not scope.get("query_string"):
                                scope["query_string"] = qs_part.encode("latin1")
                        else:
                            scope["path"] = val
                            scope["raw_path"] = val.encode("latin1")
                        break
            else:
                if scope.get("path") in ["/api/index.py", "/api/index", "/api"]:
                    scope["path"] = "/"
                    scope["raw_path"] = b"/"
        await self.app(scope, receive, send)

app = VercelPathRewriter(fastapi_app)