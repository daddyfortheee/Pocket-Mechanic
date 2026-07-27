from pathlib import Path

ROOT = Path.home() / "Pocket-Mechanic"
INDEX = ROOT / "static" / "index.html"
JS = ROOT / "static" / "app.js"
CSS = ROOT / "static" / "styles.css"
MAIN = ROOT / "app" / "main.py"
REQ = ROOT / "requirements.txt"

# ---------------------------------------------------------
# 1. UPDATE index.html
# ---------------------------------------------------------
index = INDEX.read_text()

old_form = '''        <label>What is it doing?<textarea id="symptom" required minlength="5" placeholder="Describe the exact symptom, when it happens, warning lights, noises, smells, and anything already tested."></textarea></label>
        <button class="primary" type="submit">Run diagnosis</button><p id="status" class="muted"></p>'''

new_form = '''        <label>What is it doing?
          <textarea id="symptom" required minlength="5" placeholder="Describe the exact symptom, when it happens, warning lights, noises, smells, and anything already tested."></textarea>
        </label>

        <section class="media-uploader">
          <div class="media-heading">
            <div>
              <p class="eyebrow">OPTIONAL MEDIA</p>
              <h2>Add photos or video</h2>
            </div>
            <span id="mediaCount" class="badge">0 files</span>
          </div>

          <p class="muted media-help">
            Add a clear picture of the full item, its brand logo, model-number label,
            damaged part, wiring, leak, or warning display. You may also add a short video
            showing the sound, movement, vibration, smoke, or flashing lights.
          </p>

          <div class="media-buttons">
            <label class="media-button">
              <span>📷</span>
              Take pictures
              <input
                id="cameraInput"
                class="file-input"
                type="file"
                accept="image/*"
                capture="environment"
                multiple
              />
            </label>

            <label class="media-button">
              <span>🖼️</span>
              Choose files
              <input
                id="mediaInput"
                class="file-input"
                type="file"
                accept="image/jpeg,image/png,image/webp,image/heic,image/heif,video/mp4,video/webm,video/quicktime"
                multiple
              />
            </label>

            <label class="media-button">
              <span>🎥</span>
              Record video
              <input
                id="videoInput"
                class="file-input"
                type="file"
                accept="video/*"
                capture="environment"
              />
            </label>
          </div>

          <div id="mediaPreview" class="media-preview"></div>
          <p id="mediaError" class="media-error" role="alert"></p>
        </section>

        <button id="diagnoseButton" class="primary" type="submit">Run diagnosis</button>
        <p id="status" class="muted"></p>'''

if old_form not in index:
    raise SystemExit("Could not find the diagnosis form section in index.html")

index = index.replace(old_form, new_form)
index = index.replace(
    'href="/static/styles.css?v=4"',
    'href="/static/styles.css?v=5"'
)
index = index.replace(
    'src="/static/app.js?v=4"',
    'src="/static/app.js?v=5"'
)
index = index.replace(
    'Project Atlas 0.4',
    'Project Atlas 0.5'
)

INDEX.write_text(index)

# ---------------------------------------------------------
# 2. APPEND media styles
# ---------------------------------------------------------
css = CSS.read_text()

