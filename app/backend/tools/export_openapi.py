"""Print the API's OpenAPI document. No server, no database: the schema comes from the code."""

from __future__ import annotations

import json
import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://unused@localhost/unused")  # imported, never connected

from fastapi.openapi.utils import get_openapi  # noqa: E402

from ofs.main import app  # noqa: E402
from ofs.schemas import LIVE_MESSAGE, REQUESTS  # noqa: E402

doc = get_openapi(title=app.title, version="0.1.0", routes=app.routes)
# The WebSocket's frames, so the views type them too (ws.py).
live = LIVE_MESSAGE.json_schema(ref_template="#/components/schemas/{model}")
schemas = doc.setdefault("components", {}).setdefault("schemas", {})
for name, schema in live.pop("$defs", {}).items():
    schemas.setdefault(name, schema)
schemas["LiveMessage"] = live
# Each command's payload model (CommandIn.payload is a plain object on the wire), so the views type what they send.
for model in sorted(set(REQUESTS.values()), key=lambda m: m.__name__):
    one = model.model_json_schema(ref_template="#/components/schemas/{model}")
    for name, schema in one.pop("$defs", {}).items():
        schemas.setdefault(name, schema)
    schemas.setdefault(model.__name__, one)
print(json.dumps(doc, indent=2, sort_keys=True))
