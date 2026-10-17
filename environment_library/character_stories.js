(async () => {
  const response=await fetch('/demos/CharacterStories/manifest.json',{cache:'no-store'});
  if(!response.ok)return;
  const items=await response.json();
  const section=document.createElement('section');section.style.order='5';section.className='panel';
  const heading=document.createElement('h2');heading.textContent='Leo & Amber — stories across the environments';
  const text=document.createElement('p');
  text.textContent='New dialogue, lip sync, and scene-specific action studies using the existing lion and cat. Blender foreground performances are composited over still Unreal environment views. These composite scenes do not have an equivalent native Unreal scene to open. These 12 fps previews do not test in-engine contact, occlusion, or matched lighting. Industrial and suburban backgrounds retain their stylized kit appearance.';
  const grid=document.createElement('div');grid.className='grid';
  let ready=0;
  for(const item of items){
    if(!/^[a-z_]+$/.test(item.id))continue;
    const status=await fetch('/demos/CharacterStories/'+item.id+'/delivery.json',{cache:'no-store'});
    if(!status.ok)continue;
    ready++;
    const card=document.createElement('section');card.className='card';
    const video=document.createElement('video');video.controls=true;video.preload='none';video.src=item.video;video.poster=item.poster;video.style.width='100%';
    const article=document.createElement('article');const title=document.createElement('h3');title.textContent=item.title;
    const action=document.createElement('p');action.textContent='Action study: '+item.action.replaceAll('_',' ');
    article.append(title,action);card.append(video,article);grid.append(card);
  }
  if(!ready)return;
  const complete=await fetch('/demos/CharacterStories/complete.json',{cache:'no-store'});
  section.append(heading,text);
  if(complete.ok){
    const label=document.createElement('p');label.textContent='Watch all nine short scenes:';
    const video=document.createElement('video');video.controls=true;video.preload='metadata';video.src='/demos/CharacterStories/all-stories.mp4';video.style.cssText='width:100%;max-width:960px;margin-bottom:24px';
    section.append(label,video);
  }
  section.append(grid);document.getElementById('composite-movies').append(section);
})().catch(()=>{});
