(() => {
 const section=document.createElement('section');section.className='panel';
 const title=document.createElement('h2');title.textContent='1. Describe your environment';
 const info=document.createElement('p');info.textContent='Uses the configured 3dobjectnew AI provider. Supports modular buildings, streets, lighting, procedural mountains, rain/snow prototypes and installed foliage/rocks. Cloud providers may use API credits. Review the plan and unsupported features before building.';
 const input=document.createElement('textarea');input.id='environment-prompt-input';input.setAttribute('aria-label','Environment prompt');input.rows=4;input.style.width='95%';input.maxLength=4000;input.value='Build a small village with two houses beside a straight road and a few spruce trees, at golden hour.';
 const planButton=document.createElement('button');planButton.textContent='Generate environment plan';
 const buildButton=document.createElement('button');buildButton.textContent='3. Build in Unreal';buildButton.disabled=true;
 const status=document.createElement('p');status.setAttribute('role','status');
 const details=document.createElement('details');const summary=document.createElement('summary');summary.textContent='2. Review the plan and unsupported requests';const pre=document.createElement('pre');details.append(summary,pre);
 const reference=document.createElement('input');reference.type='file';reference.accept='image/png,image/jpeg';reference.setAttribute('aria-label','Optional environment reference image');let referenceData=null;
 const referenceLabel=document.createElement('p');referenceLabel.textContent='Optional reference image — combined with your text in the same plan.';
 reference.onchange=()=>{referenceData=null;plan=null;buildButton.disabled=true;const file=reference.files[0];if(!file)return;if(file.size>12*1024*1024){status.textContent='Choose an image smaller than 12 MB';return}const reader=new FileReader();reader.onload=()=>{referenceData=reader.result};reader.readAsDataURL(file)};
 const output=document.createElement('div');let plan=null;
 async function request(path,body){const r=await fetch(path,{method:body?'POST':'GET',headers:body?{'Content-Type':'application/json'}:{},body:body?JSON.stringify(body):undefined});const data=await r.json();if(!r.ok)throw Error(data.error||'Request failed');return data}
 async function wait(job){for(;;){await new Promise(r=>setTimeout(r,1500));const data=await request('/api/jobs/'+job.id);status.textContent=data.stage||data.status;if(data.status==='failed')throw Error(data.error);if(['ready','complete'].includes(data.status))return data}}
 planButton.onclick=async()=>{planButton.disabled=true;buildButton.disabled=true;plan=null;output.replaceChildren();try{status.textContent='Planning…';const done=await wait(await request('/api/prompt-plan',{prompt:input.value,image:referenceData}));plan=done.plan;pre.textContent=JSON.stringify(plan,null,2);details.open=true;buildButton.disabled=false}catch(e){status.textContent=e.message}finally{planButton.disabled=false}};
 buildButton.onclick=async()=>{planButton.disabled=true;buildButton.disabled=true;try{const done=await wait(await request('/api/prompt-build',{plan}));const img=document.createElement('img');img.src=done.preview;img.alt='Prompt-generated Unreal environment';img.style.width='100%';const label=document.createElement('p');label.textContent='Saved '+done.report.level+' — '+done.report.warnings.join('; ');output.replaceChildren(label,img)}catch(e){status.textContent=e.message}finally{planButton.disabled=false;buildButton.disabled=!plan}};
 input.oninput=()=>{plan=null;buildButton.disabled=true};
 window.addEnvironmentAssetToPrompt=asset=>{
  if(!input.value.includes(asset.prompt_hint||asset.id)){
   const addition='\n'+(asset.prompt_hint||('Use asset '+asset.id+' ('+asset.name+').'));
   if(input.value.length+addition.length>input.maxLength)throw Error('Prompt is full. Shorten it before adding an asset.');
   input.value+=addition;input.dispatchEvent(new Event('input'));
  }
  location.hash='create/prompt';input.focus();status.textContent='Selected '+asset.name+'. Describe how many and where to place it, then generate a new plan.';
 };
section.append(title,info,input,referenceLabel,reference,document.createElement('br'),planButton,buildButton,status,details,output);document.getElementById('prompt-workspace').append(section);
})();
