# sre.vaultconfig

A minimal, self-hosted **Vault-like key-value store** built with Python / Flask.

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                      HTTP Client                      │
│         (curl / application / CI pipeline)           │
└─────────────────────┬────────────────────────────────┘
                      │ REST (JSON)
┌─────────────────────▼────────────────────────────────┐
│                   Flask API  (app.py)                 │
│                                                       │
│  Tenant ──► Group ──► Key ──► Value                  │
│  (company)  (logical   (secret  (secret               │
│             namespace)  name)    value)               │
└─────────────────────┬────────────────────────────────┘
                      │ read / write
             vault_data.json  (flat-file store)
```

### Data Model

| Level      | Description                                      | Example          |
|------------|--------------------------------------------------|------------------|
| **Tenant** | The owning company / org (top-level namespace)   | `acme`           |
| **Group**  | A logical collection of related secrets          | `database`       |
| **Key**    | The name of an individual secret                 | `db_password`    |
| **Value**  | The secret value (plain string)                  | `s3cr3t!`        |

Stored on disk as a nested JSON object:

```json
{
  "acme": {
    "database": {
      "db_password": "s3cr3t!",
      "db_host": "db.acme.internal"
    },
    "api-keys": {
      "stripe": "sk_live_..."
    }
  }
}
```

---

## API Reference

| Method   | Path                              | Description                        |
|----------|-----------------------------------|------------------------------------|
| `GET`    | `/v1`                             | List all tenants                   |
| `GET`    | `/v1/{tenant}`                    | List groups for a tenant           |
| `GET`    | `/v1/{tenant}/{group}`            | List keys in a group               |
| `GET`    | `/v1/{tenant}/{group}/{key}`      | Read a secret value                |
| `PUT`    | `/v1/{tenant}/{group}/{key}`      | Create / update a secret           |
| `DELETE` | `/v1/{tenant}/{group}/{key}`      | Delete a secret                    |

### Write a secret

```
PUT /v1/{tenant}/{group}/{key}
Content-Type: application/json

{"value": "<secret>"}
```

---

## Quick Start with Docker

```bash
# Build
docker build -t vaultconfig .

# Run (secrets persist in the container; map a volume for durability)
docker run -d \
  -p 5000:5000 \
  -v "$(pwd)/data:/app/data" \
  -e STORE_FILE=/app/data/vault_data.json \
  --name vaultconfig \
  vaultconfig
```

### Smoke test

```bash
# Write a secret
curl -s -X PUT http://localhost:5000/v1/acme/database/db_password \
  -H "Content-Type: application/json" \
  -d '{"value": "s3cr3t!"}' | jq

# Read it back
curl -s http://localhost:5000/v1/acme/database/db_password | jq

# List tenants
curl -s http://localhost:5000/v1 | jq

# Delete
curl -s -X DELETE http://localhost:5000/v1/acme/database/db_password | jq
```

---

## Local Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py        # listens on http://0.0.0.0:5000
```

### Environment variables

| Variable     | Default            | Description                         |
|--------------|--------------------|-------------------------------------|
| `PORT`       | `5000`             | TCP port the server listens on      |
| `STORE_FILE` | `vault_data.json`  | Path to the JSON persistence file   |
