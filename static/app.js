(() => {
if(!window.pocketGuruUser?.verified) return;

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

const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const HISTORY_KEY = 'pocket-guru-history-v1:' + window.pocketGuruUser.id;
const GARAGE_KEY = 'pocket-guru-garage-v1:' + window.pocketGuruUser.id;

function esc(v){return String(v ?? '').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));}
function read(key){try{return JSON.parse(localStorage.getItem(key)||'[]')}catch{return[]}}
function write(key,value){localStorage.setItem(key,JSON.stringify(value));}
function showPage(name){$$('.page').forEach(p=>p.classList.toggle('active',p.id===`page-${name}`));$$('.bottom-nav button').forEach(b=>b.classList.toggle('active',b.dataset.page===name));window.scrollTo({top:0,behavior:'smooth'});}

$$('[data-page]').forEach(b=>b.addEventListener('click',()=>showPage(b.dataset.page)));
$$('[data-diagnose]').forEach(b=>b.addEventListener('click',()=>{$('#category').value=b.dataset.diagnose;$('#category').dispatchEvent(new Event('change'));showPage('diagnose');}));

function renderHistory(){
  const items=read(HISTORY_KEY);
  const html=items.length?items.map(x=>`<div class="history-item"><strong>${esc(x.category)}</strong><div>${esc(x.symptom)}</div><small class="muted">${esc(x.title)} · ${Math.round(x.confidence*100)}%</small></div>`).join(''):'<p class="muted">No saved diagnoses yet.</p>';
  $('#homeHistory').innerHTML=html; $('#fullHistory').innerHTML=html;
}
$('#clearHistory').addEventListener('click',()=>{write(HISTORY_KEY,[]);renderHistory();});

function renderGarage(){
  const items=read(GARAGE_KEY); $('#garageCount').textContent=items.length;
  $('#garageList').innerHTML=items.length?items.map(x=>`<article class="garage-item"><div><h3>${esc(x.name)}</h3><div class="garage-meta">${esc([x.year,x.make,x.model,x.engine].filter(Boolean).join(' · '))}</div>${x.notes?`<small>${esc(x.notes)}</small>`:''}</div><div class="garage-actions"><button data-use="${esc(x.id)}">Diagnose</button><button data-delete="${esc(x.id)}" aria-label="Remove ${esc(x.name)} from My Garage">✕</button></div></article>`).join(''):'<p class="muted">Your garage is empty. Add your first vehicle, appliance, or piece of equipment.</p>';
  const selectedId = $('#profileSelect').value;
  $('#profileSelect').innerHTML='<option value="">Choose an item (optional)</option>'+items.map(x=>`<option value="${esc(x.id)}">${esc(x.name)}</option>`).join('');
  syncDiagnosisItems(); $('#profileSelect').value=selectedId;
  $$('[data-delete]').forEach(b=>b.onclick=()=>{write(GARAGE_KEY,items.filter(x=>x.id!==b.dataset.delete));renderGarage();});
  $$('[data-use]').forEach(b=>b.onclick=()=>{const x=items.find(i=>i.id===b.dataset.use);if(x){$('#category').value=x.category;syncDiagnosisItems();$('#profileSelect').value=x.id;$('#category').dispatchEvent(new Event('change'));$('#profileSelect').value=x.id;showPage('diagnose');}});
}

let addingFromDiagnosis = false;
let diagnosisRevision = 0;
function resetDiagnosis(){
  diagnosisRevision += 1;
  $('#symptom').value = '';
  $('#status').textContent = '';
  $('#result').innerHTML = '';
  $('#result').classList.add('hidden');
  selectedMedia.forEach(item => URL.revokeObjectURL(item.url));
  selectedMedia.length = 0;
  renderMediaPreview();
  setMediaError();
  $('#diagnoseButton').disabled = false;
}

