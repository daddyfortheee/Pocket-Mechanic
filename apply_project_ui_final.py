from pathlib import Path
import re
import time

html_path = Path("static/index.html")
js_path = Path("static/app.js")

html = html_path.read_text()
js = js_path.read_text()

# =========================================================
# 1. UPDATE THE HTML USING THE EXACT CURRENT STRUCTURE
# =========================================================

old_title = '<h1 id="assistTitle">Quick Diagnosis</h1>'
new_title = '<h1 id="assistTitle">Quick Diagnosis</h1>'

if old_title not in html:
    raise RuntimeError("Could not find assistTitle.")
html = html.replace(old_title, new_title, 1)

old_label = '<label>What is it doing?'
new_label = '<label><span id="symptomLabel">What is it doing?</span>'

if old_label not in html and 'id="symptomLabel"' not in html:
    raise RuntimeError("Could not find symptom label.")
if old_label in html:
    html = html.replace(old_label, new_label, 1)

old_button = '<button id="diagnoseButton" class="primary" type="submit">Run diagnosis</button>'
new_button = '<button id="diagnoseButton" class="primary" type="submit">Run diagnosis</button>'

if old_button not in html:
    raise RuntimeError("Could not find diagnoseButton.")

# Add a project-specific helper paragraph under the textarea.
textarea_end = '</textarea>\n      </label>'

project_help = '''</textarea>
        <small id="projectHelp" class="muted hidden">
          Include measurements, materials you already have, the desired result,
          budget, tools available, and any restrictions.
        </small>
      </label>'''

if 'id="projectHelp"' not in html:
    if textarea_end not in html:
        raise RuntimeError("Could not find symptom textarea closing section.")
    html = html.replace(textarea_end, project_help, 1)

# Cache-bust app.js.
version = int(time.time())

html, count = re.subn(
    r'/static/app\.js(?:\?v=[^"\']*)?',
    f'/static/app.js?v={version}',
    html,
    count=1
)

if count == 0:
    raise RuntimeError("Could not find app.js script tag.")

# =========================================================
# 2. ADD THE LIVE UI MODE SWITCHER TO app.js
# =========================================================

ui_function = r'''
function updateDiagnosisInterface() {
  const projectMode = isProjectMode();

  const title = $("#assistTitle");
  const symptomLabel = $("#symptomLabel");
  const symptomInput = $("#symptom");
  const diagnoseButton = $("#diagnoseButton");
  const projectHelp = $("#projectHelp");
  const mediaHeading = document.querySelector(".media-heading h2");
  const mediaHelp = document.querySelector(".media-help");

  if (projectMode) {
    if (title) {
      title.textContent = "Project Planner";
    }

    if (symptomLabel) {
      symptomLabel.textContent = "What are you building or repairing?";
    }

    if (symptomInput) {
      symptomInput.placeholder =
        "Describe the project, work area, measurements, materials you already have, desired result, budget, and tools available.";
    }

    if (diagnoseButton) {
      diagnoseButton.textContent = "Build project plan";
    }

    if (projectHelp) {
      projectHelp.classList.remove("hidden");
    }

    if (mediaHeading) {
      mediaHeading.textContent = "Add project photos or video";
    }

    if (mediaHelp) {
      mediaHelp.textContent =
        "Add clear photos of the work area, measurements, existing materials, damage, layout, or the result you want to recreate.";
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

    if (projectHelp) {
      projectHelp.classList.add("hidden");
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
    match = re.search(
        r'function\s+isProjectMode\s*\(\)\s*\{.*?\n\}',
        js,
        flags=re.DOTALL
    )

    if not match:
        raise RuntimeError("Could not find isProjectMode() in app.js.")

    insert_at = match.end()
    js = js[:insert_at] + "\n\n" + ui_function + js[insert_at:]

listener_code = r'''
const categorySelector = $("#category");

if (categorySelector) {
  categorySelector.addEventListener("change", updateDiagnosisInterface);
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

print("SUCCESS: Project Planner interface installed.")
print(f"Browser cache version: {version}")
