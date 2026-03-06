# ML Platform Engineering — Layer-by-Layer Build Plan

Every layer produces a working artifact. Every project extends the previous one. By the end, you have a real model registry + inference deploy pipeline.

---

## Layer 0 — Environment + Hello Service

**Goal:** Prove your toolchain works. Nothing fancy.

**Mini-project:** `hello-api/`

### What to build

| File | Contents |
|------|----------|
| `main.py` | Two routes: `GET /health` → `{"status":"ok"}`, `GET /` → `{"message":"hello"}` |
| `requirements.txt` | `fastapi`, `uvicorn` |

### Steps

1. Create project folder `hello-api/`
2. Create and activate a venv: `python -m venv .venv && source .venv/bin/activate`
3. `pip install fastapi uvicorn`
4. Write `main.py` with the two endpoints
5. Run: `uvicorn main:app --reload`
6. Open `http://127.0.0.1:8000/docs` — confirm Swagger loads
7. Hit `/health` — confirm JSON response

### Success checks

- [ ] Server starts with `--reload`
- [ ] `/health` returns JSON
- [ ] `/docs` loads interactive Swagger UI

### Resources

| Type | Resource |
|------|----------|
| Docs | [FastAPI First Steps](https://fastapi.tiangolo.com/tutorial/first-steps/) |
| Video | [FastAPI in 5 Minutes — Fireship](https://www.youtube.com/watch?v=0RS9W8MtZe4) |

---

## Layer 1 — CRUD API with In-Memory Storage

**Goal:** Learn endpoint design, Pydantic schemas, and CRUD logic — no database yet.

**Mini-project:** `mini-registry-memory/` (new project, extends nothing)

### Data model

```
Model:   { id, name, description, created_at }
Version: { id, model_id, version_tag, framework, created_at }
```

### What to build

| File | Responsibility |
|------|---------------|
| `schemas.py` | Pydantic request/response models (`ModelCreate`, `ModelResponse`, `VersionCreate`, `VersionResponse`) |
| `store.py` | Dict-based in-memory "database" with CRUD functions |
| `main.py` | Routes only — calls `store.py` functions |

### Endpoints

```
POST   /models                         → create model
GET    /models                         → list all models
GET    /models/{model_id}              → get single model
DELETE /models/{model_id}              → delete model
POST   /models/{model_id}/versions     → create version for model
GET    /models/{model_id}/versions     → list versions for model
```

### Steps

1. Define Pydantic schemas first (request vs response separation)
2. Build `store.py` — use `dict[str, ModelResponse]` as your "table", generate UUIDs for IDs
3. Wire routes in `main.py` using FastAPI's dependency injection for the store
4. Test every endpoint in `/docs`

### Success checks

- [ ] Create a model, get it back by ID
- [ ] Add two versions to that model
- [ ] List versions — both appear
- [ ] Delete model — it's gone
- [ ] Restart server — data is gone (expected, it's in-memory)

### Resources

| Type | Resource |
|------|----------|
| Docs | [FastAPI Tutorial — Path/Query/Body](https://fastapi.tiangolo.com/tutorial/) |
| Docs | [Pydantic v2 Models](https://docs.pydantic.dev/latest/concepts/models/) |
| Video | [FastAPI Full Course — freeCodeCamp (3h)](https://www.youtube.com/watch?v=0sOvCWFmrtA) — watch first 90 min |

---

## Layer 2 — Replace In-Memory with SQLite + SQLAlchemy

**Goal:** Learn ORM mapping, sessions, and why schemas/models/crud are separated.

**Mini-project:** `mini-registry-sqlite/` (copy Layer 1, replace `store.py` with real DB)

### What changes from Layer 1

| File | What's new |
|------|-----------|
| `db.py` | Engine, `SessionLocal`, `Base`, `get_db()` dependency |
| `models.py` | SQLAlchemy ORM classes (`ModelRecord`, `VersionRecord`) with relationships |
| `crud.py` | Pure functions (no FastAPI imports) — `create_model(db, data)`, etc. |
| `schemas.py` | Same as Layer 1 (Pydantic stays the same) |
| `main.py` | Routes now call `crud.py`, inject `db` via `Depends(get_db)` |

**Delete:** `store.py` — replaced by `db.py` + `models.py` + `crud.py`

### Database

SQLite: `sqlite:///./app.db` (zero setup)

### Steps

1. Install `sqlalchemy`
2. Create `db.py` — engine, session factory, `Base`, and the `get_db()` generator
3. Create `models.py` — ORM models with `relationship()` between Model ↔ Version
4. Create `crud.py` — all DB operations as plain functions
5. Update `main.py` — swap store calls for crud calls, add `Depends(get_db)`
6. Add `Base.metadata.create_all(bind=engine)` in startup (temporary — Layer 3 replaces this)
7. Test: create model, add versions, restart server — **data persists**

### Success checks

- [ ] All 6 endpoints still work
- [ ] Restart server — data survives (SQLite file persists)
- [ ] `app.db` file exists and contains your tables
- [ ] Relationships work: versions correctly link to parent model

### Resources

| Type | Resource |
|------|----------|
| Docs | [SQLAlchemy 2.0 ORM Tutorial](https://docs.sqlalchemy.org/en/20/orm/quickstart.html) |
| Docs | [FastAPI — SQL Databases](https://fastapi.tiangolo.com/tutorial/sql-databases/) |
| Video | [SQLAlchemy ORM Explained — Pretty Printed](https://www.youtube.com/watch?v=woKYyhLCcnU) |

---

## Layer 3 — Migrations with Alembic

**Goal:** Learn production DB lifecycle — schema evolves without dropping tables.

**Mini-project:** `mini-registry-alembic/` (continue from Layer 2)

### What changes from Layer 2

| Change | Detail |
|--------|--------|
| Remove | `Base.metadata.create_all()` from startup |
| Add | `alembic/` directory with migration scripts |
| Add | One schema change (e.g., `models.owner_team` column) |

### Steps

1. `pip install alembic`
2. `alembic init alembic`
3. Edit `alembic/env.py` — import your `Base` and set `target_metadata = Base.metadata`
4. Edit `alembic.ini` — set `sqlalchemy.url` to your SQLite path
5. Delete `app.db` (clean start)
6. `alembic revision --autogenerate -m "create tables"` — inspect the generated migration
7. `alembic upgrade head` — tables created
8. Add `owner_team: str | None` column to your Model in `models.py`
9. `alembic revision --autogenerate -m "add owner_team to models"`
10. `alembic upgrade head`
11. Verify: `owner_team` column exists, old data intact

### Success checks

- [ ] `alembic/versions/` has two migration files
- [ ] `alembic upgrade head` from empty DB creates everything
- [ ] `alembic downgrade -1` removes the `owner_team` column
- [ ] `alembic upgrade head` adds it back
- [ ] API still works end-to-end

### Resources

| Type | Resource |
|------|----------|
| Docs | [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html) |
| Docs | [Alembic Auto Generating Migrations](https://alembic.sqlalchemy.org/en/latest/autogenerate.html) |
| Video | [Alembic + SQLAlchemy — Eric Roby](https://www.youtube.com/watch?v=6xVtHkVwR5A) |

---

## Layer 4 — Dockerize the API + Postgres

**Goal:** Run your service like a real microservice. Switch from SQLite to Postgres.

**Mini-project:** `mini-registry-docker/` (continue from Layer 3)

### What changes from Layer 3

| Change | Detail |
|--------|--------|
| Add | `Dockerfile` for the API |
| Add | `docker-compose.yml` — API + Postgres |
| Add | `.env` file with `DATABASE_URL` |
| Change | DB URL switches from SQLite to `postgresql://...` |
| Change | Alembic reads DB URL from environment |

### Files to create

**Dockerfile:**
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml:**
```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: registry
      POSTGRES_PASSWORD: registry
      POSTGRES_DB: registry
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  api:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      - db

volumes:
  pgdata:
```

### Steps

1. Install Docker Desktop
2. Write `Dockerfile` and `docker-compose.yml`
3. Create `.env` with `DATABASE_URL=postgresql://registry:registry@db:5432/registry`
4. Update `db.py` to read `DATABASE_URL` from env
5. Update `alembic.ini` or `env.py` to also read from env
6. Add `psycopg2-binary` to `requirements.txt`
7. `docker compose up --build`
8. In another terminal: run `alembic upgrade head` against the containerized DB (or add it to API startup)
9. Test all endpoints at `http://localhost:8000/docs`

### Key concepts to understand

- **Dockerfile:** `FROM`, `COPY`, `RUN`, `CMD`
- **docker-compose:** service networking (containers reference each other by service name)
- **Volumes:** data persistence across container restarts
- **Environment variables:** config injection

### Success checks

- [ ] `docker compose up --build` starts both containers
- [ ] API reachable at `localhost:8000`
- [ ] Data survives `docker compose down` + `docker compose up` (volume persists)
- [ ] `docker compose down -v` destroys data (volume removed)

### Resources

| Type | Resource |
|------|----------|
| Docs | [Docker Get Started](https://docs.docker.com/get-started/) |
| Docs | [Docker Compose Overview](https://docs.docker.com/compose/) |
| Docs | [Dockerfile Reference](https://docs.docker.com/reference/dockerfile/) |
| Video | [Docker Full Course — TechWorld with Nana (3h)](https://www.youtube.com/watch?v=3c-iBn73dDE) — the single best Docker intro |
| Video | [Docker in 100 Seconds — Fireship](https://www.youtube.com/watch?v=Gjnup-PuquQ) — quick conceptual overview |

---

## Layer 5 — Artifact Storage (Local Filesystem First)

**Goal:** Understand blob storage separate from DB metadata — without AWS complexity.

**Mini-project:** `mini-registry-artifacts/` (continue from Layer 4)

### What changes from Layer 4

| Change | Detail |
|--------|--------|
| Add | `storage_local.py` — file-based blob storage |
| Add | `artifact_uri` column to `VersionRecord` |
| Add | New endpoints for artifact upload/download |
| Add | New Alembic migration for the column |

### New endpoints

```
POST /models/{model_id}/versions/{version_tag}/artifacts/upload
     → accepts file upload, stores to disk, returns artifact_uri

GET  /models/{model_id}/versions/{version_tag}/artifacts/download
     → returns the stored file
```

### storage_local.py functions

```python
build_key(model_id, version_tag, filename) → str
save_file(key, content: bytes) → str       # returns file path
load_file(key) → bytes
exists(key) → bool
delete(key) → None
```

### Steps

1. Create `storage_local.py` — stores files under `./artifacts/{model_id}/{version_tag}/`
2. Add `artifact_uri` column to `VersionRecord`
3. Generate + apply Alembic migration
4. Add upload endpoint — saves file, updates DB with `artifact_uri`
5. Add download endpoint — reads file by key, returns as response
6. Add a Docker volume mount in `docker-compose.yml` for the artifacts dir
7. Test full flow: create model → create version → upload artifact → download artifact

### Success checks

- [ ] Upload a `.pt` or `.json` file via `/docs`
- [ ] File appears on disk in `artifacts/` directory
- [ ] DB stores the `artifact_uri`
- [ ] Download returns the exact same file
- [ ] Restart containers — artifact still accessible

### Resources

| Type | Resource |
|------|----------|
| Docs | [FastAPI — Request Files](https://fastapi.tiangolo.com/tutorial/request-files/) |
| Docs | [FastAPI — FileResponse](https://fastapi.tiangolo.com/advanced/custom-response/#fileresponse) |

---

## Layer 6 — S3 Presigned Upload/Download

**Goal:** Swap local storage for real S3. Learn presigned URL pattern.

**Mini-project:** `mini-registry-s3/` (continue from Layer 5)

### What changes from Layer 5

| Change | Detail |
|--------|--------|
| Replace | `storage_local.py` → `storage_s3.py` |
| Add | `STORAGE_BACKEND` env var to toggle local vs S3 |
| Change | Endpoints return presigned URLs instead of handling file bytes |

### New endpoint behavior

```
POST /models/{model_id}/versions/{version_tag}/artifacts/presign-put
     → returns { "upload_url": "https://s3...", "key": "..." }

GET  /models/{model_id}/versions/{version_tag}/artifacts/presign-get
     → returns { "download_url": "https://s3..." }
```

### storage_s3.py functions

```python
build_artifact_key(model_id, version_tag, filename) → str
presign_put_url(key, content_type, expires=3600) → str
presign_get_url(key, expires=3600) → str
head_object(key) → dict | None
delete_object(key) → None
```

### Steps

1. Create an S3 bucket (dev) via AWS Console or CLI
2. Configure AWS CLI: `aws configure`
3. `pip install boto3`
4. Write `storage_s3.py`
5. Replace upload/download endpoints with presign endpoints
6. Test the full flow:
   - Request presign-put URL
   - `curl -X PUT "<presigned_url>" -H "Content-Type: application/octet-stream" --data-binary @model.pt`
   - `aws s3 ls s3://your-bucket/` — confirm file exists
   - Request presign-get URL
   - `curl -o downloaded.pt "<presigned_url>"` — confirm same file

### IAM: What you need to know now

- Create an IAM user with `s3:PutObject`, `s3:GetObject`, `s3:HeadObject` on your bucket
- Use access key + secret key in `~/.aws/credentials`
- **Principle of least privilege:** only grant what's needed

### Success checks

- [ ] Presign-put returns a working S3 upload URL
- [ ] File visible in S3 console after upload
- [ ] Presign-get returns a working download URL
- [ ] `artifact_uri` in DB points to `s3://bucket/key`
- [ ] API never touches the file bytes — client uploads directly to S3

### Resources

| Type | Resource |
|------|----------|
| Docs | [boto3 S3 — generate_presigned_url](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-presigned-urls.html) |
| Docs | [AWS S3 Developer Guide](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html) |
| Docs | [AWS IAM Getting Started](https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html) |
| Video | [S3 Explained — Be A Better Dev](https://www.youtube.com/watch?v=e4T7nL3B9X0) |
| Video | [IAM Explained — Be A Better Dev](https://www.youtube.com/watch?v=KngM5bfpttA) |

---

## Layer 7 — Tiny Inference Container

**Goal:** Understand what an inference service actually is.

**Mini-project:** `inference-service/` (separate project, references registry from Layer 6)

### What to build

A standalone FastAPI service that loads a model artifact and serves predictions.

### Files

| File | Contents |
|------|----------|
| `app.py` | FastAPI app with `POST /predict` and `GET /health` |
| `model_loader.py` | Loads artifact from local file at startup |
| `model.json` | Dummy "model" artifact (e.g., `{"weights": [0.1, 0.5, 0.3]}`) |
| `Dockerfile` | Builds inference image |
| `requirements.txt` | `fastapi`, `uvicorn` |

### Behavior

- On startup: load `model.json` into memory
- `POST /predict` with body `{"input": [1, 2, 3]}` → applies dummy logic using weights → returns `{"prediction": <result>}`
- `GET /health` → `{"status": "healthy", "model_loaded": true}`

### Steps

1. Create `inference-service/` folder
2. Write `model.json` — your fake model artifact
3. Write `model_loader.py` — reads JSON, holds weights in memory
4. Write `app.py` — loads model on startup via lifespan, serves `/predict`
5. Write `Dockerfile`
6. Build: `docker build -t inference:dev .`
7. Run: `docker run -p 8001:8000 inference:dev`
8. Test: `curl -X POST http://localhost:8001/predict -H "Content-Type: application/json" -d '{"input":[1,2,3]}'`

### Success checks

- [ ] Container builds successfully
- [ ] `/health` returns model loaded status
- [ ] `/predict` returns a response based on the artifact
- [ ] Change `model.json`, rebuild — predictions change

### Resources

| Type | Resource |
|------|----------|
| Docs | [FastAPI — Lifespan Events](https://fastapi.tiangolo.com/advanced/events/) |
| Docs | [Dockerfile best practices](https://docs.docker.com/build/building/best-practices/) |

---

## Layer 8 — Push to ECR

**Goal:** Learn container registries — the bridge between local Docker and cloud deployment.

**Mini-project:** `ecr-push-demo/` (uses inference image from Layer 7)

### What to do

No new code — this is an operations layer.

### Steps

1. Create ECR repo:
   ```
   aws ecr create-repository --repository-name inference-service
   ```
2. Login to ECR:
   ```
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account_id>.dkr.ecr.us-east-1.amazonaws.com
   ```
3. Tag image:
   ```
   docker tag inference:dev <account_id>.dkr.ecr.us-east-1.amazonaws.com/inference-service:v1
   ```
4. Push:
   ```
   docker push <account_id>.dkr.ecr.us-east-1.amazonaws.com/inference-service:v1
   ```
5. Verify in AWS Console — image appears in ECR
6. Pull it back: `docker pull <uri>:v1` — confirm it runs

### Optional addition to registry

Add `image_uri` column to `DeploymentRecord` (or `VersionRecord`) — stores the ECR URI.

### Success checks

- [ ] ECR repo exists in AWS Console
- [ ] Image visible with tag `v1`
- [ ] Can pull and run image from ECR on another machine (or after deleting local)

### Resources

| Type | Resource |
|------|----------|
| Docs | [ECR User Guide](https://docs.aws.amazon.com/AmazonECR/latest/userguide/getting-started-cli.html) |
| Video | [ECR Walkthrough](https://www.youtube.com/watch?v=6I9X9fR3F9Y) |

---

## Layer 9 — Local Orchestrator (Deploy via Docker)

**Goal:** Learn orchestration logic before touching AWS ECS.

**Mini-project:** `orchestrator-local/` (new endpoints added to your registry from Layer 6)

### What changes

| Change | Detail |
|--------|--------|
| Add | `DeploymentRecord` ORM model (`id`, `model_id`, `version_id`, `status`, `endpoint_url`, `created_at`) |
| Add | `orchestrator.py` — starts/stops containers via `subprocess` or `docker` Python SDK |
| Add | `POST /deployments` and `GET /deployments/{id}` endpoints |
| Add | Alembic migration for deployments table |

### POST /deployments behavior

1. Create deployment row with `status=pending`
2. Determine image + port
3. Run `docker run -d -p <port>:8000 inference:dev`
4. Wait for `/health` to return OK
5. Update row: `status=healthy`, `endpoint_url=http://localhost:<port>`
6. Return deployment record

### Steps

1. Add `DeploymentRecord` to `models.py`
2. Generate Alembic migration
3. Write `orchestrator.py` — wraps `docker run` / `docker stop`
4. Add deployment endpoints to `main.py`
5. Test: `POST /deployments` → container starts → hit `/predict` on returned URL

### Success checks

- [ ] `POST /deployments` starts a container and returns endpoint URL
- [ ] `GET /deployments/{id}` shows status and URL
- [ ] `/predict` works on the deployed container
- [ ] You can deploy multiple versions on different ports

### Resources

| Type | Resource |
|------|----------|
| Docs | [Docker SDK for Python](https://docker-py.readthedocs.io/en/stable/) |

---

## Layer 10 — ECS Deployment (Real Cloud Cluster)

**Goal:** Move orchestration from local Docker to AWS ECS Fargate.

**Mini-project:** `ecs-deploy/` (replace Layer 9 orchestrator backend)

### What changes

| Change | Detail |
|--------|--------|
| Replace | `orchestrator.py` local Docker calls → `orchestrator_ecs.py` with boto3 ECS calls |
| Add | ECS cluster, task definition, service, ALB — created manually first |

### Architecture

```
POST /deployments
  → orchestrator_ecs.register_task_definition(image_uri)
  → orchestrator_ecs.create_or_update_service(task_def)
  → wait for health check
  → return ALB endpoint URL
```

### Manual setup (do this in AWS Console first)

1. Create ECS cluster (Fargate)
2. Create a task definition referencing your ECR image
3. Create a service with a load balancer (ALB)
4. Confirm `/predict` works via ALB URL
5. **Then** automate steps 2-3 via boto3

### Key concepts

| Concept | What it means |
|---------|--------------|
| Cluster | Logical grouping of services |
| Task Definition | "Recipe" for a container (image, CPU, memory, ports, env vars) |
| Service | Keeps N copies of a task running |
| Fargate | AWS manages the servers — you just define containers |
| ALB | Routes traffic to healthy containers |

### Success checks

- [ ] Inference container running on ECS (visible in Console)
- [ ] Public ALB URL returns `/health` OK
- [ ] `POST /predict` works through ALB
- [ ] `POST /deployments` in your registry triggers ECS update via boto3
- [ ] Registry stores the ALB endpoint URL

### Resources

| Type | Resource |
|------|----------|
| Docs | [ECS Developer Guide](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/Welcome.html) |
| Docs | [ECS + Fargate Getting Started](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/getting-started-fargate.html) |
| Video | [ECS + Fargate Explained — Be A Better Dev](https://www.youtube.com/watch?v=QwL2cSsm2x0) |
| Video | [ECS Deep Dive — Stephane Maarek](https://www.youtube.com/watch?v=z9H5bYhLk60) |

---

## Layer 11 — GitHub Actions CI/CD

**Goal:** Automate the entire build → test → push → register → deploy pipeline.

**Mini-project:** `.github/workflows/deploy.yml` (added to your main repo)

### Pipeline stages

```
on push to main or tag:
  1. Run pytest
  2. Build inference Docker image
  3. Push to ECR
  4. Call registry API: create model version with image_uri
  5. (Optional) Call POST /deployments to trigger ECS update
```

### Steps

1. Create `.github/workflows/deploy.yml`
2. Add GitHub secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `REGISTRY_API_URL`
3. Write each pipeline step
4. Push to GitHub — watch Actions tab
5. Verify: new ECR image + new version in registry

### Success checks

- [ ] Push to `main` triggers workflow
- [ ] Tests pass in CI
- [ ] New image appears in ECR
- [ ] Registry has new version entry with correct `image_uri`
- [ ] (Optional) ECS service updates automatically

### Resources

| Type | Resource |
|------|----------|
| Docs | [GitHub Actions Docs](https://docs.github.com/en/actions) |
| Docs | [GitHub Actions — AWS ECR Login Action](https://github.com/aws-actions/amazon-ecr-login) |
| Video | [GitHub Actions Full Course — TechWorld with Nana](https://www.youtube.com/watch?v=R8_veQiYBjI) |

---

## Layer 12 — Terraform (Infrastructure as Code)

**Goal:** Make all your AWS infrastructure reproducible with one command.

**Mini-project:** `infra/` folder in your repo

### What to codify

| Resource | Terraform resource |
|----------|-------------------|
| S3 bucket | `aws_s3_bucket` |
| KMS key | `aws_kms_key` |
| ECR repo | `aws_ecr_repository` |
| ECS cluster | `aws_ecs_cluster` |
| ECS service | `aws_ecs_service` |
| Task definition | `aws_ecs_task_definition` |
| ALB | `aws_lb` + `aws_lb_target_group` + `aws_lb_listener` |
| IAM roles | `aws_iam_role` + `aws_iam_policy` |
| Security groups | `aws_security_group` |

### Steps

1. Install Terraform
2. Create `infra/main.tf`, `infra/variables.tf`, `infra/outputs.tf`
3. Start with just S3 + ECR (simplest)
4. `terraform init && terraform plan && terraform apply`
5. Incrementally add ECS, IAM, ALB
6. Tear down with `terraform destroy` — confirm everything is removed
7. Re-apply — confirm everything recreates identically

### Success checks

- [ ] `terraform apply` creates all resources
- [ ] `terraform destroy` removes them cleanly
- [ ] `terraform apply` again — identical infrastructure
- [ ] Your app works on the Terraform-provisioned infra

### Resources

| Type | Resource |
|------|----------|
| Docs | [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs) |
| Docs | [Terraform Getting Started](https://developer.hashicorp.com/terraform/tutorials/aws-get-started) |
| Video | [Terraform Full Course — TechWorld with Nana](https://www.youtube.com/watch?v=SLB_c_ayRMo) |

---

## Layer 13 — Production Hardening

**Goal:** Make the system observable, secure, and resilient.

### Monitoring

| Tool | Purpose |
|------|---------|
| CloudWatch | ECS container logs + metrics |
| Prometheus + Grafana | Custom metrics (request latency, prediction count) |
| Health checks | ALB health checks on `/health` |

### Security

| Concern | Solution |
|---------|---------|
| Encryption at rest | KMS for S3, encrypted ECS volumes |
| Network isolation | Private subnets for ECS, ALB in public subnet |
| Access control | Security groups, IAM least privilege |
| Secrets | AWS Secrets Manager or Parameter Store (not .env files) |

### Deployment strategies

| Strategy | How |
|----------|-----|
| Blue/Green | Two target groups, weighted routing |
| Rollback | Keep previous task definition, revert service |
| Canary | 10% traffic to new version, monitor, then shift |

### Resources

| Type | Resource |
|------|----------|
| Docs | [CloudWatch Container Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/ContainerInsights.html) |
| Docs | [AWS Well-Architected — Security Pillar](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html) |
| Video | [AWS Monitoring — Be A Better Dev](https://www.youtube.com/watch?v=a4dsnMLbEa8) |

---

## Capstone Demo

When you finish Layer 10, you can demo the full pipeline:

1. `POST /models` — register model metadata
2. `POST .../presign-put` — get S3 upload URL
3. `curl -X PUT <url> --data-binary @model.pt` — upload artifact
4. `POST /models/{id}/versions` — register version with `artifact_uri`
5. `POST /deployments` — triggers ECS deployment
6. `POST <alb_url>/predict` — hit live inference endpoint

That's the full ML platform loop: **register → store → deploy → serve**.

---

## How This Maps to Your Real Project

| Layers | What it covers |
|--------|---------------|
| 0–4 | FastAPI + Postgres service (what you already built) |
| 5–6 | S3 artifact storage |
| 7–8 | Containerization + ECR |
| 9–10 | Orchestrator + inference cluster |
| 11 | GitHub Actions automation |
| 12 | Terraform infrastructure as code |
| 13 | Production hardening |

## Skills You'll Have at the End

- Backend systems architecture
- DevOps automation
- Container orchestration
- Cloud infrastructure
- CI/CD pipelines
- Secure production deployments
- ML lifecycle engineering

**This is ML Platform Engineering territory.**
