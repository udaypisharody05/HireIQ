# HireIQ

AI-powered placement preparation platform with LeetCode tracking, resume analysis, and mock interviews.

This repository is a production-oriented monorepo scaffold. It includes a Next.js frontend, FastAPI backend, PostgreSQL database, and Docker Compose setup for local development.

## Repository Structure

```text
HireIQ/
  frontend/          Next.js + TypeScript + Tailwind CSS
  backend/           FastAPI application
  docker-compose.yml Local development services
  .env.example       Environment variable template
```

## Prerequisites

- Docker and Docker Compose
- Node.js 20+ for running the frontend outside Docker
- Python 3.12+ for running the backend outside Docker

## Quick Start With Docker

1. Create a local environment file:

   ```bash
   cp .env.example .env
   ```

2. Start all services:

   ```bash
   docker compose up --build
   ```

3. Open the apps:

   - Frontend: http://localhost:3000
   - Backend health check: http://localhost:8000/health
   - API docs: http://localhost:8000/docs
   - PostgreSQL: localhost:5432

## Local Development Without Docker

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

On Windows PowerShell, activate the virtual environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

Copy `.env.example` to `.env` for Docker Compose. The frontend and backend both include sensible local defaults, but `.env` should be used for local overrides.

## Available Endpoints

- `GET /health` - Returns backend health status.
- `GET /catalog/status` - Returns global LeetCode catalog size and refresh status.

## Global LeetCode Catalog

Apply migrations, then run the idempotent catalog import:

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.commands.sync_catalog
```

Run the catalog command weekly from cron or the deployment scheduler. It imports free
problems from LeetCode's public GraphQL endpoint and does not require cookies.

## Current Scope

This scaffold intentionally does not include HireIQ business logic yet. It provides the application boundaries, local infrastructure, and placeholder pages needed for future development.
