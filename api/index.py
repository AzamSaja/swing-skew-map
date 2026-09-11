import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from web.app import app

@app.middleware("http")
async def vercel_path_rewrite(request, call_next):
    # If request was rewritten by Vercel, restore original client path
    for h in ["x-matched-path", "x-vercel-matched-path", "x-forwarded-uri", "x-original-uri"]:
        val = request.headers.get(h)
        if val:
            path_val = val.split("?")[0]
            if path_val and path_val != request.scope["path"]:
                request.scope["path"] = path_val
                request.scope["raw_path"] = path_val.encode("latin1")
                break
    else:
        if request.scope.get("path") in ["/api/index.py", "/api/index", "/api"]:
            request.scope["path"] = "/"
            request.scope["raw_path"] = b"/"
    return await call_next(request)