/* Portable, versioned backups of browser-local work. Imports merge; never erase work. */
(() => {
  const status=document.getElementById('backupStatus');
  const keys=['pocket-mechanic-garage-v4','pocket-mechanic-history-v4'];
  const read=key=>{const data=JSON.parse(localStorage.getItem(key)||'[]');if(!Array.isArray(data))throw new Error('Saved data is damaged.');return data;};
  document.getElementById('exportWork').onclick=()=>{
    try{
      const data={format:'pocket-guru-backup',version:1,created_at:new Date().toISOString(),garage:read(keys[0]),history:read(keys[1])};
      const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));
      const link=document.createElement('a');link.href=url;link.download='pocket-guru-backup.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
      status.textContent='Backup downloaded. Keep this file private; it contains your repair notes.';
    }catch(error){status.textContent='Could not export: '+error.message;}
  };
  document.getElementById('importWork').onchange=async event=>{
    const file=event.target.files[0];if(!file)return;
    const old=keys.map(key=>localStorage.getItem(key));
    try{
      if(file.size>5*1024*1024)throw new Error('Backup is larger than 5 MB.');
      const data=JSON.parse(await file.text());
      if(data.format!=='pocket-guru-backup'||data.version!==1||!Array.isArray(data.garage)||!Array.isArray(data.history))throw new Error('Choose a Pocket Guru backup file.');
      const categories=['automotive','motorcycle','appliance','equipment','home','diy'];
      const merged=[data.garage,data.history].map((records,i)=>{
        if(records.length>1000||records.some(x=>!x||typeof x!=='object'||Array.isArray(x)||typeof x.id!=='string'||!categories.includes(x.category)))throw new Error('Backup contains invalid records.');
        const current=read(keys[i]);const ids=new Set(current.map(x=>x.id));
        return [...current,...records.filter(x=>{if(ids.has(x.id))return false;ids.add(x.id);return true;})];
      });
      try{keys.forEach((key,i)=>localStorage.setItem(key,JSON.stringify(merged[i])));}catch(error){keys.forEach((key,i)=>{if(old[i]!==null)localStorage.setItem(key,old[i]);else localStorage.removeItem(key);});throw error;}
      document.dispatchEvent(new Event('pocket:backup-restored'));
      status.textContent='Backup restored. Existing items were kept.';
    }catch(error){status.textContent='Could not restore: '+error.message;}
    finally{event.target.value='';}
  };
})();
