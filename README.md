---
title: Futurisys API
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# Futurisys — ML Model API

This project deploys a machine learning model in production. The model predicts the risk of an
employee leaving the company (attrition), and was trained in a previous project.

To deploy it, the project provides:
- a **FastAPI** API to expose the model
- a **PostgreSQL** database holding the dataset and a full trace of every exchange with the model
- **unit tests** with Pytest to guarantee reliability
- **Git / GitHub Actions** for version control and continuous integration

## Table of contents
- [How it works](#how-it-works)
- [Project structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [API reference](#api-reference)
- [Testing](#testing)
- [Deployment](#deployment)
- [Security](#security)
- [Authentication](#authentication)
- [Git conventions](#git-conventions)
- [Author](#author)

## How it works

Every call to the model goes through the database, so nothing is lost:

```
                        ┌──────────────── PostgreSQL ─────────────────┐
 3 CSV files ─import──> │ employee / evaluation / sondage   (dataset) │
                        │                                             │
 Client ──> FastAPI ──> │ prediction_input  ──> model ──>             │
                        │ prediction_output <──────────     (history) │
                        │ model_version                               │
                        └─────────────────────────────────────────────┘
```

- The API receives **raw employee data only** (27 fields). The 10 engineered features
  (`taux_promotion`, `zone_distance`, …) are computed by `modele/features.py`, using the exact
  formulas from the training notebook. This prevents training/serving skew.
- The raw input and the model's answer are written to two dedicated tables in a single
  transaction, together with the model version used.
- The database schema is documented in [docs/db_schema.md](docs/db_schema.md).

## Project structure

```
app/          the API only
  main.py         FastAPI application + routes (/, /health, /predict)
  schemas.py      API input/output validation (Pydantic)
  service.py      the database -> model -> database sequence
  dependencies.py one database session per request
modele/       the model
  pred.py         loads modele_attrition.joblib and runs predire()
  features.py     the 10 engineered features (same formulas as training)
db/           the database (see docs/db_schema.md)
  models.py       the 6 tables (SQLAlchemy)
  database.py     connection, reads DATABASE_URL from .env
  create_db.py    creates the database, the tables and the model version
  import_csv.py   imports the 3 dataset CSV files
  predictions.py  writes predictions (input + output)
  setup_postgres.sh  installs/starts PostgreSQL and creates the database user
  verify.sql      read-only SQL checks
data/         the 3 CSV files + the training notebook (not in git: HR data)
docs/         database schema and technical choices
tests/        64 tests (pytest)
```

## Prerequisites

- Ubuntu / WSL, Python 3.11+, git
- PostgreSQL 16 (installed by `db/setup_postgres.sh`)
- the 3 dataset files in `data/`: `extrait_sirh.csv`, `extrait_eval.csv`, `extrait_sondage.csv`
  (not in git, because they contain HR data)

## Installation

1. Clone the repository.

2. Create the Python environment:

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

3. Configure the database connection. Copy the template (do not rename it), then replace
   `changeme` with your own password, using letters and digits only:

```bash
cp .env.example .env
```

4. Install PostgreSQL, start it, and create the user declared in `.env`
   (asks for your Linux `sudo` password):

```bash
bash db/setup_postgres.sh
```

## Usage

Run these from the project root, in this order:

```bash
venv/bin/python -m db.create_db      # database + 6 tables + model version
venv/bin/python -m db.import_csv     # dataset: 1470 rows x 3 tables
venv/bin/uvicorn app.main:app --port 7861
```

Then open http://127.0.0.1:7861/docs to call `/predict` from the browser.

Check the database at any time (read-only):

```bash
psql "$(grep ^DATABASE_URL .env | cut -d= -f2- | sed 's/+psycopg//')" -f db/verify.sql
```

Useful options:

| Command | Effect |
|---|---|
| `venv/bin/python -m db.create_db` | safe to re-run; creates only what is missing |
| `venv/bin/python -m db.create_db --reset` | drops and recreates all tables (deletes everything) |
| `venv/bin/python -m db.import_csv` | refuses to run if data is already loaded |
| `venv/bin/python -m db.import_csv --replace` | reloads the dataset, keeps the prediction history |

After a Windows or WSL restart, PostgreSQL is stopped. Start it again with:

```bash
sudo service postgresql start
```

## API reference

| Route | Method | Description |
|---|---|---|
| `/` | GET | welcome message |
| `/health` | GET | returns `{"status": "ok"}`; works without a database |
| `/docs` | GET | interactive documentation (Swagger) |
| `/predict` | POST | prediction for one employee, recorded in the database |

`/predict` expects the 27 raw fields (see the example in `/docs`) and returns:

```json
{
  "id_prediction": 1,
  "probabilite_depart": 0.031,
  "seuil": 0.294,
  "prediction": 0,
  "label": "Reste probable"
}
```

`id_prediction` is the `prediction_input.id_input` of the saved row, so any answer can be traced
back in the database:

```sql
SELECT i.*, o.status, o.probabilite_depart, o.prediction, m.seuil
FROM prediction_input i
JOIN prediction_output o USING (id_input)
JOIN model_version m USING (id_model_version)
WHERE i.id_input = 1;
```

Response codes:

| Code | When | Saved in the database |
|---|---|---|
| 200 | success | input + output with `status='success'` |
| 422 | invalid data, or an engineered feature was sent | nothing: the model is never called |
| 500 | the model failed | input + output with `status='error'` and the message |
| 503 | the database is unavailable or not configured | nothing: no prediction without traceability |

## Testing

The tests need no PostgreSQL: they run against a throwaway in-memory SQLite database, which is
why they also work in GitHub Actions.

```bash
venv/bin/python -m pytest -q
venv/bin/python -m pytest --cov=app --cov=db --cov=modele --cov-report=term
```

Current state: **64 tests, 86% coverage**.

| File | What it tests |
|---|---|
| `tests/test_schemas.py` | API input validation (Pydantic) |
| `tests/test_features.py` | the engineered feature formulas |
| `tests/test_pred.py` | model loading and the decision threshold |
| `tests/test_db_models.py` | the table constraints |
| `tests/test_create_db.py` | table creation and the model version |
| `tests/test_import_csv.py` | the dataset import (conversions, all-or-nothing) |
| `tests/test_api.py` | the routes and the traceability in the database |

`tests/conftest.py` swaps the real database for the test one by overriding the `get_session`
dependency of FastAPI.

## Deployment

### Continuous integration and delivery

`.github/workflows/CI_CD.yml` runs on every push and pull request to `main` and `develop`:

| Job | What it does |
|---|---|
| `build_job` | installs the dependencies on Python 3.11 |
| `test_job` | runs the whole test suite with coverage |
| `deploy_job` | pushes the repository to the Hugging Face Space, only on a push to `main` |

The deploy job uses the official `huggingface/hub-sync` action and needs an `HF_TOKEN` secret in
the GitHub repository settings.

### The API on Hugging Face

The Space [anchaekim/futurisys](https://huggingface.co/spaces/anchaekim/futurisys) runs the
`Dockerfile`, which serves the API on port 7860.

### The database stays local (by design)

The project brief allows the database to be local only, and that is the choice made here: the
PostgreSQL database runs on the developer's machine and is never exposed to the internet.

Consequences on the deployed Space:

| Route on the Space | Behaviour |
|---|---|
| `/`, `/health`, `/docs` | work normally |
| `/predict` | returns **503** with `"Base de données non configurée (DATABASE_URL manquante)"` |

This is intentional, not a bug. The API refuses to predict when it cannot record the exchange,
because full traceability is a requirement of the project. The Space therefore demonstrates the
deployment chain (Docker, CI/CD, hosting), while the complete pipeline — dataset, predictions and
their history — runs locally.

Why the database is not hosted online:
- the data is **personal HR data** (salary, age, marital status), which is subject to the GDPR and
  should not be copied to a free third-party service;
- a Space's disk is **not persistent**, so a database stored inside it would be wiped on every
  restart;
- the brief requires PostgreSQL locally, not a hosted database.

To run the full pipeline, follow [Installation](#installation) and [Usage](#usage) locally. If the
database ever needs to be reachable from the Space, the only change required is to provide a
`DATABASE_URL` secret in the Space settings; no code change is needed.

## Security

- **No password in the code or in git.** The connection string lives in `.env`, which is listed in
  `.gitignore` and `.dockerignore`. `.env.example` is the committed template and contains only a
  fake password.
- **No HR data in git or in the Docker image.** `data/` (the CSV files and the training notebook)
  is excluded from both.
- **A dedicated PostgreSQL user** (`futurisys`) is used instead of the `postgres` superuser.
- **The database validates every write** with `CHECK`, `NOT NULL`, `UNIQUE` and foreign key
  constraints, so invalid data cannot be stored even by a script that bypasses the API.
- **The database is not exposed** to the network: it listens on `localhost` only.
- **Errors are recorded, not hidden:** a model failure is stored with `status='error'`.

## Authentication

There is none yet: `/predict` is open to anyone who can reach the API. This is acceptable while the
database is local and the endpoint is unreachable from the internet. If the endpoint were ever
opened to real users, an API key or OAuth would be required, since the requests carry personal data.

## Git conventions

- `main`: stable branch, the only one that triggers deployment.
- `develop`: integration branch for ongoing work.
- Feature branches (e.g. `feat/HF`) are merged into `develop` through pull requests, so the tests
  run before the merge.
- Remotes: `github` (source code, CI/CD) and `origin` (the Hugging Face Space).
- Commit messages state what changed, e.g. `Pydantic classes for types in the Employee Base Model`.

## Author

Andrea Kim — OpenClassrooms project 5 (deploying a model in production).
