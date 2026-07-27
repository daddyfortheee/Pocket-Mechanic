from pathlib import Path
import re
import time

html_path = Path("static/index.html")
js_path = Path("static/app.js")

html = html_path.read_text()
js = js_path.read_text()

# ---------------------------------------------------------
# 1. Give the visible diagnosis-page elements reliable IDs.
# ---------------------------------------------------------

# Page title: Quick Diagnosis
html, count = re.subn(
    r'(<h1)([^>]*)(>\s*Quick Diagnosis\s*</h1>)',
    r'\1 id="diagnosisPageTitle"\2\3',
    html,
    count=1,
    flags=re.IGNORECASE
)

if count == 0 and 'id="diagnosisPageTitle"' not in html:
    raise RuntimeError("Could not find the Quick Diagnosis heading.")

# Question label: What is it doing?
html, count = re.subn(
    r'<label>\s*What is it doing\?\s*</label>',
    '<label id="symptomLabel" for="symptom">What is it doing?</label>',
    html,
    count=1,
    flags=re.IGNORECASE
)

if count == 0 and 'id="symptomLabel"' not in html:
    raise RuntimeError("Could not find the symptom label.")

# Ensure symptom textarea has the correct baseline placeholder.
html = re.sub(
    r'(<textarea[^>]*id=["\']symptom["\'][^>]*?)placeholder=["\'][^"\']*["\']',
    r'\1placeholder="Describe the exact symptom, when it happens, warning lights, noises, smells, and anything already tested."',
    html,
    count=1,
    flags=re.IGNORECASE
)

# Button text stays diagnostic by default.
html = re.sub(
    r'(<button[^>]*id=["\']diagnoseButton["\'][^>]*>).*?(</button>)',
    r'\1Run diagnosis\2',
    html,
    count=1,
    flags=re.IGNORECASE | re.DOTALL
)

# ---------------------------------------------------------
# 2. Add project-mode UI behavior to app.js.
# ---------------------------------------------------------

ui_code = r'''
function updateDiagnosisInterface() {
  const projectMode = isProjectMode();

  const title = $("#diagnosisPageTitle");
  const symptomLabel = $("#symptomLabel");
  const symptomInput = $("#symptom");
  const diagnoseButton = $("#diagnoseButton");

  if (projectMode) {
    if (title) title.textContent = "Project Planner";

    if (symptomLabel) {
      symptomLabel.textContent = "What are you building or repairing?";
    }

    if (symptomInput) {
      symptomInput.placeholder =
        "Describe the project, room or work area, measurements, materials you already have, desired result, budget, and any photos or videos.";
    }

    if (diagnoseButton) {
      diagnoseButton.textContent = "Build project plan";
    }
  } else {
    if (title) title.textContent = "Quick Diagnosis";

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
  }
}
'''

if "function updateDiagnosisInterface()" not in js:
    is_project_match = re.search(
        r'function\s+isProjectMode\s*\(\)\s*\{.*?\n\}',
        js,
        flags=re.DOTALL
    )

    if is_project_match:
        insert_at = is_project_match.end()
        js = js[:insert_at] + "\n\n" + ui_code + js[insert_at:]
    else:
        raise RuntimeError("Could not find isProjectMode() in static/app.js.")

# Add category change listener.
if '"#category").addEventListener("change", updateDiagnosisInterface)' not in js:
    listener_code = r'''
const categorySelector = $("#category");

if (categorySelector) {
  categorySelector.addEventListener("change", updateDiagnosisInterface);
}

updateDiagnosisInterface();
'''

    form_marker = re.search(
        r'\$\(["\']#diagnosisForm["\']\)\.addEventListener\(["\']submit["\']',
        js
    )

    if form_marker:
        js = js[:form_marker.start()] + listener_code + "\n" + js[form_marker.start():]
    else:
        js += "\n" + listener_code

# ---------------------------------------------------------
# 3. Force browsers to load the new app.js.
# ---------------------------------------------------------

version = int(time.time())

html, changed = re.subn(
    r'(<script[^>]+src=["\']/static/app\.js)(?:\?v=[^"\']*)?(["\'])',
    rf'\1?v={version}\2',
    html,
    count=1,
    flags=re.IGNORECASE
)

if changed == 0:
    raise RuntimeError("Could not find the /static/app.js script tag.")

html_path.write_text(html)
js_path.write_text(js)

print("SUCCESS: Project Planner UI added.")
print(f"Cache version: {version}")
