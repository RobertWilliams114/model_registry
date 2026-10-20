# Model Registry

**A versioned ML model registry with artifact storage and container-based deployment — the MLflow registry, rebuilt from the database up to understand what it actually does.**

Training a model is the part everyone writes tutorials about. Getting that model versioned, stored, promoted to production, and served behind an HTTP endpoint is the part that makes it useful, and it is almost entirely a systems problem: schema design, migrations, object storage, and process supervision.

This is that layer, built from scratch. FastAPI and SQLAlchemy over Postgres for the registry itself, S3 presigned URLs for artifacts, Alembic for schema evolution, and a Docker orchestrator that launches a separate inference container per deployed version.

---

## The problem it solves

A team trains five versions of a fraud model. Which one is in production? Where is its artifact? Who owns it? If the new version is worse, what exactly do you roll back to?

Answering that needs three things, and this registry provides each one:

| Need | Mechanism |
|---|---|
| Stable identity for a model, independent of its versions | `models` table; versions reference it by foreign key |
| Exactly one current version per model, enforced on write | `create_version` demotes the incumbent in the same transaction |
| An artifact you can actually retrieve later | Presigned S3 `PUT`/`GET` URLs keyed by `model_id/version_tag/filename` |

The promotion rule is the one with real teeth. Marking a new version current has to atomically clear the flag on the previous one and update the parent model's pointer, or the registry can report two production versions at once. `src/registry/crud.py` does both updates before the insert and commits once.

---

## Architecture

```
   client
     |
     |  POST /models/{id}/versions          POST /deployments
     v                                            |
+----------------------+                          |
|  FastAPI  (registry) |                          v
|  main.py  11 routes  |                  +-----------------+
+----------+-----------+                  |  orchestrator   |
           |                              |  docker run     |
     +-----+------+                       |  poll /health   |
     |            |                       +--------+--------+
     v            v                                |
+---------+  +-----------+                         v
| Postgres|  |    S3     |                 +---------------+
| models  |  | presigned |                 | inference svc |
| versions|  |  PUT/GET  |                 | FastAPI       |
|deploymts|  +-----------+                 | /health       |
+----+----+                                | /predict      |
     ^                                     +---------------+
     |
  Alembic
 5 migrations
```

Two services, deliberately separated. The registry is a long-lived control plane that owns metadata; an inference service is a short-lived data plane that owns one model's weights and nothing else. They share no database and no code — the orchestrator's only contract with a deployed container is `GET /health` returning 200.

### Why presigned URLs instead of proxying uploads

The obvious design has the client `POST` a model file to the API, which forwards it to S3. That puts a multi-gigabyte checkpoint through the API process, where it consumes a worker for the duration of the transfer and bounds throughput by the API's bandwidth rather than S3's.

Instead, `POST /models/{model_id}/versions/{version_tag}/upload` records the object key in the database and returns a presigned `POST` policy. The client uploads directly to S3. The API handles bytes of JSON, never bytes of model. `GET .../upload-form` returns a browser form built from the same policy, which is how this gets tested by hand.

The tradeoff is that the database records the artifact URI *before* the upload is known to have succeeded, so a client that abandons the transfer leaves a version row pointing at an object that does not exist. A completion callback or a reconciliation sweep would close that gap; neither is implemented.

### Schema evolution is tracked, not improvised

Five Alembic migrations, in order:

```
2344cad24b57  create models and versions
c52db5868ca8  add versions.artifact_uri
8c265dfcf651  make artifact_uri nullable
10160c94f363  add models.owner_team
d5ea0e477d5d  add deployments table
```

The third one exists because the second got it wrong: `artifact_uri` was added `NOT NULL`, which made it impossible to create a version before uploading its artifact. The fix is a migration rather than an edit to the original, so the history stays replayable from an empty database. That sequence is the honest record of the schema being designed incrementally.

---

## Quickstart

**Requirements:** Python 3.10+, Docker, and AWS credentials in `~/.aws` if you want the artifact endpoints.

```bash
# Postgres and the API together
docker compose up --build

# or run the API against your own database
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e ".[dev]"

export DATABASE_URL="postgresql+psycopg2://registry:registry@localhost:5432/registry"
alembic upgrade head
uvicorn registry.main:app --reload
```

Interactive API docs at `http://localhost:8000/docs`.

