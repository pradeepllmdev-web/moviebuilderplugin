(() => {

 const groups={
 assets:[['presets','Generators & presets','Procedural pieces and planning templates; distinct from installed models.',['asset-presets']],['environments','Environment assets','Installed catalogue assets available to prompt planning.',['asset-environments']],['characters','Characters','Verified character imports used in existing demos.',['asset-characters']],['animations','Animations','Verified imported action clips; compatibility is character-specific.',['asset-animations']]],
 'scene-create':[['prompt','Scene prompt','Describe actions and dialogue, review the supported plan, then build an editable Unreal scene.',['scene-create-workspace']],['movie','Movie prompt','Plan a short story with shots, build them, review in Unreal, then render and assemble.',['movie-prompt-workspace']]],
 movies:[['native','Unreal scenes','Completed scene Â· Characters and environment rendered together in Unreal.',['native-movies']],['composite','Composite scenes','Completed previews Â· Blender characters over Unreal backgrounds.',['composite-movies']],['scale','Scale tests','Completed check Â· Compare character, furniture and building sizes.',['scale-tests']],['physics','Physics tests','Completed test Â· Grounding, ramps and object contact.',['physics-tests']]],
 create:[['prompt','From prompt','Action Â· Describe a location, review the plan, then build in Unreal.',['prompt-workspace']],['image','From image','Action Â· Upload an outdoor reference and optionally draw a layout.',['image-workspace']],['example','Image example','Completed example Â· Reference, layout and saved result.',['image-examples']]],
 locations:[['comparisons','Prompt examples','Completed prompt tests Â· Compare different layouts, vegetation and lighting.',['prompt-comparisons']],['latest','Latest result','Completed build Â· Your most recent generated environment.',['latest-prompt']],['nature','Nature','Forests, rivers, meadows and highlands.',['nature-studies']],['buildings','Buildings & city','House interiors, exteriors and skyline.',['building-studies']],['architecture','Architecture kit','Reusable building pieces and their assembly example.',['architecture-kit']],['streets','Street kit','Roads, junctions, pavements and their connection example.',['street-kit']],['archive','All environments','Saved builds, earlier versions and experiments.',['gallery']]]
 };
 const remembered={};

 // Replace method cards with a consistent second tab row in every workspace.

 document.querySelector('.method-picker')?.remove();

 for(const [group,items] of Object.entries(groups)){

  const host=document.getElementById('view-'+group),nav=document.createElement('nav');nav.className='subtabs';nav.setAttribute('role','tablist');nav.setAttribute('aria-label',group+' functionality');

  const intro=host.querySelector('.section-intro')||host.querySelector('p');intro.after(nav);

  for(const [key,label,description,mounts] of items){

   const button=document.createElement('button');button.id='tab-'+group+'-'+key;button.textContent=label;button.dataset.subtab=key;button.setAttribute('role','tab');button.setAttribute('aria-controls','panel-'+group+'-'+key);nav.append(button);

   const panel=document.createElement('section');panel.id='panel-'+group+'-'+key;panel.setAttribute('role','tabpanel');panel.setAttribute('aria-labelledby',button.id);panel.hidden=true;

   const note=document.createElement('p');note.className='capability-note';note.textContent=description;panel.append(note);

   for(const id of mounts){let mount=document.getElementById(id);if(!mount){mount=document.createElement('div');mount.id=id}mount.hidden=false;panel.append(mount)}

   nav.after(panel);button.onclick=()=>show(group,key);

  }

  // Old wrappers are empty after the mounts move into their subpanels.

  for(const node of host.querySelectorAll('details.archive'))node.remove();

  host.querySelector('.subtabs').addEventListener('keydown',event=>{

   const buttons=[...nav.querySelectorAll('[role=tab]')];const current=buttons.indexOf(document.activeElement);if(current<0)return;

   let next;if(event.key==='ArrowRight')next=(current+1)%buttons.length;else if(event.key==='ArrowLeft')next=(current-1+buttons.length)%buttons.length;else if(event.key==='Home')next=0;else if(event.key==='End')next=buttons.length-1;else return;

   event.preventDefault();buttons[next].click();buttons[next].focus();

  });

 }

 document.getElementById('view-lab')?.remove();document.getElementById('location-studies')?.remove();document.getElementById('movie-demos')?.remove();document.getElementById('kit-demos')?.remove();document.getElementById('technical-demos')?.remove();

 function show(group,key){

  if(!groups[group])group='create';if(!groups[group].some(item=>item[0]===key))key=remembered[group]||groups[group][0][0];remembered[group]=key;

  for(const view of Object.keys(groups))document.getElementById('view-'+view).hidden=view!==group;

  for(const button of document.querySelectorAll('[data-view]')){const active=button.dataset.view===group;button.setAttribute('aria-pressed',String(active));button.setAttribute('aria-selected',String(active));button.setAttribute('role','tab');button.setAttribute('aria-controls','view-'+button.dataset.view);button.tabIndex=active?0:-1;document.getElementById('view-'+button.dataset.view).setAttribute('role','tabpanel')}

  for(const [item] of groups[group]){const active=item===key;document.getElementById('panel-'+group+'-'+item).hidden=!active;const button=document.getElementById('tab-'+group+'-'+item);button.setAttribute('aria-selected',String(active));button.tabIndex=active?0:-1}

  history.replaceState(null,'','#'+group+'/'+key);

 }

 for(const button of document.querySelectorAll('[data-view]'))button.onclick=()=>show(button.dataset.view);

 const mainNav=document.querySelector('.workspace-nav');mainNav.setAttribute('role','tablist');mainNav.addEventListener('keydown',event=>{const buttons=[...mainNav.querySelectorAll('[data-view]')];const current=buttons.indexOf(document.activeElement);if(current<0)return;let next;if(event.key==='ArrowRight')next=(current+1)%buttons.length;else if(event.key==='ArrowLeft')next=(current-1+buttons.length)%buttons.length;else if(event.key==='Home')next=0;else if(event.key==='End')next=buttons.length-1;else return;event.preventDefault();buttons[next].click();buttons[next].focus()});

 window.showEnvironmentImageWorkspace=()=>show('create','image');

 const restore=()=>{let [group,key]=location.hash.slice(1).split('/');if(group==='lab'){group=['scale','physics'].includes(key)?'movies':'locations'}show(group,key)};restore();addEventListener('hashchange',restore);

 (async()=>{

  const r=await fetch('/demos/latest-prompt.json',{cache:'no-store'});if(!r.ok)return;

  const latest=await r.json();if(!/^PromptSet_[a-f0-9]{12}$/.test(latest.id))return;

  const reportResponse=await fetch('/demos/'+latest.id+'/build-result.json');if(!reportResponse.ok)return;

  const report=await reportResponse.json();const section=document.createElement('section');section.className='panel';

  const badge=document.createElement('span');badge.className='badge';badge.textContent='Latest prompt build Â· prototype';

  const title=document.createElement('h2');title.textContent='Your latest prompt-generated environment';

  const link=document.createElement('a');link.href='/demos/'+latest.id+'/preview.png';link.target='_blank';const img=document.createElement('img');img.src=link.href;img.alt='Latest prompt-generated Unreal environment';img.style.width='100%';link.append(img);

  const note=document.createElement('p');note.textContent=(report.warnings||[]).join(' ');

  const details=document.createElement('details');const summary=document.createElement('summary');summary.textContent='Open in Unreal / view saved plan';const level=document.createElement('p');level.textContent=report.level;level.style.overflowWrap='anywhere';const recipe=document.createElement('a');recipe.href='/demos/'+latest.id+'/plan.json';recipe.textContent='Saved environment plan';recipe.target='_blank';details.append(summary,level,recipe);section.append(badge,title,link,note,details);document.getElementById('latest-prompt').append(section);

 })().catch(console.error);

})();

