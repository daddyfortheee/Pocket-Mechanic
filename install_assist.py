from pathlib import Path
from datetime import datetime
import re
import shutil


main_path = Path("app/main.py")
index_path = Path("static/index.html")
js_path = Path("static/app.js")

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

for path in (main_path, index_path, js_path):
    backup = path.with_name(f"{path.name}.assist-backup-{stamp}")
    shutil.copy2(path, backup)
    print(f"Backup: {backup}")


# -------------------------
# Backend routing
# -------------------------

main = main_path.read_text()

planner_import = "from app.project_planner import build_project_plan"

if planner_import not in main:
    lines = main.splitlines()

    for index, line in enumerate(lines):
        if line.startswith("from app.diagnosis_engine import"):
            lines.insert(index + 1, planner_import)
            break
    else:
        raise RuntimeError("Could not find the diagnosis engine import.")

    main = "\n".join(lines) + "\n"


if 'if req.category == "diy":' not in main:
    media_pattern = re.compile(
        r'(def diagnose\(req: DiagnosisRequest\) -> DiagnosisResponse:\s*\n'
        r'\s+media = req\.answers\.get\("media", \[\]\)\s*\n'
        r'\s+media_count = len\(media\) if isinstance\(media, list\) else 0\s*\n)'
    )

    match = media_pattern.search(main)

    if not match:
        raise RuntimeError("Could not locate the diagnose() media section.")

    diy_branch = '''
    if req.category == "diy":
        plan = build_project_plan(
            description=req.symptom,
            answers=req.answers,
            media_count=media_count,
        )

        project_result = Cause(
            title=plan["title"],
            confidence=plan["confidence"],
            why=plan["why"],
            checks=plan["checks"],
            repair=plan["repair"],
            safety="medium",
        )

        return DiagnosisResponse(
            id=str(uuid4()),
            created_at=datetime.now(timezone.utc).isoformat(),
            category=req.category,
            symptom=req.symptom,
            summary=plan["summary"],
            safety_message=plan["safety_message"],
            causes=[project_result],
        )

'''

    main = (
        main[:match.end()]
        + diy_branch
        + main[match.end():]
    )

main_path.write_text(main)
print("Patched app/main.py")


# -------------------------
# HTML labels
# -------------------------

index = index_path.read_text()

index = index.replace(
    "<h1>Quick Diagnosis</h1>",
    '<h1 id="assistTitle">Quick Diagnosis</h1>',
)

index = index.replace(
    "<label>What is it doing?<textarea",
    '<label><span id="promptLabel">What is it doing?</span><textarea',
)

index = index.replace(
    '<button data-page="diagnose"><span>🔎</span>Quick Diagnosis</button>',
    '<button data-page="diagnose"><span>🧰</span>Assist</button>',
)

index_path.write_text(index)
print("Patched static/index.html")


# -------------------------
# JavaScript behavior
# -------------------------

js = js_path.read_text()

assist_code = '''
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
    garage_match = re.search(
        r"const GARAGE_KEY\s*=\s*[^;]+;",
        js,
    )

    if not garage_match:
        raise RuntimeError("Could not locate GARAGE_KEY.")

    js = (
        js[:garage_match.end()]
        + "\n"
        + assist_code
        + js[garage_match.end():]
    )


new_render = '''
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

    ${data.causes.map(c => `
      <article class="cause">
        <h3>
          ${esc(c.title)}
          <span class="confidence">
            ${Math.round(c.confidence * 100)}%
          </span>
        </h3>

        <p>${esc(c.why)}</p>

        <h4>${checksHeading}</h4>
        <ol>
          ${c.checks.map(value => `
            <li>${esc(value)}</li>
          `).join("")}
        </ol>

        <h4>${repairHeading}</h4>
        <ul>
          ${c.repair.map(value => `
            <li>${esc(value)}</li>
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

render_pattern = re.compile(
    r"function renderResult\(data\)\{.*?result\.scrollIntoView\(\{behavior:"
    r'"smooth",block:"start"\}\);\s*\}',
    re.DOTALL,
)

if not render_pattern.search(js):
    raise RuntimeError("Could not locate renderResult().")

js = render_pattern.sub(
    lambda _: new_render.strip(),
    js,
    count=1,
)


if '$("#category")?.addEventListener("change", updateAssistMode);' not in js:
    navigation_text = '$$("[data-page]").forEach'

    position = js.find(navigation_text)

    if position == -1:
        raise RuntimeError("Could not locate page-navigation code.")

    listener = '''
$("#category")?.addEventListener("change", updateAssistMode);
updateAssistMode();

'''

    js = js[:position] + listener + js[position:]


submit_marker = '''  const button = $("#diagnoseButton");
  button.disabled = true;
  setMediaError("");
'''

submit_replacement = '''  const button = $("#diagnoseButton");
  const projectMode = isProjectMode();
  button.disabled = true;
  setMediaError("");
'''

if submit_marker in js:
    js = js.replace(
        submit_marker,
        submit_replacement,
        1,
    )


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

js_path.write_text(js)
print("Patched static/app.js")
print("Assist upgrade installed successfully.")