media_css = r'''

/* Project Atlas 0.5 — photo and video uploads */
.media-uploader{
  margin:18px 0;
  padding:17px;
  border:2px dashed #cbd5e1;
  border-radius:16px;
  background:#f8fafc
}
.media-heading{
  display:flex;
  justify-content:space-between;
  align-items:flex-start;
  gap:12px
}
.media-heading h2{
  margin:0;
  font-size:1.25rem
}
.media-help{
  margin:10px 0 15px;
  line-height:1.5
}
.media-buttons{
  display:grid;
  grid-template-columns:repeat(3,1fr);
  gap:9px
}
.media-button{
  display:flex;
  min-height:82px;
  margin:0;
  padding:12px 8px;
  align-items:center;
  justify-content:center;
  flex-direction:column;
  gap:5px;
  border:1px solid #cbd5e1;
  border-radius:13px;
  background:#fff;
  cursor:pointer;
  text-align:center;
  font-size:.84rem;
  font-weight:900
}
.media-button:active{
  transform:scale(.98)
}
.media-button span{
  font-size:1.55rem
}
.file-input{
  position:absolute;
  width:1px;
  height:1px;
  margin:0;
  padding:0;
  opacity:0;
  overflow:hidden
}
.media-preview{
  display:grid;
  grid-template-columns:repeat(3,1fr);
  gap:9px;
  margin-top:14px
}
.media-item{
  position:relative;
  min-width:0;
  overflow:hidden;
  border:1px solid #dbe1e8;
  border-radius:12px;
  background:#fff
}
.media-item img,
.media-item video{
  display:block;
  width:100%;
  height:105px;
  object-fit:cover;
  background:#0f172a
}
.media-details{
  padding:8px
}
.media-name{
  display:block;
  overflow:hidden;
  font-size:.72rem;
  font-weight:800;
  text-overflow:ellipsis;
  white-space:nowrap
}
.media-size{
  display:block;
  margin-top:2px;
  color:#64748b;
  font-size:.67rem
}
.remove-media{
  position:absolute;
  top:5px;
  right:5px;
  width:28px;
  height:28px;
  padding:0;
  border:0;
  border-radius:50%;
  background:#0f172ae6;
  color:#fff;
  font-size:1rem;
  font-weight:900
}
.media-error{
  min-height:1.2em;
  margin:10px 0 0;
  color:#b91c1c;
  font-size:.82rem;
  font-weight:800
}
.upload-progress{
  margin-top:8px;
  color:#b45309;
  font-weight:800
}
.primary:disabled{
  cursor:not-allowed;
  opacity:.55
}
@media(max-width:520px){
  .media-buttons{
    grid-template-columns:1fr
  }
  .media-button{
    min-height:58px;
    flex-direction:row
  }
  .media-preview{
    grid-template-columns:repeat(2,1fr)
  }
}
'''

if "Project Atlas 0.5 — photo and video uploads" not in css:
    css += media_css

CSS.write_text(css)

# ---------------------------------------------------------
# 3. PATCH app.js
# ---------------------------------------------------------
js = JS.read_text()

insert_before = "$('#diagnosisForm').addEventListener('submit',async e=>{"

media_js = r'''
const selectedMedia = [];
const MAX_IMAGES = 6;
const MAX_VIDEOS = 1;
const MAX_IMAGE_SIZE = 15 * 1024 * 1024;
const MAX_VIDEO_SIZE = 75 * 1024 * 1024;

function formatBytes(bytes){
  if(bytes < 1024) return `${bytes} B`;
  if(bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function mediaType(file){
  if(file.type.startsWith('image/')) return 'image';
  if(file.type.startsWith('video/')) return 'video';
  return 'unknown';
}

function setMediaError(message=''){
  $('#mediaError').textContent = message;
}

function addMediaFiles(fileList){
  setMediaError();

  for(const file of [...fileList]){
    const type = mediaType(file);

    if(type === 'unknown'){
      setMediaError('That file type is not supported.');
      continue;
    }

    const imageCount = selectedMedia.filter(x => mediaType(x.file) === 'image').length;
    const videoCount = selectedMedia.filter(x => mediaType(x.file) === 'video').length;

    if(type === 'image' && imageCount >= MAX_IMAGES){
      setMediaError(`You may attach up to ${MAX_IMAGES} pictures.`);
      continue;
    }

    if(type === 'video' && videoCount >= MAX_VIDEOS){
      setMediaError('You may attach one video.');
      continue;
    }

    if(type === 'image' && file.size > MAX_IMAGE_SIZE){
      setMediaError(`${file.name} is larger than the 15 MB picture limit.`);
      continue;
    }

    if(type === 'video' && file.size > MAX_VIDEO_SIZE){
      setMediaError(`${file.name} is larger than the 75 MB video limit.`);
      continue;
    }

    const duplicate = selectedMedia.some(
      x => x.file.name === file.name &&
           x.file.size === file.size &&
           x.file.lastModified === file.lastModified
    );

    if(duplicate) continue;

    selectedMedia.push({
      id: crypto.randomUUID ? crypto.randomUUID() : String(Date.now() + Math.random()),
      file,
      url: URL.createObjectURL(file)
    });
  }

  renderMediaPreview();

  $('#cameraInput').value = '';
  $('#mediaInput').value = '';
  $('#videoInput').value = '';
}

function removeMedia(id){
  const index = selectedMedia.findIndex(x => x.id === id);
  if(index === -1) return;

  URL.revokeObjectURL(selectedMedia[index].url);
  selectedMedia.splice(index, 1);
  renderMediaPreview();
}

function renderMediaPreview(){
  const preview = $('#mediaPreview');
  const count = selectedMedia.length;

  $('#mediaCount').textContent = `${count} ${count === 1 ? 'file' : 'files'}`;

  preview.innerHTML = selectedMedia.map(item => {
    const file = item.file;
    const type = mediaType(file);

    const visual = type === 'image'
      ? `<img src="${item.url}" alt="Selected repair picture">`
      : `<video src="${item.url}" controls preload="metadata"></video>`;

    return `
      <article class="media-item">
        ${visual}
        <button
          class="remove-media"
          type="button"
          data-remove-media="${item.id}"
          aria-label="Remove ${esc(file.name)}"
        >×</button>
        <div class="media-details">
          <span class="media-name">${esc(file.name)}</span>
          <span class="media-size">${formatBytes(file.size)}</span>
        </div>
      </article>
    `;
  }).join('');

  $$('[data-remove-media]').forEach(button => {
    button.addEventListener('click', () => removeMedia(button.dataset.removeMedia));
  });
}

async function uploadSelectedMedia(){
  if(!selectedMedia.length) return [];

  const formData = new FormData();

  selectedMedia.forEach(item => {
    formData.append('files', item.file, item.file.name);
  });

  const response = await fetch('/api/uploads', {
    method: 'POST',
    body: formData
  });

  if(!response.ok){
    let message = `Media upload failed (${response.status})`;

    try{
      const error = await response.json();
      message = error.detail || message;
    }catch{}

    throw new Error(message);
  }

  const result = await response.json();
  return result.files || [];
}

$('#cameraInput').addEventListener('change', event => {
  addMediaFiles(event.target.files);
});

$('#mediaInput').addEventListener('change', event => {
  addMediaFiles(event.target.files);
});

$('#videoInput').addEventListener('change', event => {
  addMediaFiles(event.target.files);
});

'''

