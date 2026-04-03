#!/usr/bin/python3
"""
sre.vaultconfig — a minimal Vault-like key-value store.

Data model:  tenant (company)  →  group  →  key  →  value
Persistence: JSON flat-file (STORE_FILE env var, default vault_data.json)
"""

import json
import logging
import os

from flask import Flask, Response, abort, request

STORE_FILE = os.environ.get("STORE_FILE", "vault_data.json")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------

def _load() -> dict:
    """Load the store from disk; return empty dict if the file is missing."""
    if os.path.exists(STORE_FILE):
        with open(STORE_FILE) as fh:
            return json.load(fh)
    return {}


def _save(store: dict) -> None:
    """Persist the store to disk atomically."""
    tmp = STORE_FILE + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(store, fh, indent=2)
    os.replace(tmp, STORE_FILE)


def _json(data, status: int = 200) -> Response:
    return Response(json.dumps(data, ensure_ascii=False),
                    status=status,
                    content_type="application/json")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/v1", methods=["GET"])
def list_tenants():
    """List all tenant names."""
    store = _load()
    return _json({"tenants": sorted(store.keys())})


@app.route("/v1/<tenant>", methods=["GET"])
def list_groups(tenant: str):
    """List all groups for a tenant."""
    store = _load()
    if tenant not in store:
        abort(404, description=f"Tenant '{tenant}' not found")
    return _json({"tenant": tenant, "groups": sorted(store[tenant].keys())})


@app.route("/v1/<tenant>/<group>", methods=["GET"])
def list_keys(tenant: str, group: str):
    """List all keys inside a group."""
    store = _load()
    if tenant not in store or group not in store.get(tenant, {}):
        abort(404, description=f"Group '{tenant}/{group}' not found")
    return _json({"tenant": tenant,
                  "group": group,
                  "keys": sorted(store[tenant][group].keys())})


@app.route("/v1/<tenant>/<group>/<key>", methods=["GET"])
def read_secret(tenant: str, group: str, key: str):
    """Read a single secret value."""
    store = _load()
    try:
        value = store[tenant][group][key]
    except KeyError:
        abort(404, description=f"Key '{tenant}/{group}/{key}' not found")
    return _json({"tenant": tenant, "group": group, "key": key, "value": value})


@app.route("/v1/<tenant>/<group>/<key>", methods=["PUT"])
def write_secret(tenant: str, group: str, key: str):
    """Create or update a secret.  Body: {"value": "<secret>"}"""
    body = request.get_json(silent=True) or {}
    if "value" not in body:
        abort(400, description="Request body must contain a 'value' field")
    store = _load()
    tenant_store = store.setdefault(tenant, {})
    group_store = tenant_store.setdefault(group, {})
    group_store[key] = body["value"]
    _save(store)
    logger.info("Written %s/%s/%s", tenant, group, key)
    return _json({"tenant": tenant, "group": group, "key": key,
                  "value": body["value"]}, status=201)


@app.route("/v1/<tenant>/<group>/<key>", methods=["DELETE"])
def delete_secret(tenant: str, group: str, key: str):
    """Delete a secret."""
    store = _load()
    try:
        del store[tenant][group][key]
    except KeyError:
        abort(404, description=f"Key '{tenant}/{group}/{key}' not found")
    # Clean up empty parent nodes
    if not store[tenant][group]:
        del store[tenant][group]
    if not store[tenant]:
        del store[tenant]
    _save(store)
    logger.info("Deleted %s/%s/%s", tenant, group, key)
    return _json({"deleted": True, "key": key})


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(400)
@app.errorhandler(404)
def http_error(e):
    return _json({"error": e.description}, status=e.code)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
