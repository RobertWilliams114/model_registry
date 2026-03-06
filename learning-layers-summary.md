# Learning Layers — Progress Summary

Use this to pick up where you left off on any environment.

---

## Project Location

- Windows: `C:\Users\rjwil\CodingProjects\project_prep\Reusable_Model_Registry`
- Full learning plan: `~/ml-platform-learning-plan.md`

## Layer Overview

| Layer | Status | Description |
|-------|--------|-------------|
| 0 | Complete | Hello Service — FastAPI + uvicorn basics |
| 1 | Complete | In-memory CRUD API |
| 2 | In Progress | SQLite + SQLAlchemy ORM |
| 3–13 | Not Started | See `ml-platform-learning-plan.md` |

---

## Layer 0 — Hello Service (Complete)

- `layer0/main.py` — two endpoints: `GET /health`, `GET /`
- Confirmed FastAPI, uvicorn, and Swagger UI all work

---

## Layer 1 — In-Memory CRUD (Complete)

### Files

| File | Purpose |
|------|---------|
| `main.py` | Routes only — calls store functions |
| `schemas.py` | Pydantic request/response models |
| `store.py` | Dict-based in-memory storage + UUID generation |

### Endpoints

```
POST   /models                     → create model
GET    /models                     → list all models
GET    /models/{model_id}          → get single model
DELETE /models/{model_id}          → delete model
POST   /models/{model_id}/versions → create version
GET    /models/{model_id}/versions → list versions for model
```

### Schemas

- `ModelCreate` — name, description (optional)
- `ModelResponse` — id, name, description, current_version_id
- `VersionCreate` — model_id, version_tag, framework (enum), promote_to_current
- `VersionResponse` — id, model_id, version_tag, framework, current_version
- `enum_frameworks` — PyTorch, TensorFlow, LightGBM

### Key decisions

- Server generates UUIDs, not the client
- `Create` schemas have no `id` field; `Response` schemas do
- Store functions build the complete object and return it

---

## Layer 2 — SQLite + SQLAlchemy (In Progress)

### What changed from Layer 1

Replaced `store.py` (in-memory lists) with a real database using SQLAlchemy ORM.

### Files

| File | Purpose |
|------|---------|
| `db.py` | Engine, Base, sessionmaker, `get_db()` dependency |
| `models.py` | SQLAlchemy ORM classes (Model, Version) |
| `crud.py` | All DB operations — replaces `store.py` |
| `schemas.py` | Same Pydantic schemas + `ConfigDict(from_attributes=True)` |
| `main.py` | Routes inject `db: Session = Depends(get_db)`, call crud functions |

### db.py structure

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

engine = create_engine("sqlite:///registry.db", echo=True)
Base = declarative_base()
Session = sessionmaker(bind=engine)

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()
```

### models.py structure

- `Model` — id (String PK), name, description, current_version_id, versions (relationship)
- `Version` — id (String PK), version_tag, framework, model_id (FK → models.id), current_version (Boolean), model (relationship)
- All UUID columns stored as `String` because SQLite doesn't support native UUID
- Enum handled by Pydantic, not SQLAlchemy — framework column is just `String`

### crud.py structure

- `create_model(db, data)` — creates Model object with `str(uuid4())`, db.add, db.commit
- `get_models(db)` — `db.query(Model).all()`
- `get_model(db, model_id)` — `.filter().first()`
- `delete_model(db, model_id)` — `.filter().delete()`, db.commit
- `create_version(db, data)` — creates Version object, converts model_id to str, db.add, db.commit
- `get_versions(db, model_id)` — `.filter().all()`

### main.py pattern

```python
from db import engine, Base, get_db
from sqlalchemy.orm import Session

Base.metadata.create_all(bind=engine)

@app.post("/models", response_model=schemas.ModelResponse, ...)
def create_model(payload: schemas.ModelCreate, db: Session = Depends(get_db)):
    return crud.create_model(db, payload)
```

### schemas.py changes from Layer 1

Added `ConfigDict(from_attributes=True)` to response schemas so Pydantic can read attributes from SQLAlchemy objects:

```python
from pydantic import BaseModel, Field, ConfigDict

class ModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    ...
```

### What's left to finish Layer 2

**Version promotion logic** in `crud.create_version`:

1. When `promote_to_current` is `True`:
   - Query for existing version on the same model where `current_version == True`
   - Set that old version's `current_version` to `False`
   - Set the new version's `current_version` to `True`
   - Query for the parent Model, update its `current_version_id` to the new version's ID
2. All changes within a single `db.commit()` so they succeed or fail together

---

## Key Lessons Learned

### Python / FastAPI

- Relative imports (`from .`) don't work when running a file directly with uvicorn — use regular imports (`import schemas`)
- `{payload}` creates a **set**, not a dict — return the object directly: `return payload`
- Pydantic models aren't dicts — can't use `payload["id"]`, use `setattr` or build a new object
- Path parameters must come before parameters with defaults in function signatures
- `Depends(get_db)` not `Depends(get_db())` — don't call the function, pass it

### Architecture patterns

- `ModelCreate` (what client sends) vs `ModelResponse` (what client gets back) — server generates UUID in between
- Route → crud function → database. Routes should not contain DB logic.
- `get_db()` creates a **new session per request** — don't reuse a global session

### SQLAlchemy specifics

- SQLAlchemy model attribute names must match Pydantic schema field names for `from_attributes` to work
- SQLite doesn't support native UUID — store as `String`, convert with `str(uuid4())`
- Python `Enum` isn't a valid SQLAlchemy column type — use `String` and let Pydantic handle validation
- `.query()` returns a query object — need `.all()` for lists, `.first()` for single results
- `db.commit()` must be called after `db.add()` or `.delete()` to persist changes
- `declarative_base()` must be created once and shared — don't create separate instances in different files

---

## Next: Layer 3 — Alembic Migrations

After finishing version promotion logic:

1. Remove `Base.metadata.create_all()` from main.py
2. Initialize Alembic: `alembic init alembic`
3. Configure `alembic/env.py` to import your `Base` and models
4. Generate first migration: `alembic revision --autogenerate -m "create tables"`
5. Apply: `alembic upgrade head`
6. Make a schema change, generate second migration, apply it
7. Verify `alembic downgrade` and `alembic upgrade` work cleanly
