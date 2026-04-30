# Mesh — running locally

Mesh V1 is a FastAPI + MongoDB monolith. Python 3.12 or newer is required.

## 1. Install dependencies

```bash
pip install -e '.[dev]'
```

## 2. Set up MongoDB

Pick whichever fits — **V1 does not require Docker.**

**Easiest: MongoDB Atlas free tier (recommended).**
1. Create a free cluster at <https://www.mongodb.com/cloud/atlas/register>.
2. Add `0.0.0.0/0` to the network access list (or your IP) so your laptop can connect.
3. Create a database user and copy the connection string (it looks like `mongodb+srv://user:pass@cluster.xxx.mongodb.net/`).
4. Use that as your `MONGODB_URI` in step 3.

**Alternative: local mongod install.**
1. Install MongoDB 7+ for your OS (`brew install mongodb-community` on macOS, equivalent on Linux/Windows).
2. Start the daemon (`brew services start mongodb-community`, or `mongod --dbpath ...`).
3. Use `MONGODB_URI=mongodb://localhost:27017`.

**Alternative: docker-compose stack** (config provided, optional).
```bash
docker compose up -d
```
Then use `MONGODB_URI=mongodb://localhost:27017`.

## 3. Configure the environment

```bash
cp .env.example .env
```

Then edit `.env` and fill in:
- `MONGODB_URI` from step 2
- `JWT_SECRET` — generate with:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(48))"
  ```

## 4. Run the dev server

```bash
uvicorn app.main:app --reload --port 8000
```

Health check: <http://localhost:8000/health>

## 5. Run tests

```bash
pytest
```
