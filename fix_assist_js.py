from pathlib import Path

path = Path("static/app.js")
js = path.read_text()

# -------------------------------------------------
# 1. Add project/diagnosis mode switching functions
# -------------------------------------------------

assist_functions = r'''
function isProjectMode(){
  return $("#category")?.value === "diy";
}

function updateAssistMode(){
  const projectMode = isProjectMode();
  const title = $("#assistTitle");
  const prompt = $("#promptLabel");
  const symptom = $("#symptom");
  const button = $("#diagnoseButton");

  if(title){
    title.textContent = projectMode
      ? "Project Assistant"
      : "Quick Diagnosis";
  }

  if(prompt){
    prompt.textContent = projectMode
      ? "Describe your project"
      : "What is it doing?";
  }

  if(symptom){
    symptom.placeholder = projectMode
      ? "Example: Install 12x24 porcelain tile on a bathroom floor. Include dimensions, surface type, materials, and desired layout."
      : "Describe the exact symptom, when it happens, warning lights, noises, smells, and anything already tested.";
  }

  if(button){
    button.textContent = projectMode
      ? "Build project plan"
      : "Run diagnosis";
  }
}

'''

if "function isProjectMode()" not in js:
    marker = "const GARAGE_KEY ="
    start = js.find(marker)

    if start == -1:
        raise RuntimeError("Could not find GARAGE_KEY.")

    end = js.find(";", start)

    if end == -1:
        raise RuntimeError("Could not find the end of GARAGE_KEY.")

    js = js[:end + 1] + "\n" + assist_functions + js[end + 1:]


# -------------------------------------------------
# 2. Replace the compressed result renderer
# -------------------------------------------------

render_start = js.find("function renderResult(data){")
render_end_marker = "const selectedMedia = [];"
render_end = js.find(render_end_marker, render_start)

if render_start == -1:
    raise RuntimeError("Could not find renderResult(data).")

if render_end == -1:
    raise RuntimeError("Could not find selectedMedia after renderResult.")

new_render = r'''
function renderResult(data){
  const result = $("#result");
  const projectMode = data.category === "diy";

  result.classList.remove("hidden");

  const heading = projectMode
    ? "Project plan"
    : "Diagnostic result";

  const checksHeading = projectMode
    ? "Preparation and steps"
    : "Checks";

  const repairHeading = projectMode
    ? "Materials, tools, and next steps"
    : "Repair path";

  result.innerHTML = `
    <h2>${heading}</h2>
    <p>${esc(data.summary)}</p>
    <div class="safety">${esc(data.safety_message)}</div>

    ${data.causes.map(cause => `
      <article class="cause">
        <h3>
          ${esc(cause.title)}
          <span class="confidence">
            ${Math.round(cause.confidence * 100)}%
          </span>
        </h3>

        <p>${esc(cause.why)}</p>

        <h4>${checksHeading}</h4>
        <ol>
          ${cause.checks.map(item => `
            <li>${esc(item)}</li>
          `).join("")}
        </ol>

        <h4>${repairHeading}</h4>
        <ul>
          ${cause.repair.map(item => `
            <li>${esc(item)}</li>
          `).join("")}
        </ul>
      </article>
    `).join("")}
  `;

  result.scrollIntoView({
    behavior: "smooth",
    block: "start"
  });
}

'''

js = js[:render_start] + new_render + js[render_end:]


# -------------------------------------------------
# 3. Watch the category dropdown
# -------------------------------------------------

category_listener = r'''
$("#category")?.addEventListener("change", updateAssistMode);
updateAssistMode();

'''

if '$("#category")?.addEventListener("change", updateAssistMode);' not in js:
    navigation_marker = '$$("[data-page]").forEach'
    position = js.find(navigation_marker)

    if position == -1:
        raise RuntimeError("Could not find page navigation code.")

    js = js[:position] + category_listener + js[position:]


# -------------------------------------------------
# 4. Add projectMode to form submission
# -------------------------------------------------

submit_marker = '''const button = $("#diagnoseButton");
  button.disabled = true;
  setMediaError("");'''

submit_replacement = '''const button = $("#diagnoseButton");
  const projectMode = isProjectMode();
  button.disabled = true;
  setMediaError("");'''

if "const projectMode = isProjectMode();" not in js[js.find('$("#diagnosisForm")'):]:
    if submit_marker not in js:
        raise RuntimeError("Could not find diagnosis submit button setup.")

    js = js.replace(
        submit_marker,
        submit_replacement,
        1,
    )


# -------------------------------------------------
# 5. Update progress and completion messages
# -------------------------------------------------

js = js.replace(
    '"Analyzing symptoms…"',
    '(projectMode ? "Building project plan…" : "Analyzing symptoms…")',
)

js = js.replace(
    '"Diagnosis complete."',
    '(projectMode ? "Project plan complete." : "Diagnosis complete.")',
)

js = js.replace(
    '`Could not run diagnosis: ${error.message}`',
    '`${projectMode ? "Could not build project plan" : "Could not run diagnosis"}: ${error.message}`',
)

js = js.replace(
    '"No saved diagnoses yet."',
    '"No saved activity yet."',
)


path.write_text(js)
print("static/app.js patched successfully.")
