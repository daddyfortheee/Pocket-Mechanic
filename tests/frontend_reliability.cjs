const assert=require('node:assert/strict'),fs=require('fs'),{JSDOM}=require('jsdom');
(async()=>{
const dom=new JSDOM(fs.readFileSync('static/index.html','utf8'),{url:'https://pocket.test',runScripts:'outside-only'});
const w=dom.window,q=s=>w.document.querySelector(s);w.scrollTo=()=>{};w.HTMLElement.prototype.scrollIntoView=()=>{};w.AbortSignal=AbortSignal;
let release,calls=0;w.fetch=async url=>{
 if(url==='/health')return {ok:false};
 calls++;await new Promise(r=>release=r);
 return {ok:true,json:async()=>({id:'test',category:'automotive',symptom:'Engine does not start',summary:'Test',safety_message:'Test safely',created_at:new Date().toISOString(),causes:[{title:'Test battery',confidence:.8,why:'Test',checks:['Test'],repair:['Test'],safety:'low'}]})};
};
w.eval(fs.readFileSync('static/app.js','utf8'));await new Promise(r=>setTimeout(r,0));
assert.equal(q('#connection').textContent,'Offline');q('#symptom').value='Engine does not start';
const submit=()=>q('#diagnosisForm').dispatchEvent(new w.Event('submit',{cancelable:true}));submit();submit();await new Promise(r=>setTimeout(r,0));assert.equal(calls,1,'Duplicate submits must not start duplicate diagnoses');
w.Storage.prototype.setItem=()=>{throw new Error('quota exceeded')};release();await new Promise(r=>setTimeout(r,10));
assert(q('#result').textContent.includes('Test battery'),'Completed diagnosis must remain visible when storage fails');assert(q('#status').textContent.includes('Could not save history'));assert.equal(q('#diagnoseButton').disabled,false);
w.close();console.log('PASS: failed health, duplicate submissions, full-storage result recovery');
})().catch(e=>{console.error(e);process.exit(1)});