const garageForm = $('#garageForm');
const garageFormHome = garageForm.parentElement;
function updateItemFields(){
  const type = $('#garageCategory').value;
  const vehicle = ['automotive','motorcycle'].includes(type);
  $('#garageYear').parentElement.hidden = !vehicle;
  $('#garageYear').disabled = !vehicle;
  const fields = [
    ['garageMake', vehicle ? 'Make' : 'Brand', vehicle ? 'Make (optional)' : 'Brand (optional)'],
    ['garageModel', 'Model', vehicle ? 'Model (optional)' : 'Model number (optional)'],
    ['garageEngine', vehicle ? 'Engine' : type === 'appliance' ? 'Appliance type / details' : 'System / equipment type', vehicle ? 'Engine (optional)' : 'Type / details (optional)']
  ];
  fields.forEach(([id,label,placeholder])=>{
    const input = $('#'+id);
    input.parentElement.firstChild.textContent = label;
    input.placeholder = placeholder;
  });
  $('#garageName').placeholder = vehicle ? 'Vehicle name' : 'Item name';
}
function syncDiagnosisItems(){
  const category = $('#category').value;
  const previous = $('#profileSelect').value;
  $('#profileSelect').innerHTML = '<option value="">Choose an item (optional)</option>' + read(GARAGE_KEY).filter(x=>x.category===category).map(x=>`<option value="${esc(x.id)}">${esc(x.name)}</option>`).join('');
  $('#profileSelect').value = previous;
  $('#addDiagnosisItem').textContent = ['automotive','motorcycle'].includes(category) ? 'Add vehicle' : category==='appliance' ? 'Add appliance' : 'Add item';
  $('#addDiagnosisItem').hidden = category==='diy';
}
function closeItemEditor(){
  garageFormHome.appendChild(garageForm);
  $('#diagnosisItemEditor').hidden = true;
  addingFromDiagnosis = false;
}
$('#addDiagnosisItem').addEventListener('click',()=>{
  resetDiagnosis();
  $('#profileSelect').value = '';
  garageForm.reset();
  $('#garageCategory').value = $('#category').value;
  updateItemFields();
  addingFromDiagnosis = true;
  $('#diagnosisItemEditor').appendChild(garageForm);
  $('#diagnosisItemEditor').hidden = false;
  $('#diagnosisItemEditor').scrollIntoView({behavior:'smooth',block:'start'});
  $('#garageName').focus({preventScroll:true});
});
$('#garageCategory').addEventListener('change',updateItemFields);
$('#category').addEventListener('change',()=>{resetDiagnosis();closeItemEditor();syncDiagnosisItems();});
$('#profileSelect').addEventListener('change',resetDiagnosis);
$$('[data-page]').forEach(b=>b.addEventListener('click',closeItemEditor));
$$('[data-diagnose]').forEach(b=>b.addEventListener('click',()=>{closeItemEditor();syncDiagnosisItems();}));
const cancelItem = document.createElement('button');
cancelItem.type='button';cancelItem.textContent='Cancel';
cancelItem.addEventListener('click',closeItemEditor);$('#itemEditorActions').appendChild(cancelItem);
garageForm.addEventListener('submit',e=>{
  e.preventDefault();
  e.stopPropagation();
  const items=read(GARAGE_KEY);
  const item={id:crypto.randomUUID?crypto.randomUUID():String(Date.now()),name:$('#garageName').value.trim(),category:$('#garageCategory').value,year:$('#garageYear').disabled?'':$('#garageYear').value,make:$('#garageMake').value.trim(),model:$('#garageModel').value.trim(),engine:$('#garageEngine').value.trim(),notes:$('#garageNotes').value.trim()};
  if(!item.name){$('#garageName').focus();return;}
  items.unshift(item);
  try{write(GARAGE_KEY,items);}catch{alert('Could not save this item. Your browser storage may be full.');return;}
  const returnToDiagnosis = addingFromDiagnosis;
  closeItemEditor();garageForm.reset();updateItemFields();renderGarage();
  if(returnToDiagnosis){resetDiagnosis();$('#category').value=item.category;syncDiagnosisItems();$('#profileSelect').value=item.id;$('#status').textContent = `${item.name} saved to My Garage. Start a new diagnosis below.`;$('#diagnosisForm').scrollIntoView({behavior:'smooth',block:'start'});}
});
updateItemFields();
syncDiagnosisItems();

