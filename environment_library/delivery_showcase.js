(async()=>{
 const response=await fetch('/delivery_scene/delivery.json',{cache:'no-store'});if(!response.ok)return;
 const report=await response.json();if(!report.full_decode_passed)return;
 const section=document.createElement('section');section.style.order='4';section.className='panel';
 const heading=document.createElement('h2');heading.textContent=report.title;
 const text=document.createElement('p');text.textContent='Amber delivers a parcel, bumps a crate, and Leo helps clear the way. A new 21-second scene rendered entirely in Unreal, with four camera shots, dialogue, facial animation and recorded collision physics.';
 const video=document.createElement('video');video.controls=true;video.preload='metadata';video.src='/delivery_scene/special-delivery.mp4';video.poster='/delivery_scene/poster.png';video.style.cssText='width:100%;max-width:960px';
 const captions=document.createElement('track');captions.kind='subtitles';captions.src='/delivery_scene/captions.vtt';captions.srclang='en';captions.label='English';captions.default=true;video.append(captions);
 const note=document.createElement('p');note.textContent='24 fps · 960 × 540 · Movie Render Queue. Foot placement, hand grip and acting still need refinement; this is a development scene rather than a finished film.';
 section.append(heading,text,video,note);document.getElementById('native-movies').append(section);
})().catch(()=>{});
