# Pocket Mechanic MVP 0.1

This is the first runnable software build from **Project Atlas**.

## What works

- PMOS-style diagnostic workflow
- Ranked likely causes with working confidence
- Safety classification and stop-work guidance
- Guided Repair Mode
- Saved vehicle/appliance/equipment profiles
- Diagnosis and repair history
- Browser local storage
- Installable Progressive Web App support
- Responsive phone and desktop interface

The included local diagnostic engine has example logic for:

- Vehicle speedometer/odometer/cruise-control failures
- Serpentine belt edge shredding
- Dryer heating/thermistor fault codes
- Small-engine no-start problems
- Home electrical hazards

Unknown symptoms fall back to a structured evidence-collection workflow.

## Run it

### Fastest method

Open `index.html` directly in a modern browser.

Most features work immediately. The install/offline feature requires a local web server.

### Recommended method

From this folder, run:

```bash
python -m http.server 8080
```

Then open:

```text
http://localhost:8080
```

On Android/Chrome, use the browser menu to install or add Pocket Mechanic to the home screen.

## Important limitation

This is a functional prototype, not a production diagnostic authority. It uses local rule-based logic and does not yet call a cloud AI model, verified repair database, VIN decoder, parts catalog, or authentication service.

## Next engineering sprint

1. Add FastAPI backend and PostgreSQL schema.
2. Add secure user authentication.
3. Connect PMOS orchestration to an AI service.
4. Add image upload and component identification.
5. Add equipment-specific service information retrieval.
6. Add technician-reviewed safety and repair content.
7. Add automated tests, analytics, and deployment pipeline.

## Structure

- `index.html` — application shell
- `styles.css` — responsive design system
- `app.js` — PMOS rules, state, diagnosis, repair mode
- `manifest.json` — PWA metadata
- `service-worker.js` — offline caching
- `PROJECT_ATLAS_BUILD_NOTES.md` — product and engineering notes