if insert_before not in js:
    raise SystemExit("Could not find diagnosis submit handler in app.js")

if "const selectedMedia = [];" not in js:
    js = js.replace(insert_before, media_js + insert_before)

old_submit = """$('#diagnosisForm').addEventListener('submit',async e=>{
  e.preventDefault();$('#status').textContent='Analyzing symptoms…';
  const payload={category:$('#category').value,symptom:$('#symptom').value,answers:{},profile_id:$('#profileSelect').value||null};
  try{const res=await fetch('/api/diagnoses',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});if(!res.ok)throw new Error(`Request failed (${res.status})`);const data=await res.json();renderResult(data);const top=data.causes[0];const items=read(HISTORY_KEY);items.unshift({category:data.category,symptom:data.symptom,title:top.title,confidence:top.confidence,created_at:data.created_at});write(HISTORY_KEY,items.slice(0,30));renderHistory();$('#status').textContent='Diagnosis complete.';}catch(err){$('#status').textContent=`Could not run diagnosis: ${err.message}`;}
});"""

new_submit = """$('#diagnosisForm').addEventListener('submit', async event => {
  event.preventDefault();

  const button = $('#diagnoseButton');
  button.disabled = true;
  setMediaError();

  try{
    $('#status').textContent = selectedMedia.length
      ? 'Uploading pictures and video…'
      : 'Analyzing symptoms…';

    const uploadedMedia = await uploadSelectedMedia();

    $('#status').textContent = 'Analyzing symptoms…';

    const payload = {
      category: $('#category').value,
      symptom: $('#symptom').value,
      answers: {
        media: uploadedMedia
      },
      profile_id: $('#profileSelect').value || null
    };

    const response = await fetch('/api/diagnoses', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload)
    });

    if(!response.ok){
      let message = `Request failed (${response.status})`;

      try{
        const error = await response.json();
        message = error.detail || message;
      }catch{}

      throw new Error(message);
    }

    const data = await response.json();
    renderResult(data);

    const top = data.causes[0];
    const items = read(HISTORY_KEY);

    items.unshift({
      category: data.category,
      symptom: data.symptom,
      title: top.title,
      confidence: top.confidence,
      created_at: data.created_at,
      media_count: uploadedMedia.length
    });

    write(HISTORY_KEY, items.slice(0, 30));
    renderHistory();

    $('#status').textContent = uploadedMedia.length
      ? `Diagnosis complete with ${uploadedMedia.length} attachment${uploadedMedia.length === 1 ? '' : 's'}.`
      : 'Diagnosis complete.';
  }catch(error){
    $('#status').textContent = `Could not run diagnosis: ${error.message}`;
  }finally{
    button.disabled = false;
  }
});"""

if old_submit not in js:
    raise SystemExit("Could not replace the old diagnosis submit handler in app.js")

js = js.replace(old_submit, new_submit)
JS.write_text(js)

# ---------------------------------------------------------
# 4. PATCH FastAPI backend
# ---------------------------------------------------------
main = MAIN.read_text()

