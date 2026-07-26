const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const HISTORY_KEY = 'pocket-mechanic-history-v4';
const GARAGE_KEY = 'pocket-mechanic-garage-v4';

function esc(v){return String(v ?? '').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));}
function read(key){try{return JSON.parse(localStorage.getItem(key)||'[]')}catch{return[]}}
function write(key,value){localStorage.setItem(key,JSON.stringify(value));}
function showPage(name){$$('.page').forEach(p=>p.classList.toggle('active',p.id===`page-${name}`));$$('.bottom-nav button').forEach(b=>b.classList.toggle('active',b.dataset.page===name));window.scrollTo({top:0,behavior:'smooth'});}

$$('[data-page]').forEach(b=>b.addEventListener('click',()=>showPage(b.dataset.page)));
$$('[data-diagnose]').forEach(b=>b.addEventListener('click',()=>{$('#category').value=b.dataset.diagnose;showPage('diagnose');}));

function renderHistory(){
  const items=read(HISTORY_KEY);
  const html=items.length?items.map(x=>`<div class="history-item"><strong>${esc(x.category)}</strong><div>${esc(x.symptom)}</div><small class="muted">${esc(x.title)} · ${Math.round(x.confidence*100)}%</small></div>`).join(''):'<p class="muted">No saved diagnoses yet.</p>';
  $('#homeHistory').innerHTML=html; $('#fullHistory').innerHTML=html;
}
$('#clearHistory').addEventListener('click',()=>{write(HISTORY_KEY,[]);renderHistory();});

function renderGarage(){
  const items=read(GARAGE_KEY); $('#garageCount').textContent=items.length;
  $('#garageList').innerHTML=items.length?items.map(x=>`<article class="garage-item"><div><h3>${esc(x.name)}</h3><div class="garage-meta">${esc([x.year,x.make,x.model,x.engine].filter(Boolean).join(' · '))}</div>${x.notes?`<small>${esc(x.notes)}</small>`:''}</div><div class="garage-actions"><button data-use="${esc(x.id)}">Diagnose</button><button data-delete="${esc(x.id)}">✕</button></div></article>`).join(''):'<p class="muted">Your garage is empty. Add your first vehicle, appliance, or piece of equipment.</p>';
  $('#profileSelect').innerHTML='<option value="">None selected</option>'+items.map(x=>`<option value="${esc(x.id)}">${esc(x.name)}</option>`).join('');
  $$('[data-delete]').forEach(b=>b.onclick=()=>{write(GARAGE_KEY,items.filter(x=>x.id!==b.dataset.delete));renderGarage();});
  $$('[data-use]').forEach(b=>b.onclick=()=>{const x=items.find(i=>i.id===b.dataset.use);if(x){$('#category').value=x.category;$('#profileSelect').value=x.id;showPage('diagnose');}});
}

$('#garageForm').addEventListener('submit',e=>{
  e.preventDefault(); const items=read(GARAGE_KEY);
  items.unshift({id:crypto.randomUUID?crypto.randomUUID():String(Date.now()),name:$('#garageName').value.trim(),category:$('#garageCategory').value,year:$('#garageYear').value,make:$('#garageMake').value.trim(),model:$('#garageModel').value.trim(),engine:$('#garageEngine').value.trim(),notes:$('#garageNotes').value.trim()});
  write(GARAGE_KEY,items);e.target.reset();renderGarage();
});

function renderResult(data){
  const r=$('#result');r.classList.remove('hidden');r.innerHTML=`<h2>Diagnostic result</h2><p>${esc(data.summary)}</p><div class="safety">${esc(data.safety_message)}</div>${data.causes.map(c=>`<article class="cause"><h3>${esc(c.title)} <span class="confidence">${Math.round(c.confidence*100)}%</span></h3><p>${esc(c.why)}</p><h4>Checks</h4><ol>${c.checks.map(v=>`<li>${esc(v)}</li>`).join('')}</ol><h4>Repair path</h4><ul>${c.repair.map(v=>`<li>${esc(v)}</li>`).join('')}</ul></article>`).join('')}`;r.scrollIntoView({behavior:'smooth',block:'start'});
}

$('#diagnosisForm').addEventListener('submit',async e=>{
  e.preventDefault();$('#status').textContent='Analyzing symptoms…';
  const payload={category:$('#category').value,symptom:$('#symptom').value,answers:{},profile_id:$('#profileSelect').value||null};
  try{const res=await fetch('/api/diagnoses',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});if(!res.ok)throw new Error(`Request failed (${res.status})`);const data=await res.json();renderResult(data);const top=data.causes[0];const items=read(HISTORY_KEY);items.unshift({category:data.category,symptom:data.symptom,title:top.title,confidence:top.confidence,created_at:data.created_at});write(HISTORY_KEY,items.slice(0,30));renderHistory();$('#status').textContent='Diagnosis complete.';}catch(err){$('#status').textContent=`Could not run diagnosis: ${err.message}`;}
});

$('#obdForm').addEventListener('submit',async e=>{
  e.preventDefault();const code=$('#obdCode').value.trim().toUpperCase();const out=$('#obdResult');out.innerHTML='<p class="muted">Looking up code…</p>';
  try{const res=await fetch(`/api/obd/${encodeURIComponent(code)}`);if(!res.ok)throw new Error('This code is not in the offline starter library yet.');const d=await res.json();out.innerHTML=`<article class="obd-card"><p class="eyebrow">${esc(d.system)}</p><h2>${esc(d.code)} — ${esc(d.title)}</h2><h3>First checks</h3><ol>${d.first_checks.map(x=>`<li>${esc(x)}</li>`).join('')}</ol></article>`;}catch(err){out.innerHTML=`<div class="safety">${esc(err.message)}</div>`;}
});

async function connection(){try{const r=await fetch('/health');const d=await r.json();$('#connection').textContent=`Local · v${d.version}`;}catch{$('#connection').textContent='Offline';}}
if('serviceWorker'in navigator)navigator.serviceWorker.register('/static/service-worker.js').catch(()=>{});
renderHistory();renderGarage();connection();
