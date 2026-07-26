# Pocket Mechanic — Project Atlas 0.4

Termux-hosted FastAPI repair dashboard with Quick Diagnosis, My Garage, OBD-II starter lookup, Repair Library, and local history.

## Run

```bash
cd ~/Pocket-Mechanic
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Open `http://127.0.0.1:8080/?v=4`.
