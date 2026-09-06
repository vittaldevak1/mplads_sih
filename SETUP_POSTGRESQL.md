# PostgreSQL Installation Guide for MPLADS Platform

## Option 1: Manual Installation

1. Download PostgreSQL 16 from: https://www.postgresql.org/download/windows/
2. Run the installer
3. Set password for postgres user (use: postgres)
4. Keep default port: 5432
5. Complete installation

## Option 2: Docker (Recommended)

```bash
docker run -d \
  --name mplads-postgres \
  -e POSTGRES_DB=mplads \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  postgres:16-alpine
```

## After Installation

1. Create the database:
```sql
psql -U postgres -c "CREATE DATABASE mplads;"
```

2. Run the schema:
```bash
psql -U postgres -d mplads -f docker/init.sql
```

3. Install Python dependencies:
```bash
cd backend
pip install -r requirements.txt
```

4. Run data ingestion:
```bash
python scripts/import_data.py
```

5. Start the backend:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Verify Installation

```bash
# Check PostgreSQL is running
psql -U postgres -c "\l"

# Check tables created
psql -U postgres -d mplads -c "\dt"
```
