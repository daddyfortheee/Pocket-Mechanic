from pathlib import Path

path = Path("static/app.js")
js = path.read_text()

# Add the project-mode helper near the beginning of app.js.
if "function isProjectMode()" not in js:
    helper = """
function isProjectMode() {
    const categoryElement = document.querySelector("#category");
    const category = (categoryElement?.value || "").toLowerCase();

    return (
        category.includes("diy") ||
        category.includes("project") ||
        category.includes("home improvement") ||
        category.includes("construction") ||
        category.includes("craft")
    );
}

"""
    marker = "const $ = selector => document.querySelector(selector);"

    if marker in js:
        js = js.replace(marker, marker + "\n" + helper, 1)
    else:
        js = helper + js

# Add projectMode immediately after the diagnosis form is submitted.
old_submit = """  const button = $("#diagnoseButton");
  button.disabled = true;
  setMediaError("");"""

new_submit = """  const button = $("#diagnoseButton");
  const projectMode = isProjectMode();

  button.disabled = true;
  setMediaError("");"""

if old_submit in js:
    js = js.replace(old_submit, new_submit, 1)
elif "const projectMode = isProjectMode();" not in js:
    raise RuntimeError("Could not find diagnosis button setup.")

# Update the first progress message.
old_progress = """    $("#status").textContent = selectedMedia.length
      ? "Uploading pictures and video..."
      : "Analyzing symptoms...";"""

new_progress = """    $("#status").textContent = selectedMedia.length
      ? "Uploading pictures and video..."
      : projectMode
        ? "Building project plan..."
        : "Analyzing symptoms...";"""

if old_progress in js:
    js = js.replace(old_progress, new_progress, 1)

# Update the message shown after media upload.
js = js.replace(
    '''    $("#status").textContent = "Analyzing symptoms...";''',
    '''    $("#status").textContent = projectMode
      ? "Building project plan..."
      : "Analyzing symptoms...";''',
    1
)

# Update remaining completion/error/activity wording where present.
js = js.replace(
    '"Diagnosis complete."',
    'projectMode ? "Project plan complete." : "Diagnosis complete."'
)

js = js.replace(
    '`Could not run diagnosis: ${error.message}`',
    '`${projectMode ? "Could not build project plan" : "Could not run diagnosis"}: ${error.message}`'
)

js = js.replace(
    '"No saved diagnoses yet."',
    'projectMode ? "No saved project activity yet." : "No saved diagnoses yet."'
)

path.write_text(js)
print("static/app.js patched successfully.")
