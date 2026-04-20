# Restaurant-BACED

Restaurant-BACED is a data-driven restaurant inventory and order management system. The project combines a Streamlit front end, a Flask REST API, and a MySQL database to support restaurant workflows such as order handling, menu and inventory management, and operations reporting.

## Project Overview

The application is organized around three layers:

- `app/` - the Streamlit UI
- `api/` - the Flask REST API
- `database-files/` - SQL scripts used to initialize the MySQL database

The docker-compose setup, defined in `docker-compose.yaml` starts three services:

- `app` on `http://localhost:8501`
- `api` on `http://localhost:4000`
- `db` exposed on MySQL port `3200`

## Getting Started

### Prerequisites

- Docker
- A copy of `api/.env` based on `api/.env.template`

### Setup

From the repository root:

```bash
cp api/.env.template api/.env
```

Set `MYSQL_ROOT_PASSWORD` `api/.env` to a strong password.

From the repository root, start the full stack:

```bash
docker compose up # run in foreground
docker compose up -d # run in background
```

That command builds the images if needed and starts the app, API, and database containers in the background.

To stop and remove the containers:

```bash
docker compose down
```

## Team Members

- Darshan Balaji
- Evan Blankenship
- Aditya Kompella
- Bianca Sellemi
- Cade Walkush

## Demo Video

Coming soon