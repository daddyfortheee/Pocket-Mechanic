# Pocket Guru

FastAPI repair and DIY guide with photo inspection, diagnosis, My Garage, OBD-II starter lookup, Repair Library, and local history.

## Run

```bash
cd ~/Pocket-Mechanic
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Open `http://127.0.0.1:8080/?v=11`.

Photo inspection requires `OPENAI_API_KEY` in the server environment. Garage items and repair history are stored locally in the browser.
