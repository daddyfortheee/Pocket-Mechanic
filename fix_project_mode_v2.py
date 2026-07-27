from pathlib import Path
import re

path = Path("static/app.js")
js = path.read_text()

# 1. Add project-mode helper.
if "function isProjectMode()" not in js:
    helper = r'''
function isProjectMode() {
  const category = ($("#category")?.value || "").toLowerCase();

  return [
    "diy",
    "project",
    "home improvement",
    "construction",
    "craft"
  ].some(type => category.includes(type));
}

'''

    dollar_helper = re.search(
        r'const\s+\$\s*=\s*selector\s*=>\s*document\.querySelector\(selector\);\s*',
        js
    )

    if dollar_helper:
        position = dollar_helper.end()
        js = js[:position] + "\n" + helper + js[position:]
    else:
        js = helper + js

# 2. Add projectMode after the diagnosis button declaration.
if "const projectMode = isProjectMode();" not in js:
    pattern = r'(const\s+button\s*=\s*\$\(["\']#diagnoseButton["\']\);\s*)'

    js, count = re.subn(
        pattern,
        r'\1\n  const projectMode = isProjectMode();\n',
        js,
        count=1
    )

    if count == 0:
        raise RuntimeError("Could not locate the diagnoseButton declaration.")

# 3. Change initial status text.
pattern = re.compile(
    r'\$\(["\']#status["\']\)\.textContent\s*=\s*selectedMedia\.length\s*'
    r'\?\s*["\']Uploading pictures and video\.\.\.["\']\s*'
    r':\s*["\']Analyzing symptoms\.\.\.["\'];',
    re.MULTILINE
)

replacement = '''$("#status").textContent = selectedMedia.length
      ? "Uploading pictures and video..."
      : projectMode
        ? "Building project plan..."
        : "Analyzing symptoms...";'''

js, _ = pattern.subn(replacement, js, count=1)

# 4. Change the status after media upload.
js = re.sub(
    r'\$\(["\']#status["\']\)\.textContent\s*=\s*["\']Analyzing symptoms\.\.\.["\'];',
    '''$("#status").textContent = projectMode
      ? "Building project plan..."
      : "Analyzing symptoms...";''',
    js,
    count=1
)

# 5. Change completion wording.
js = js.replace(
    '"Diagnosis complete."',
    'projectMode ? "Project plan complete." : "Diagnosis complete."'
)

js = js.replace(
    "'Diagnosis complete.'",
    'projectMode ? "Project plan complete." : "Diagnosis complete."'
)

# 6. Change error wording.
js = js.replace(
    '`Could not run diagnosis: ${error.message}`',
    '`${projectMode ? "Could not build project plan" : "Could not run diagnosis"}: ${error.message}`'
)

# 7. Change empty-history wording.
js = js.replace(
    '"No saved diagnoses yet."',
    'projectMode ? "No saved project activity yet." : "No saved diagnoses yet."'
)

js = js.replace(
    "'No saved diagnoses yet.'",
    'projectMode ? "No saved project activity yet." : "No saved diagnoses yet."'
)

path.write_text(js)
print("SUCCESS: static/app.js patched.")