```bash
# register a model, then a version, and promote it
curl -X POST localhost:8000/models \
  -H 'Content-Type: application/json' \
  -d '{"name": "fraud-detector", "description": "gradient boosted trees"}'

curl -X POST localhost:8000/models/$MODEL_ID/versions \
  -H 'Content-Type: application/json' \
  -d '{"model_id": "'$MODEL_ID'", "version_tag": "1.0.0",
       "framework": "LightGBM", "promote_to_current": true}'
```

### Deploying a version

The inference service is a standalone FastAPI app that loads weights from a JSON file at startup and serves a linear model:

```bash
cd inference-service
docker build -t inference-demo .
docker run -d -p 8001:8000 inference-demo
curl localhost:8001/health
curl -X POST localhost:8001/predict -d '{"input": [1.0, 2.0, 3.0]}'
```

`src/registry/orchestrator.py` drives that lifecycle programmatically — `start_container`, `wait_for_healthy` with a timeout, `stop_container`. The deployment *endpoints* that would expose this over HTTP are stubs; see Limitations.

---

## Project layout

```
src/registry/
  main.py          FastAPI app, 11 routes
  models.py        SQLAlchemy ORM: Model, Version, DeploymentRecord
  schemas.py       Pydantic request/response models
  crud.py          queries, including the version-promotion transaction
  db.py            lazy engine, session factory, FastAPI dependency
  orchestrator.py  docker run / health poll / docker stop
  storage/
    s3.py          presigned PUT and GET
    local.py       filesystem fallback
alembic/versions/  5 migrations
inference-service/ separate deployable app and Dockerfile
tests/
```

### Database access is lazy, on purpose

`db.py` builds the engine on first use rather than at import:

```python
def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(get_database_url(), echo=False)
    return _engine
```

The earlier version called `create_engine(...)` at module level, which meant `import registry.crud` opened a connection pool. Any test of the CRUD layer therefore needed a reachable Postgres before a single fixture could run, so the business logic was untestable for reasons that had nothing to do with the business logic. Deferring engine construction lets a test inject an in-memory SQLite engine and exercise the promotion rule in milliseconds.

The URL also pins its driver — `postgresql+psycopg2://` rather than `postgresql://` — because a bare scheme resolves to psycopg2 on SQLAlchemy 2.0 and to psycopg v3 on 2.1+, which turns a dependency bump into a connection failure.

---

## Stack

Python 3.12 · FastAPI · SQLAlchemy 2.0 · Alembic · Pydantic v2 · PostgreSQL 16 · boto3 / S3 · Docker

---

## Limitations

- **The deployment endpoints are not implemented.** `POST /deployments` and `GET /deployments/{id}` are stubs that return nothing. The `deployments` table and `orchestrator.py` both exist and work, but nothing wires the orchestrator to the API, so deployment is currently a library call rather than a service.
- **No authentication.** Every endpoint is open, and `owner_team` is recorded but never enforced.
- **No test suite.** `tests/` is a package with nothing in it. The CRUD layer is now structured to be testable, which is the prerequisite, not the achievement.
- The S3 bucket name is hardcoded in `src/registry/storage/s3.py`; it should come from configuration.
- `storage/local.py` is a filesystem fallback that no route uses — the upload path is S3-only.
- The inference service serves a dot product from `model.json`. It demonstrates the deployment contract rather than real inference; loading a genuine PyTorch or LightGBM artifact is the obvious extension.
- Single-node orchestration via `docker run`. A real platform would target Kubernetes, and `wait_for_healthy` is a stand-in for a readiness probe.

> **Note on history:** model artifacts (`*.pth`) and database files were committed early in this project's life and have since been stripped from the git history to keep the repository small. Commits before the restructure reference an `artifacts/` directory that will be empty on checkout.

---

## Roadmap

- Wire `POST /deployments` to the orchestrator and record the result in `DeploymentRecord`
- A test suite: the promotion invariant first, since "exactly one current version" is the one rule worth enforcing
- Load real framework artifacts in the inference service instead of a JSON weight vector
- Move bucket, region, and credentials into configuration
- API key or OIDC authentication, with `owner_team` as the authorization boundary
- Kubernetes deployment target behind the same orchestrator interface

---

## Provenance

Built as a self-directed study of ML platform engineering, worked through in incremental layers — database schema, then CRUD, then artifact storage, then containerized deployment. The learning plan that structured it is preserved at `docs/learning-plan.md`. The per-layer directories were collapsed into the current package during cleanup; their history remains in the git log.