main = main.replace(
    "from pathlib import Path",
    "from pathlib import Path\nimport re"
)

main = main.replace(
    "from fastapi import FastAPI, HTTPException",
    "from fastapi import FastAPI, File, HTTPException, UploadFile"
)

old_dirs = '''BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"'''

new_dirs = '''BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = Path("/tmp/pocket-mechanic-uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_IMAGE_SIZE = 15 * 1024 * 1024
MAX_VIDEO_SIZE = 75 * 1024 * 1024
MAX_IMAGES = 6
MAX_VIDEOS = 1

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/heic",
    "image/heif",
}

ALLOWED_VIDEO_TYPES = {
    "video/mp4",
    "video/webm",
    "video/quicktime",
}'''

if old_dirs not in main:
    raise SystemExit("Could not find BASE_DIR section in main.py")

main = main.replace(old_dirs, new_dirs)

main = main.replace(
    'app = FastAPI(title="Pocket Mechanic API", version="0.4.0")',
    'app = FastAPI(title="Pocket Mechanic API", version="0.5.0")'
)

route_marker = '''
Category = Literal["automotive", "motorcycle", "appliance", "home", "equipment", "diy"]
'''

upload_route = '''
Category = Literal["automotive", "motorcycle", "appliance", "home", "equipment", "diy"]


def safe_filename(filename: str | None) -> str:
    original = filename or "upload"
    clean = re.sub(r"[^A-Za-z0-9._-]+", "_", original).strip("._")
    return clean[:120] or "upload"


@app.post("/api/uploads")
async def upload_media(files: list[UploadFile] = File(...)) -> dict[str, Any]:
    if not files:
        raise HTTPException(status_code=400, detail="No files were selected.")

    if len(files) > MAX_IMAGES + MAX_VIDEOS:
        raise HTTPException(
            status_code=400,
            detail=f"Upload up to {MAX_IMAGES} pictures and {MAX_VIDEOS} video.",
        )

    image_count = 0
    video_count = 0
    uploaded: list[dict[str, Any]] = []

    for upload in files:
        content_type = (upload.content_type or "").lower()

        if content_type in ALLOWED_IMAGE_TYPES:
            image_count += 1
            file_kind = "image"
            size_limit = MAX_IMAGE_SIZE

            if image_count > MAX_IMAGES:
                raise HTTPException(
                    status_code=400,
                    detail=f"Only {MAX_IMAGES} pictures may be uploaded.",
                )

        elif content_type in ALLOWED_VIDEO_TYPES:
            video_count += 1
            file_kind = "video"
            size_limit = MAX_VIDEO_SIZE

            if video_count > MAX_VIDEOS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Only {MAX_VIDEOS} video may be uploaded.",
                )

        else:
            raise HTTPException(
                status_code=415,
                detail=f"{upload.filename or 'The selected file'} is not a supported picture or video.",
            )

        contents = await upload.read(size_limit + 1)
        await upload.close()

        if len(contents) > size_limit:
            limit_mb = size_limit // (1024 * 1024)
            raise HTTPException(
                status_code=413,
                detail=f"{upload.filename or 'The selected file'} exceeds the {limit_mb} MB limit.",
            )

        media_id = str(uuid4())
        cleaned_name = safe_filename(upload.filename)
        extension = Path(cleaned_name).suffix.lower()
        stored_name = f"{media_id}{extension}"
        stored_path = UPLOAD_DIR / stored_name
        stored_path.write_bytes(contents)

        uploaded.append(
            {
                "id": media_id,
                "kind": file_kind,
                "filename": cleaned_name,
                "content_type": content_type,
                "size_bytes": len(contents),
                "stored_name": stored_name,
            }
        )

    return {
        "count": len(uploaded),
        "files": uploaded,
        "message": "Media uploaded successfully.",
    }
'''

if route_marker not in main:
    raise SystemExit("Could not find Category section in main.py")

main = main.replace(route_marker, upload_route)
MAIN.write_text(main)

# ---------------------------------------------------------
# 5. ADD python-multipart
# ---------------------------------------------------------
requirements = REQ.read_text()

if "python-multipart" not in requirements:
    if requirements and not requirements.endswith("\n"):
        requirements += "\n"
    requirements += "python-multipart==0.0.20\n"

REQ.write_text(requirements)

print()
print("SUCCESS: Pocket Mechanic media upload code installed.")
print("Updated:")
print("  static/index.html")
print("  static/styles.css")
print("  static/app.js")
print("  app/main.py")
print("  requirements.txt")
