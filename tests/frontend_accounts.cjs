const {JSDOM}=require('jsdom');
const fs=require('fs');
const path=require('path');
const assert=require('assert');
const root=path.resolve(__dirname,'../static');
const tick=()=>new Promise(resolve=>setTimeout(resolve,0));
async function harness({configured=true,user=null,storage={},scriptFails=false}={}) {
  const dom=new JSDOM(fs.readFileSync(path.join(root,'index.html'),'utf8'),{url:'https://pocket.test',runScripts:'outside-only'});
  const w=dom.window;const calls=[];w.Headers=Headers;w.Request=Request;w.scrollTo=()=>{};w.HTMLElement.prototype.scrollIntoView=()=>{};
  w.alert=message=>{throw Error(message)};
  for(const [key,value] of Object.entries(storage))w.localStorage.setItem(key,JSON.stringify(value));
  let wrongCode=true;
  w.fetch=async (url,options={})=>{
    calls.push({url,options,body:options.body?JSON.parse(options.body):null});
    let data={},status=200;
    if(url==='/api/auth/config')data={configured};
    else if(url==='/api/auth/session')data={user};
    else if(url==='/api/auth/signup')data={verification_required:true};
    else if(url==='/api/auth/verify') {
      if(wrongCode){data={detail:'That code is incorrect or expired.'};status=400;wrongCode=false;}
      else data={user:{id:'account-a',email:'a@example.com',verified:true}};
    }else if(url==='/health')data={status:'ok'};
    else if(url==='/api/profiles')data=[];
    return {ok:status<400,status,json:async()=>data};
  };
  const append=w.document.body.appendChild.bind(w.document.body);
  w.document.body.appendChild=node=>{
    const result=append(node);
    if(node.tagName==='SCRIPT'&&node.src.includes('/static/app.js'))queueMicrotask(()=>{
      if(scriptFails)node.onerror();else{w.eval(fs.readFileSync(path.join(root,'app.js'),'utf8'));node.onload();}
    });
    return result;
  };
  const ids=[...w.document.querySelectorAll('[id]')].map(el=>el.id);
  assert.equal(new Set(ids).size,ids.length,'IDs must be unique');
  w.eval(fs.readFileSync(path.join(root,'accounts.js'),'utf8'));await tick();await tick();
  return {w,calls,q:s=>w.document.querySelector(s),close:()=>w.close()};
}
(async()=>{
  let h=await harness();const {w,q,calls}=h;
  assert(q('#appContent').hidden);assert(!q('#accountForm').hidden);
  assert(!w.document.querySelector('script[src*="/static/app.js"]'));
  q('#accountEmailInput').value='a@example.com';q('#accountPassword').value='a-long-password';
  q('#accountForm').dispatchEvent(new w.Event('submit',{cancelable:true}));await tick();
  assert(q('#accountForm').hidden);assert(!q('#verificationForm').hidden);assert(q('#appContent').hidden);
  assert.equal(q('#accountPassword').value,'');assert(q('#resendCode').disabled);
  q('#verificationCode').value='000000';q('#verificationForm').dispatchEvent(new w.Event('submit',{cancelable:true}));await tick();
  assert(q('#appContent').hidden);assert(q('#accountStatus').textContent.includes('incorrect'));
  q('#verificationCode').value='123456';q('#verificationForm').dispatchEvent(new w.Event('submit',{cancelable:true}));await tick();await tick();
  assert(!q('#appContent').hidden);assert(q('#authGate').hidden);assert.equal(q('#accountEmail').textContent,'a@example.com');
  await w.fetch('/api/profiles');assert.equal(calls.at(-1).options.headers.get('X-Pocket-Guru-User'),'account-a');
  assert(![...Array(w.localStorage.length)].map((_,i)=>w.localStorage.key(i)).some(key=>/token|password/.test(key)));
  h.close();
  h=await harness({configured:false});assert(h.q('#appContent').hidden);assert(h.q('#accountSubmit').disabled);assert(h.q('#accountStatus').textContent.includes('being set up'));h.close();
  h=await harness({user:{id:'account-a',email:'a@example.com',verified:true},scriptFails:true});assert(h.q('#appContent').hidden);assert(h.q('#accountStatus').textContent.includes('Could not load'));h.close();
  const garage=[{id:'one',name:'A truck',type:'automotive'}];
  h=await harness({user:{id:'account-b',email:'b@example.com',verified:true},storage:{'pocket-guru-garage-v1:account-a':garage,'pocket-mechanic-garage-v4':garage}});
  assert.equal(h.q('#garageCount').textContent,'0');assert(!h.q('#legacyImport').hidden);
  h.q('#importLocalData').click();assert.equal(h.q('#garageCount').textContent,'1');assert.equal(h.w.localStorage.getItem('pocket-guru-legacy-claimed'),'account-b');
  assert.equal(JSON.parse(h.w.localStorage.getItem('pocket-guru-garage-v1:account-a'))[0].name,'A truck');h.close();
  console.log('PASS: signup gate, wrong/valid verification code, cooldown, private account header, no client tokens, unconfigured gate, load failure, account-specific garage and explicit legacy import');
})().catch(error=>{console.error(error);process.exit(1)});
