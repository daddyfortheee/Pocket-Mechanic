(() => {
  'use strict';
  const q = selector => document.querySelector(selector);
  const nativeFetch = window.fetch.bind(window);
  let mode = 'signup', pendingEmail = '', purpose = 'signup', loaded = false, ready = false;
  let resendAt = 0, busy = false;
  const status = (text, error=false) => {q('#accountStatus').textContent=text;q('#accountStatus').classList.toggle('error',error);};
  function setBusy(value){
    busy=value;
    q('#authGate').querySelectorAll('button').forEach(button=>button.disabled=value||!ready);
    q('#resendCode').disabled=value||!ready||Date.now()<resendAt;
  }
  async function api(path,body={}){
    const response=await nativeFetch('/api/auth/'+path,{method:'POST',headers:{'Content-Type':'application/json'},credentials:'same-origin',body:JSON.stringify(body),cache:'no-store'});
    let data;
    try{data=await response.json();}catch{throw new Error('The account service did not respond. Please try again.');}
    if(!response.ok){
      const message=typeof data.detail==='string'?data.detail:'Check your details and try again.';
      const error=new Error(message);error.status=response.status;throw error;
    }
    return data;
  }
  function showMode(next){
    mode=next;pendingEmail='';q('#verificationCode').value='';q('#newPassword').value='';q('#accountPassword').value='';
    q('#accountForm').hidden=false;q('#verificationForm').hidden=true;q('#authTabs').hidden=false;
    q('#showSignup').classList.toggle('active',mode==='signup');q('#showSignin').classList.toggle('active',mode==='signin');
    q('#passwordLabel').hidden=mode==='recover';q('#accountPassword').required=mode!=='recover';q('#accountPassword').disabled=mode==='recover';
    q('#accountPassword').autocomplete=mode==='signup'?'new-password':'current-password';
    q('#forgotPassword').hidden=mode!=='signin';
    q('#accountHeading').textContent=mode==='signup'?'Welcome to Pocket Guru':mode==='signin'?'Welcome back':'Reset your password';
    q('#accountHelp').textContent=mode==='signup'?'Create your account. We’ll email you a six-digit code to verify it.':mode==='signin'?'Sign in to pick up where you left off.':'Enter your email and we’ll send a password-reset code.';
    q('#accountSubmit').textContent=mode==='signup'?'Create account & send code':mode==='signin'?'Sign in':'Send reset code';status('');
  }
  function showCode(email,kind){
    pendingEmail=email;purpose=kind;
    q('#accountPassword').value='';q('#verificationCode').value='';q('#newPassword').value='';q('#accountForm').hidden=true;q('#authTabs').hidden=true;q('#verificationForm').hidden=false;
    q('#verificationHeading').textContent=kind==='recovery'?'Choose a new password':'Verify your email';
    q('#verificationHelp').textContent=`Enter the six-digit code sent to ${email}.`;
    q('#newPasswordLabel').hidden=kind!=='recovery';q('#newPassword').required=kind==='recovery';q('#newPassword').disabled=kind!=='recovery';
    q('#verifySubmit').textContent=kind==='recovery'?'Reset password & sign in':'Verify & continue';
    q('#verificationCode').focus();
  }
  function startCooldown(){resendAt=Date.now()+60000;updateCooldown();}
  function updateCooldown(){const remaining=Math.max(0,Math.ceil((resendAt-Date.now())/1000));q('#resendCode').textContent=remaining?`Resend in ${remaining}s`:'Resend code';q('#resendCode').disabled=busy||!ready||remaining>0;}
  setInterval(updateCooldown,1000);
  async function enterApp(user){
    if(!user?.verified||!user.id)throw new Error('Verify your email to continue.');
    if(window.pocketGuruUser&&window.pocketGuruUser.id!==user.id){location.reload();return;}
    window.pocketGuruUser=user;
    q('#accountEmail').textContent=user.email;
    q('#signOut').setAttribute('aria-label',`Sign out of ${user.email}`);
    q('#accountPassword').value='';q('#newPassword').value='';q('#verificationCode').value='';
    if(!loaded){
      await new Promise((resolve,reject)=>{const script=document.createElement('script');script.src='/static/app.js?v=12';script.onload=resolve;script.onerror=()=>reject(new Error('Could not load Pocket Guru. Refresh and try again.'));document.body.appendChild(script);});
      loaded=true;
    }
    q('#authGate').hidden=true;q('#appContent').hidden=false;q('#headerAccount').hidden=false;q('#connection').hidden=true;
    window.scrollTo({top:0});
  }
  // Bind each private request to the account shown on screen, including across tabs.
  window.fetch=async(input,init={})=>{
    const url=new URL(typeof input==='string'?input:input.url,location.href);
    const isPrivate=url.origin===location.origin&&url.pathname.startsWith('/api/')&&!url.pathname.startsWith('/api/auth/');
    if(!isPrivate)return nativeFetch(input,init);
    const headers=new Headers(init.headers||(input instanceof Request?input.headers:undefined));
    if(window.pocketGuruUser)headers.set('X-Pocket-Guru-User',window.pocketGuruUser.id);
    const options={...init,headers,credentials:'same-origin',cache:'no-store'};
    const response=await nativeFetch(input,options);
    if(response.status!==401)return response;
    const refreshed=await api('session');
    if(!refreshed.user?.verified||refreshed.user.id!==window.pocketGuruUser?.id){location.reload();throw new Error('Please sign in again.');}
    return nativeFetch(input,options);
  };
  q('#showSignup').onclick=()=>showMode('signup');q('#showSignin').onclick=()=>showMode('signin');q('#forgotPassword').onclick=()=>showMode('recover');
  q('#backToAccount').onclick=()=>showMode(purpose==='recovery'?'recover':'signup');
  q('#accountForm').addEventListener('submit',async event=>{
    event.preventDefault();if(busy||!ready)return;setBusy(true);status('Please wait…');
    const email=q('#accountEmailInput').value.trim().toLowerCase();
    try{
      if(mode==='signup'){
        await api('signup',{email,password:q('#accountPassword').value});showCode(email,'signup');startCooldown();status('Check your inbox for your verification code.');
      }else if(mode==='signin'){
        const data=await api('signin',{email,password:q('#accountPassword').value});await enterApp(data.user);
      }else{
        await api('recover',{email});showCode(email,'recovery');startCooldown();status('If an account exists, a reset code is on its way.');
      }
    }catch(error){
      if(mode==='signin'&&error.status===403){showCode(email,'signup');status('Your email needs verification. Tap Resend code to get a new code.',true);}else status(error.message,true);
    }finally{setBusy(false);}
  });
  q('#verificationForm').addEventListener('submit',async event=>{
    event.preventDefault();if(busy||!ready)return;setBusy(true);status('Checking your code…');
    try{const payload={email:pendingEmail,code:q('#verificationCode').value.trim(),purpose};if(purpose==='recovery')payload.new_password=q('#newPassword').value;const data=await api('verify',payload);await enterApp(data.user);}catch(error){status(error.message,true);}finally{setBusy(false);}
  });
  q('#resendCode').onclick=async()=>{
    if(busy||Date.now()<resendAt)return;setBusy(true);
    try{const data=await api('resend',{email:pendingEmail,purpose});startCooldown();status(data.message);}catch(error){status(error.message,true);}finally{setBusy(false);}
  };
  q('#signOut').onclick=async()=>{
    q('#signOut').disabled=true;
    try{await api('signout');location.reload();}catch(error){q('#signOut').disabled=false;alert(error.message);}
  };
  async function boot(){
    setBusy(true);
    try{
      const response=await nativeFetch('/api/auth/config',{cache:'no-store'});if(!response.ok)throw new Error('Could not reach the account service. Refresh and try again.');
      const config=await response.json();
      if(!config.configured){status('Account creation is being set up. Please try again shortly.');q('#connection').textContent='Setup in progress';return;}
      ready=true;const data=await api('session');if(data.user)await enterApp(data.user);else{showMode('signup');q('#connection').textContent='Connected';}
    }catch(error){status(error.message,true);}finally{setBusy(false);}
  }
  boot();
})();
