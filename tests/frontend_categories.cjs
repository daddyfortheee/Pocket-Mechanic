const assert=require('node:assert/strict');
const fs=require('fs');
const {JSDOM}=require('jsdom');
(async()=>{
 const dom=new JSDOM(fs.readFileSync('static/index.html','utf8'),{url:'https://pocket.test',runScripts:'outside-only'});
 const w=dom.window,q=s=>w.document.querySelector(s),change=s=>q(s).dispatchEvent(new w.Event('change'));
 w.scrollTo=()=>{};w.HTMLElement.prototype.scrollIntoView=()=>{};
 w.fetch=async()=>({ok:true,json:async()=>({options:['Ford'],version:'test'})});
 w.eval(fs.readFileSync('static/app.js','utf8'));w.eval(fs.readFileSync('static/vehicle-picker.js','utf8'));
 for(const [category,brand,model] of [['appliance','GE','GFW550SSNWW'],['motorcycle','Honda','Rebel 500'],['equipment','Yamaha','Drive2']]){
  q('#garageCategory').value=category;change('#garageCategory');
  assert(!q('#garageMakePicker').hidden);assert(!q('#garageModelPicker').hidden);
  assert([...q('#garageMakePicker').options].some(o=>o.value===brand));
  q('#garageMakePicker').value=brand;change('#garageMakePicker');
  assert([...q('#garageModelPicker').options].some(o=>o.value===model));
  q('#garageModelPicker').value=model;change('#garageModelPicker');assert.equal(q('#garageModel').value,model);
  q('#garageMakePicker').value='__manual__';change('#garageMakePicker');assert.equal(q('#garageModel').value,'');assert(!q('#garageMake').hidden);
  q('#garageMake').value='Unlisted maker';change('#garageMake');q('#garageModelPicker').value='__manual__';change('#garageModelPicker');assert(!q('#garageModel').hidden);
 }
 q('#garageCategory').value='home';change('#garageCategory');q('#garageMakePicker').value='Trane';change('#garageMakePicker');q('#garageModelPicker').value='__manual__';change('#garageModelPicker');assert(!q('#garageModel').hidden);
 q('#garageCategory').value='motorcycle';change('#garageCategory');q('#garageMakePicker').value='Honda';change('#garageMakePicker');q('#garageYear').value='2004';q('#garageYear').dispatchEvent(new w.Event('input'));assert.equal(q('#garageMake').value,'Honda');
 q('#garageMake').value='Yamaha';q('#garageModel').value='Older model';q('#garageForm').dispatchEvent(new w.Event('pocket:item-loaded'));assert.equal(q('#garageModelPicker').value,'Older model');
 q('#category').value='appliance';change('#category');q('#addDiagnosisItem').click();assert(!q('#garageMakePicker').hidden);assert.equal(q('#garageMakePicker').getAttribute('aria-label'),'Choose brand');
 await new Promise(r=>setTimeout(r,0));
 console.log('PASS: category brands/models, dependent reset, manual entry, motorcycle year, saved models, shared diagnosis fields');w.close();
})().catch(e=>{console.error(e);process.exit(1)});