function renderVisualAnalysis(analysis){
  if(!analysis) return '';
  if(!analysis.available) return `<section class="cause"><h3>Photos were not analyzed</h3><p>${esc(analysis.reason)}</p>${analysis.attachment_warning ? `<p>${esc(analysis.attachment_warning)}</p>` : ''}</section>`;
  const list = (title, items) => Array.isArray(items) && items.length ? `<h4>${title}</h4><ul>${items.map(item => `<li>${esc(item)}</li>`).join('')}</ul>` : '';
  return `<section class="cause"><h3>Photo inspection</h3><p class="muted">Preliminary visual evidence. Confirm the fault with tests before ordering parts.</p><p><strong>Brand:</strong> ${esc(analysis.brand)}<br><strong>Model:</strong> ${esc(analysis.model)}<br><strong>Serial / VIN:</strong> ${esc(analysis.serial_or_vin)}</p>${list('Visible label text',analysis.visible_text)}${list('Visible components',analysis.identified_parts)}${list('Visible abnormalities',analysis.visible_problems)}<p>${esc(analysis.likely_relevance)}</p>${list('Next photos and tests',analysis.follow_up)}${analysis.safety_warning && !['None','Unknown'].includes(analysis.safety_warning) ? `<div class="safety">${esc(analysis.safety_warning)}</div>` : ''}<p class="muted">Analyzed: ${(analysis.analyzed_files || []).map(esc).join(', ')}</p>${list('Not analyzed',analysis.skipped_files)}${analysis.attachment_warning ? `<p>${esc(analysis.attachment_warning)}</p>` : ''}</section>`;
}

function renderResult(data){
  const r=$('#result');r.classList.remove('hidden');r.innerHTML=`<h2>Your next steps</h2><p>${esc(data.summary)}</p>${renderVisualAnalysis(data.visual_analysis)}<div class="safety">${esc(data.safety_message)}</div>${data.causes.map(c=>`<article class="cause"><h3>${esc(c.title)} <span class="confidence">${Math.round(c.confidence*100)}%</span></h3><p>${esc(c.why)}</p><h4>Checks</h4><ol>${c.checks.map(v=>`<li>${esc(v)}</li>`).join('')}</ol><h4>Repair path</h4><ul>${c.repair.map(v=>`<li>${esc(v)}</li>`).join('')}</ul></article>`).join('')}`;r.scrollIntoView({behavior:'smooth',block:'start'});
}


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

