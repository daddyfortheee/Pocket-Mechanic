const assert=require('node:assert/strict'),fs=require('fs'),{JSDOM}=require('jsdom');
(async()=>{
const dom=new JSDOM(fs.readFileSync('static/index.html','utf8'),{url:'https://pocket.test',runScripts:'outside-only'});
const w=dom.window,q=s=>w.document.querySelector(s),change=s=>q(s).dispatchEvent(new w.Event('change')),tick=()=>new Promise(r=>setTimeout(r,0));
w.scrollTo=()=>{};w.HTMLElement.prototype.scrollIntoView=()=>{};w.AbortSignal=AbortSignal;
const calls=[];let release;
w.fetch=async url=>{
 if(url==='/health')return {ok:true,json:async()=>({version:'test'})};
 calls.push(url);const p=new URL(url,w.location.href).searchParams;
 if(p.get('year')==='1990')await new Promise(r=>release=r);
 return {ok:true,json:async()=>({options:p.get('category')==='equipment'?['4020']:p.get('year')==='1980'?['KZ550-A1']:['New model'],source:'test year records'})};
};
w.eval(fs.readFileSync('static/app.js','utf8'));w.eval(fs.readFileSync('static/vehicle-picker.js','utf8'));
q('#garageCategory').value='motorcycle';change('#garageCategory');q('#garageMakePicker').value='Kawasaki';change('#garageMakePicker');await tick();
assert.equal(q('#garageModelPicker').options[0].textContent,'Choose a year first');
q('#garageYear').value='1980';q('#garageYear').dispatchEvent(new w.Event('input'));await new Promise(r=>setTimeout(r,320));await tick();
assert(calls.at(-1).includes('year=1980'));assert(calls.at(-1).includes('make=Kawasaki'));assert(calls.at(-1).includes('category=motorcycle'));
assert([...q('#garageModelPicker').options].some(o=>o.value==='KZ550-A1'));
q('#garageModelPicker').value='KZ550-A1';change('#garageModelPicker');
q('#garageYear').value='1990';q('#garageYear').dispatchEvent(new w.Event('input'));assert.equal(q('#garageModel').value,'');await new Promise(r=>setTimeout(r,320));
q('#garageYear').value='1980';q('#garageYear').dispatchEvent(new w.Event('input'));await new Promise(r=>setTimeout(r,320));await tick();release();await tick();assert([...q('#garageModelPicker').options].some(o=>o.value==='KZ550-A1'));assert(![...q('#garageModelPicker').options].some(o=>o.value==='New model'));
q('#garageCategory').value='equipment';change('#garageCategory');assert(!q('#garageYear').disabled);assert(!q('#garageYear').parentElement.hidden);
q('#garageYear').value='1968';q('#garageMakePicker').value='John Deere';change('#garageMakePicker');await tick();assert(calls.at(-1).includes('year=1968'));assert(calls.at(-1).includes('make=John+Deere'));assert([...q('#garageModelPicker').options].some(o=>o.value==='4020'));
q('#garageMakePicker').value='Ford';change('#garageMakePicker');assert.equal(q('#garageModel').value,'');await tick();
q('#garageModelPicker').value='__manual__';change('#garageModelPicker');assert(!q('#garageModel').hidden);
await tick();console.log('PASS: year/make queries, year reset, stale response rejection, farm year fields, manual fallback');w.close();
})().catch(e=>{console.error(e);process.exit(1)});
