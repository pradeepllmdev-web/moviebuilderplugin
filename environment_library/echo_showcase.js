(async()=>{
 const r=await fetch('/demos/EchoInspector/movie.json',{cache:'no-store'});if(!r.ok)return;const movie=await r.json();if(!movie.full_decode_passed)return;
 const section=document.createElement('section');section.className='panel';section.style.order='0';
 const title=document.createElement('h2');title.textContent=movie.title+(movie.revision>=3?' — gentler animation (v3)':movie.revision>=2?' — corrected animation (v2)':' — new movie demo');const note=document.createElement('p');note.textContent='16 seconds · 640 × 360 · Leo and Amber. Created as a new movie in 3dobjectnew, with two shots, local dialogue, Blender body/facial performance, native Unreal rendering and Movie Builder assembly.';
 const video=document.createElement('video');video.controls=true;video.preload='metadata';video.src=movie.video;video.poster=movie.poster;video.style.width='100%';const track=document.createElement('track');track.kind='subtitles';track.src=movie.captions;track.srclang='en';track.label='English';track.default=true;video.append(track);
 const controls=document.createElement('div');const status=document.createElement('p');
 for(const [shot,label] of [[-10,'Open lion rock-gap jump'],[-9,'Open lion boulder scramble'],[-8,'Open lion mountain-climbing test'],[-7,'Open improved supercar driving scene'],[-6,'Open lion fire-road driving scene'],[-5,'Open fixed-grip IK test'],[-4,'Open fallen-branch interaction test'],[-3,'Open lion forest adventure'],[-2,'Open running + lip sync + blink test'],[-1,'Open running + lip sync test'],[0,'Open single-animation lion test in Unreal'],[914,'Open shot 1 in Unreal'],[915,'Open shot 2 in Unreal']]){
  const button=document.createElement('button');button.textContent=label;button.onclick=async()=>{
   button.disabled=true;status.textContent='Opening level and Sequencer…';
   try{const response=await fetch('/api/open-unreal',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scene:shot===-10?'lion-jump':shot===-9?'lion-scramble':shot===-8?'lion-climb':shot===-7?'lion-drive-v2':shot===-6?'lion-drive':shot===-5?'lion-grip':shot===-4?'lion-branch':shot===-3?'lion-forest':shot===-2?'lion-run-blink':shot===-1?'lion-run-mouth':shot===0?'lion-trial':'echo-inspector',shot_id:shot})});let job=await response.json();if(!response.ok)throw Error(job.error||'Could not open scene');
    while(job.status==='running'){await new Promise(resolve=>setTimeout(resolve,700));job=await(await fetch('/api/jobs/'+job.id)).json();}
    if(job.status!=='complete')throw Error(job.error||'Could not open scene');
    status.textContent='Opened in Unreal. Press Play in the Sequencer timeline to preview, or drag the playhead to inspect a frame.';
   }catch(error){status.textContent=error.message;}finally{button.disabled=false;}
  };controls.append(button);
 }
 const help=document.createElement('p');help.textContent='Lion isolation test: six seconds, one running clip. No dialogue, facial animation, gaze, foot locking or added acting. Open in Unreal and press Sequencer Play.';
 const limitation=document.createElement('p');limitation.textContent=movie.limitations.join(' ');section.append(title,note,controls,help,status,video,limitation);document.getElementById('native-movies').append(section);
})().catch(console.error);

