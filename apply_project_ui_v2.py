from pathlib import Path
import re
import time

html_path = Path("static/index.html")
js_path = Path("static/app.js")

html = html_path.read_text()
js = js_path.read_text()

# ---------------------------------------------------------
# 1. Add an ID around the existing symptom label text.
# ---------------------------------------------------------

if 'id="symptomLabel"' not in html:
    html, count = re.subn(
        r'(<label[^>]*>)\s*What is it doing\?',
        r'\1<span id="symptomLabel">What is it doing?</span>',
        html,
        count=1,
        flags=re.IGNORECASE
    )

    if count == 0:
        raise RuntimeError("Could not locate 'What is it doing?'.")

# Confirm the existing title and button are present.
if 'id="assistTitle"' not in html:
    raise RuntimeError("Could not find assistTitle.")

if 'id="diagnoseButton"' not in html:
    raise RuntimeError("Could not find diagnoseButton.")

# ---------------------------------------------------------
# 2. Force browsers to load the updated JavaScript.
# ---------------------------------------------------------

version = int(time.time())

html, count = re.subn(
    r'/static/app\.js(?:\?v=[^"\']*)?',
    f'/static/app.js?v={version}',
    html,
    count=1
)

if count == 0:
    raise RuntimeError("Could not find the app.js script tag.")

# ---------------------------------------------------------
# 3. Add the visible Project Planner interface switcher.
# ---------------------------------------------------------

ui_code = r'''
function updateDiagnosisInterface() {
  const projectMode = isProjectMode();

  const title = $("#assistTitle");
  const symptomLabel = $("#symptomLabel");
  const symptomInput = $("#symptom");
  const diagnoseButton = $("#diagnoseButton");
  const mediaHeading = document.querySelector(
    "#page-diagnose .media-heading h2"
  );
  const mediaHelp = document.querySelector(
    "#page-diagnose .media-help"
  );

  if (projectMode) {
    if (title) {
      title.textContent = "Project Planner";
    }

    if (symptomLabel) {
      symptomLabel.textContent =
        "What are you building, installing, or repairing?";
    }

    if (symptomInput) {
      symptomInput.placeholder =
        "Describe the project, work area, measurements, materials you already have, desired result, budget, and tools available.";
    }

    if (diagnoseButton) {
      diagnoseButton.textContent = "Build project plan";
    }

    if (mediaHeading) {
      mediaHeading.textContent = "Add project photos or video";
    }

    if (mediaHelp) {
      mediaHelp.textContent =
        "Add clear photos or video of the work area, measurements, layout, existing materials, damage, or the result you want to recreate.";
    }
  } else {
    if (title) {
      title.textContent = "Quick Diagnosis";
    }

    if (symptomLabel) {
      symptomLabel.textContent = "What is it doing?";
    }

    if (symptomInput) {
      symptomInput.placeholder =
        "Describe the exact symptom, when it happens, warning lights, noises, smells, and anything already tested.";
    }

    if (diagnoseButton) {
      diagnoseButton.textContent = "Run diagnosis";
    }

    if (mediaHeading) {
      mediaHeading.textContent = "Add photos or video";
    }

    if (mediaHelp) {
      mediaHelp.textContent =
        "Add a clear picture of the full item, its brand logo, model-number label, damaged part, wiring, leak, or warning display. You may also add a short video showing the sound, movement, vibration, smoke, or flashing lights.";
    }
  }
}
'''

if "function updateDiagnosisInterface()" not in js:
    marker = '$("#cameraInput").addEventListener("change", event => {'

    if marker not in js:
        raise RuntimeError("Could not find the camera input listener.")

    js = js.replace(marker, ui_code + "\n" + marker, 1)

# ---------------------------------------------------------
# 4. Run the switcher whenever Category changes.
# ---------------------------------------------------------

listener_code = r'''
const categorySelector = $("#category");

if (categorySelector) {
  categorySelector.addEventListener(
    "change",
    updateDiagnosisInterface
  );
}

updateDiagnosisInterface();

'''

if "categorySelector.addEventListener" not in js:
    marker = '$("#diagnosisForm").addEventListener("submit", async event => {'

    if marker not in js:
        raise RuntimeError("Could not find diagnosis form submit listener.")

    js = js.replace(marker, listener_code + marker, 1)

html_path.write_text(html)
js_path.write_text(js)

print("SUCCESS: Dynamic Project Planner UI installed.")
print(f"Cache version: {version}")
