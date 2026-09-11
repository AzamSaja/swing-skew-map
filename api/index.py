import sys
import urllib.parse
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
            raw_qs = scope.get("query_string", b"").decode("latin1")
            if "__path" in raw_qs:
                params = urllib.parse.parse_qsl(raw_qs, keep_blank_values=True)
                path_val = "/"
                filtered_params = []
                for k, v in params:
                    if k == "__path":
                        path_val = v if v.startswith("/") else f"/{v}"
                    else:
                        filtered_params.append((k, v))
                scope["path"] = path_val
                scope["raw_path"] = path_val.encode("latin1")
                scope["query_string"] = urllib.parse.urlencode(filtered_params).encode("latin1")
            elif scope.get("path") in ["/api/index.py", "/api/index", "/api"]:
                scope["path"] = "/"
                scope["raw_path"] = b"/"
        await self.app(scope, receive, send)

app = VercelPathRewriter(fastapi_app)