(async()=>{
 const response=await fetch('/physics_lab/simulation.json',{cache:'no-store'});
 if(!response.ok)return;
 const report=await response.json();if(report.status!=='complete')return;
 const section=document.createElement('section');section.style.order='9';section.className='panel';
 const title=document.createElement('h2');title.textContent='Real Unreal character physics — ramp, crate and wall';
 const text=document.createElement('p');text.textContent='Leo and Amber are imported skeletal characters inside Unreal. Character capsules and gravity handle ground/ramp movement. An 18 kg crate receives a one-time contact-triggered impulse; the wall blocks movement. This live viewport recording is separate from the composited story previews.';
 const metrics=document.createElement('p');metrics.textContent='Measured crate displacement: '+(report.summary.crate_displacement_cm/100).toFixed(2)+' m. Lion travel: '+(report.summary.travel_cm.lion/100).toFixed(1)+' m; cat travel: '+(report.summary.travel_cm.cat/100).toFixed(1)+' m.';
 const video=document.createElement('video');video.controls=true;video.preload='metadata';video.src='/physics_lab/physics-test.mp4';video.poster='/physics_lab/setup.png';video.style.cssText='width:100%;max-width:960px';
 const limitation=document.createElement('p');limitation.className='warning';limitation.textContent='Still pending: foot IK/plant locking, stride-speed matching, idle transitions when blocked, and natural impact/recoil animations. Capsule grounding does not guarantee precise foot contact. The crate impulse is triggered from measured proximity and stopped movement, rather than a bound engine hit-event callback.';
 section.append(title,text,metrics,video,limitation);document.getElementById('physics-tests').append(section);
})().catch(()=>{});