$('#diagnosisForm').addEventListener('submit', async event => {
  event.preventDefault();

  const revision = diagnosisRevision;
  const button = $('#diagnoseButton');
  
  const projectMode = isProjectMode();
button.disabled = true;
  setMediaError();

  try{
    $('#status').textContent = selectedMedia.length
      ? 'Uploading pictures and video…'
      : 'Analyzing symptoms…';

    const uploadedMedia = await uploadSelectedMedia();
    if(revision !== diagnosisRevision) return;

    $('#status').textContent = uploadedMedia.length ? 'Inspecting photos and analyzing symptoms…' : 'Analyzing symptoms…';

    const payload = {
      category: $('#category').value,
      symptom: $('#symptom').value,
      answers: {
        media: uploadedMedia,
        item: read(GARAGE_KEY).find(x=>x.id === $('#profileSelect').value) || null
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
    if(revision !== diagnosisRevision) return;
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
      ? (data.visual_analysis?.available ? 'Diagnosis and photo inspection complete.' : 'Symptom diagnosis complete. Photos were not analyzed; see details above.')
      : projectMode ? "Project plan complete." : "Diagnosis complete.";
  }catch(error){
    if(revision !== diagnosisRevision) return;
    $('#status').textContent = `${projectMode ? "Could not build project plan" : "Could not run diagnosis"}: ${error.message}`;
  }finally{
    button.disabled = false;
  }
});

$('#obdForm').addEventListener('submit',async e=>{
  e.preventDefault();const code=$('#obdCode').value.trim().toUpperCase();const out=$('#obdResult');out.innerHTML='<p class="muted">Looking up code…</p>';
  try{const res=await fetch(`/api/obd/${encodeURIComponent(code)}`);if(!res.ok)throw new Error('This code is not in the offline starter library yet.');const d=await res.json();out.innerHTML=`<article class="obd-card"><p class="eyebrow">${esc(d.system)}</p><h2>${esc(d.code)} — ${esc(d.title)}</h2><h3>First checks</h3><ol>${d.first_checks.map(x=>`<li>${esc(x)}</li>`).join('')}</ol></article>`;}catch(err){out.innerHTML=`<div class="safety">${esc(err.message)}</div>`;}
});

async function connection(){try{const r=await fetch('/health');const d=await r.json();$('#connection').textContent=d.version ? 'Connected' : 'Connected';}catch{$('#connection').textContent='Offline';}}
if('serviceWorker'in navigator)navigator.serviceWorker.register('/static/service-worker.js').catch(()=>{});
renderHistory();renderGarage();connection();
const legacyGarage = read('pocket-mechanic-garage-v4');
const legacyHistory = read('pocket-mechanic-history-v4');
if(!localStorage.getItem('pocket-guru-legacy-claimed') && (legacyGarage.length || legacyHistory.length)){
  $('#legacyImport').hidden = false;
}
$('#importLocalData').addEventListener('click',()=>{
  try{
    const garage = read(GARAGE_KEY);
    const history = read(HISTORY_KEY);
    write(GARAGE_KEY,[...garage,...legacyGarage.filter(item=>!garage.some(saved=>saved.id===item.id))]);
    write(HISTORY_KEY,[...history,...legacyHistory.filter(item=>!history.some(saved=>saved.created_at===item.created_at && saved.symptom===item.symptom))].slice(0,30));
    localStorage.setItem('pocket-guru-legacy-claimed',window.pocketGuruUser.id);
    localStorage.removeItem('pocket-mechanic-garage-v4');
    localStorage.removeItem('pocket-mechanic-history-v4');
    $('#legacyImport').hidden = true;
    renderGarage();renderHistory();
  }catch{alert('Could not import your saved items. Your browser storage may be full.');}
});

/* POCKET_PROJECT_UI_V3 */
(() => {
  function projectUiMode() {
    const category = document.querySelector("#category");
    return (category?.value || "").toLowerCase() === "diy";
  }

  function findSymptomLabel() {
    const symptom = document.querySelector("#symptom");
    return symptom ? symptom.closest("label") : null;
  }

  function updateProjectInterface() {
    const isProject = projectUiMode();

    const title = document.querySelector("#assistTitle");
    const symptom = document.querySelector("#symptom");
    const symptomLabel = findSymptomLabel();
    const button = document.querySelector("#diagnoseButton");
    const mediaHeading = document.querySelector(
      "#page-diagnose .media-heading h2"
    );
    const mediaHelp = document.querySelector(
      "#page-diagnose .media-help"
    );

    if (isProject) {
      if (title) {
        title.textContent = "Project Planner";
      }

      if (symptomLabel) {
        const textNode = Array.from(symptomLabel.childNodes).find(
          node =>
            node.nodeType === Node.TEXT_NODE &&
            node.textContent.trim()
        );

        if (textNode) {
          textNode.textContent =
            "What are you building, installing, or repairing?";
        }
      }

      if (symptom) {
        symptom.placeholder =
          "Describe the project, work area, measurements, materials you already have, desired result, budget, and tools available.";
      }

      if (button) {
        button.textContent = "Build project plan";
      }

      if (mediaHeading) {
        mediaHeading.textContent = "Add project photos or video";
      }

      if (mediaHelp) {
        mediaHelp.textContent =
          "Add clear photos or video of the work area, layout, measurements, existing materials, damage, or the result you want to recreate.";
      }
    } else {
      if (title) {
        title.textContent = "Find a fix";
      }

      if (symptomLabel) {
        const textNode = Array.from(symptomLabel.childNodes).find(
          node =>
            node.nodeType === Node.TEXT_NODE &&
            node.textContent.trim()
        );

        if (textNode) {
          textNode.textContent = "What’s going wrong?";
        }
      }

      if (symptom) {
        symptom.placeholder =
          "Describe the exact symptom, when it happens, warning lights, noises, smells, and anything already tested.";
      }

      if (button) {
        button.textContent = "Find my next steps";
      }

      if (mediaHeading) {
        mediaHeading.textContent = "Add a photo";
      }

      if (mediaHelp) {
        mediaHelp.textContent =
          "Add a clear photo of the item, model label, or affected part. Videos can be attached, but aren’t analyzed yet.";
      }
    }
  }

  function initializeProjectInterface() {
    const category = document.querySelector("#category");

    if (category) {
      category.addEventListener("change", updateProjectInterface);
    }

    updateProjectInterface();
  }

  if (document.readyState === "loading") {
    document.addEventListener(
      "DOMContentLoaded",
      initializeProjectInterface
    );
  } else {
    initializeProjectInterface();
  }
})();

})();
