(() => {
 const pending=new Map();
 const reportFor=id=>{if(!pending.has(id))pending.set(id,fetch('/demos/'+encodeURIComponent(id)+'/build-result.json').then(r=>r.ok?r.json():null).catch(()=>null));return pending.get(id)};
 window.addOpenInUnrealButton=(host,spec)=>{
  if(!host||host.dataset.unrealOpenAttached)return;
  host.dataset.unrealOpenAttached='true';
  const button=document.createElement('button');button.textContent=spec.scene?'Open scene in Unreal':'Open environment in Unreal';
  const status=document.createElement('p');status.setAttribute('role','status');status.setAttribute('aria-live','polite');
  button.onclick=async()=>{button.disabled=true;status.textContent='Checking the Unreal editor…';try{
   const response=await fetch('/api/open-unreal',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(spec)});let job=await response.json();if(!response.ok)throw Error(job.error||'Could not open in Unreal');
   const deadline=Date.now()+100000;
   while(Date.now()<deadline){await new Promise(r=>setTimeout(r,700));const r=await fetch('/api/jobs/'+job.id);job=await r.json();if(!r.ok)throw Error(job.error||'Could not read open status');status.textContent=job.stage||job.status;if(job.status==='failed')throw Error(job.error);if(job.status==='complete'){status.textContent=spec.scene?'Scene opened in Unreal with Sequencer. Press Play in Sequencer to preview.':'Environment opened in Unreal.';return}}
   throw Error('Opening is taking longer than expected. Check Unreal before retrying.');
  }catch(error){status.textContent=error.message}finally{button.disabled=false}};
  const folder=document.createElement('button');folder.textContent='Open level folder';
  folder.onclick=async()=>{folder.disabled=true;try{const response=await fetch('/api/open-folder',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(spec)});const data=await response.json();if(!response.ok)throw Error(data.error||'Could not open folder');status.textContent='Folder opened in File Explorer. Level file: '+data.filename}catch(error){status.textContent=error.message}finally{folder.disabled=false}};
  host.append(button,folder,status);
 };
 const visited=new WeakSet();
 function scan(){
  for(const node of document.querySelectorAll('img,p,small,video')){
   if(visited.has(node))continue;
   // Labels and images in the inventory/composite movies refer to assets or background plates.
   if(node.closest('#view-assets,#composite-movies'))continue;
   if(node.tagName==='VIDEO'){
    visited.add(node);if(node.getAttribute('src')==='/delivery_scene/special-delivery.mp4')window.addOpenInUnrealButton(node.closest('.panel'),{scene:'delivery'});continue;
   }
   if(node.tagName==='IMG'){
    const match=(node.getAttribute('src')||'').match(/^\/demos\/([A-Za-z0-9_]+)\//);if(!match)continue;visited.add(node);
    reportFor(match[1]).then(report=>{if(report?.level)window.addOpenInUnrealButton(node.closest('.card')||node.closest('.panel'),{level:report.level})});
   }else{
    const match=node.textContent.match(/\/Game\/EnvironmentDemos\/[A-Za-z0-9_]+/);if(!match)continue;visited.add(node);window.addOpenInUnrealButton(node.closest('.card')||node.closest('.panel'),{level:match[0]});
   }
  }
 }
 let scheduled=false;new MutationObserver(()=>{if(scheduled)return;scheduled=true;queueMicrotask(()=>{scheduled=false;scan()})}).observe(document.querySelector('main'),{childList:true,subtree:true});scan();
})();
