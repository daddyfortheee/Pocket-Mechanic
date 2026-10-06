const assert=require('node:assert/strict'),fs=require('fs'),{JSDOM}=require('jsdom');
(async()=>{
const w=new JSDOM(fs.readFileSync('static/index.html','utf8'),{url:'https://pocket.test',runScripts:'outside-only'}).window,q=s=>w.document.querySelector(s),key='pocket-mechanic-garage-v4';
w.localStorage.setItem(key,JSON.stringify([{id:'existing',category:'appliance',name:'My washer'}]));let restored=0;w.document.addEventListener('pocket:backup-restored',()=>restored++);w.eval(fs.readFileSync('static/data-backup.js','utf8'));
async function upload(data){Object.defineProperty(q('#importWork'),'files',{configurable:true,value:[{size:100,text:async()=>JSON.stringify(data)}]});q('#importWork').dispatchEvent(new w.Event('change'));await new Promise(r=>setTimeout(r,10));}
await upload({format:'pocket-guru-backup',version:1,garage:[{id:'new',category:'motorcycle',name:'Bike'},{id:'existing',category:'appliance',name:'Overwrite'}],history:[]});
assert.equal(restored,1);let records=JSON.parse(w.localStorage.getItem(key));assert.equal(records.length,2);assert.equal(records[0].name,'My washer');
await upload({garage:[],history:[]});assert(q('#backupStatus').textContent.includes('Could not restore'));assert.equal(JSON.parse(w.localStorage.getItem(key)).length,2);assert.equal(restored,1);
w.close();console.log('PASS: backup merges, preserves existing records, rejects invalid file without data loss');
})().catch(e=>{console.error(e);process.exit(1)});
