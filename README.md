# CECILia API <img src="https://snipboard.io/rlh6gz.jpg" width="10%" align="right" valign="middle" alt="CECILia logo"/>

Service API from Sinal Business

<div align="center">

![version](https://img.shields.io/badge/version-2.0.0-red.svg)
![status](https://img.shields.io/badge/status-stable-006400.svg)
![python](https://img.shields.io/badge/Python-3.10-3776AB.svg?logo=python&logoColor=white)
![fastapi](https://img.shields.io/badge/FastAPI-API-009688.svg?logo=fastapi&logoColor=white)
![docker](https://img.shields.io/badge/Docker-ready-2496ED.svg?logo=docker&logoColor=white)
[![docs](https://img.shields.io/badge/docs-ReDoc-85EA2D.svg)](https://chat-gdatabot.onrender.com/docs)
![security](https://img.shields.io/badge/security-Bearer_token-important.svg)

</div>

<details>
  <summary><strong>[Open/Close] Table of Contents</strong></summary>

- [CECILia API ](#cecilia-api-)
  - [✨ About](#-about)
  - [🧰 Technology](#-technology)
  - [🏗️ Architecture](#️-architecture)
  - [🚀 Getting Started](#-getting-started)
    - [Requirements](#requirements)
    - [Local installation](#local-installation)
  - [🔐 Authentication](#-authentication)
  - [📡 Endpoints](#-endpoints)
    - [Service status](#service-status)
    - [Validate CPF or CNPJ](#validate-cpf-or-cnpj)
    - [Atualizar Cobrança de Cliente](#atualizar-cobrança-de-cliente)
  - [🐳 Docker](#-docker)
  - [⚙️ Environment Variables](#️-environment-variables)
  - [Render Deployment](#render-deployment)
  - [📁 Project Structure](#-project-structure)
  - [🛡️ Security](#️-security)

</details>

---

## ✨ About

The CECILia API is a FastAPI service used by the CECILia ecosystem. Version `2.0.0` currently provides:

- CPF validation, including format, length, repeated digits, and check digits.
- Numeric and alphanumeric CNPJ validation, including check digits.
- Bearer token authentication for protected routes.
- ReDoc and OpenAPI documentation.
- SQL Server connection support for data-backed services.
- Adm endpoint for BotConversa collection webhook updates.
- Containerized execution with Docker and Docker Compose.

## 🧰 Technology

| Technology | Purpose |
| --- | --- |
| Python 3.10 | Application runtime |
| FastAPI | HTTP API framework |
| Pydantic | Request and response validation |
| Uvicorn | ASGI server |
| PyODBC | SQL Server connectivity |
| Docker | Containerized deployment |
| OpenAPI / ReDoc | Interactive API documentation |

## 🏗️ Architecture

```text
Client
  |
  | Authorization: Bearer <TOKEN>
  v
FastAPI
  |
  +-- Routers
  |     +-- Health and documentation
  |     +-- Document validation
  |     +-- Adm collection webhook updates
  |
  +-- Services
  |     +-- CPF and CNPJ validation rules
  |
  +-- Core
        +-- Authentication
        +-- SQL Server connection
```

## 🚀 Getting Started

### Requirements

- Python `3.10+`
- ODBC Driver for SQL Server when database access is used
- Docker and Docker Compose, optionally

### Local installation

```bash
git clone https://github.com/Sinal-Business/cecilia-api.git
cd cecilia-api

python -m venv .venv
```

Activate the virtual environment:

```powershell
# Windows
.\.venv\Scripts\Activate.ps1
```

```bash
# Linux or macOS
source .venv/bin/activate
```

Install and run:

```bash
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The local service will be available at:

- API: `http://localhost:8000`
- ReDoc: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`
- OpenAPI YAML: `http://localhost:8000/openapi.yaml`

## 🔐 Authentication

Protected routes require the token configured in the `TOKEN` environment variable.

```http
Authorization: Bearer <TOKEN>
Content-Type: application/json
```

Never commit tokens, passwords, connection strings, or local environment files.

## 📡 Endpoints

### Service status

```http
GET /
```

Example response:

```json
{
  "status": "API on air"
}
```

### Validate CPF or CNPJ

```http
POST /validations/document
Authorization: Bearer <TOKEN>
Content-Type: application/json
```

CPF request:

```json
{
  "tipo": "cpf",
  "valor": "12345678909"
}
```

CNPJ request:

```json
{
  "tipo": "cnpj",
  "valor": "12345678000195"
}
```

Response format:

```json
{
  "valid_doc": true,
  "status": "CPF_VALID",
  "notes": "Obrigada 😊"
}
```

Possible status values:

| Document | Status |
| --- | --- |
| CPF | `CPF_VALID` |
| CPF | `CPF_INVALID_EMPTY` |
| CPF | `CPF_INVALID_FORMAT` |
| CPF | `CPF_INVALID_LENGTH` |
| CPF | `CPF_INVALID_DIGITS` |
| CNPJ | `CNPJ_VALID` |
| CNPJ | `CNPJ_INVALID_EMPTY` |
| CNPJ | `CNPJ_INVALID_FORMAT` |
| CNPJ | `CNPJ_INVALID_LENGTH` |
| CNPJ | `CNPJ_INVALID_DIGITS` |
| General | `DOCUMENT_INVALID_TYPE` |

### Atualizar Cobrança de Cliente

```http
PATCH /adm/client-charge
Authorization: Bearer <TOKEN>
Content-Type: application/json
```

Request:

```json
{
  "contato": "+5521999999999",
  "status": "Atual (Com Projeção)",
  "resposta": "Cliente informou previsão de pagamento.",
  "dt_projecao_pgto": "2026-06-30"
}
```

The endpoint filters `dbo.sinal_financeiro_hiscobranca` by `contato`, updates
all matching invoices, and only changes `status`, `resposta`, and
`dt_projecao_pgto`. `status` is required; `resposta` and `dt_projecao_pgto`
are optional. The received `contato` may include `+`, spaces, hyphens, or
parentheses; the API normalizes it to digits before matching the database.
`dt_cobranca` is filled automatically by the backend with the current
São Paulo date and time whenever the update is processed.

Response:

```json
{
  "ok": true,
  "updated_count": 1,
  "contato": "5521999999999"
}
```

## 🐳 Docker

Create a local `.env` file with the required variables, then run:

```bash
docker compose up --build
```

The API will be exposed at `http://localhost:8000`.

To stop the service:

```bash
docker compose down
```

## ⚙️ Environment Variables

| Variable | Required | Description |
| --- | --- | --- |
| `TOKEN` | Yes | Bearer token accepted by protected endpoints |
| `DATABASE_URL` | For database access | Full SQL Server ODBC connection string; preferred for Render |
| `SQL_SERVER_HOST` | Fallback database access | SQL Server hostname when `DATABASE_URL` is not set |
| `SQL_SERVER_DB` | Fallback database access | Database name when `DATABASE_URL` is not set |
| `SQL_SERVER_USER` | Fallback database access | Database user when `DATABASE_URL` is not set |
| `SQL_SERVER_PASSWORD` | Fallback database access | Database password when `DATABASE_URL` is not set |
| `PORT` | No | HTTP port used by the container; defaults to `8000` |

Example with placeholders only:

```dotenv
TOKEN=replace-with-a-strong-random-token
DATABASE_URL=Driver={ODBC Driver 18 for SQL Server};Server=tcp:your-server.database.windows.net,1433;Database=your-database;Uid=your-user;Pwd=your-password;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;
SQL_SERVER_HOST=your-server
SQL_SERVER_DB=your-database
SQL_SERVER_USER=your-user
SQL_SERVER_PASSWORD=your-password
PORT=8000
```

## Render Deployment

Deploy this service as a Docker Web Service, not as the native Python runtime.
The Docker image installs Microsoft's SQL Server ODBC driver, which is required
by `pyodbc` when `DATABASE_URL` uses `Driver={ODBC Driver 18 for SQL Server}`.

Recommended Render settings:

| Setting | Value |
| --- | --- |
| Runtime | Docker |
| Dockerfile Path | `./dockerfile` |
| Environment variables | `TOKEN`, `DATABASE_URL` |

If the service is deployed as Python instead of Docker, SQL Server routes can
fail with:

```text
Can't open lib 'ODBC Driver 18 for SQL Server' : file not found
```

## 📁 Project Structure

```text
cecilia-api/
├── core/                 # Authentication and database connection
├── routers/              # HTTP route definitions
├── schemas/              # Pydantic request and response models
├── services/             # Business and validation rules
├── docker-compose.yml    # Local container orchestration
├── dockerfile            # Container image definition
├── main.py               # FastAPI application entry point
├── openapi.yaml          # OpenAPI contract
└── requirements.txt      # Python dependencies
```

## 🛡️ Security

- Store production secrets only in the deployment platform's secret manager.
- Use a long, randomly generated token and rotate it periodically.
- Do not expose SQL Server directly to the public internet.
- Restrict database credentials to the minimum required permissions.
- Review dependency and container image updates before each release.
- Keep `openapi.yaml` synchronized with the FastAPI-generated contract.

---

<div align="center">
Developed for the <strong>CECILia</strong> ecosystem by Sinal Business
</div>
