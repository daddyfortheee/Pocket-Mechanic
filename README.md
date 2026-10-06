# Pocket Guru

FastAPI repair and DIY guide with photo inspection, diagnosis, My Garage, OBD-II starter lookup, Repair Library, and local history.

## Run

```bash
cd ~/Pocket-Mechanic
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Open `http://127.0.0.1:8080/`.

Photo inspection requires `OPENAI_API_KEY` in the server environment. Garage items and repair history are stored locally in the browser.

## Reliability checks

Install `requirements-dev.txt`, then run `python -m pytest -q`. Frontend checks use Node 22 and `jsdom@26.1.0`: run every `tests/frontend_*.cjs` with `NODE_PATH` pointing to the jsdom installation. CI runs backend/frontend tests and a dependency vulnerability audit on pushes, PRs and daily.

The app is currently a beta. Read [the launch-readiness audit](docs/launch-readiness.md) before offering subscriptions. Verified accounts, cloud sync and billing remain release gates. Private guest API records are temporary and scoped to signed browser sessions; keep local garage/history backups from the History page.
