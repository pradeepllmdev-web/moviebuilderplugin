(async()=>{
 const response=await fetch('/demos/latest-scale-check.json',{cache:'no-store'});if(!response.ok)return;
 const latest=await response.json();if(!/^ScaleCheck_[0-9_]+$/.test(latest.id))return;
 const base='/demos/'+latest.id+'/';const details=await fetch(base+'build-result.json');if(!details.ok)return;
 const report=await details.json();const section=document.createElement('section');section.style.order='8';section.className='panel';
 const title=document.createElement('h2');title.textContent='Real-world scale check';
 const text=document.createElement('p');text.textContent='Lion 185 cm · cat 150 cm · doorway 100 × 220 cm · ruler 200 cm · table 75 cm · chair 90 cm overall. These objects share one Unreal level and real centimetre dimensions. The background building is three storeys, '+(report.building_height_cm/100).toFixed(1)+' m tall; the tree retains its imported '+(report.tree_native_height_cm/100).toFixed(1)+' m height.';
 const grid=document.createElement('div');grid.className='grid';
 for(const [view,label] of [['character_height','Character-height comparison'],['wide','Building and tree comparison']]){
  const card=document.createElement('section');card.className='card';const a=document.createElement('a');a.href=base+view+'.png';a.target='_blank';
  const img=document.createElement('img');img.src=a.href;img.alt=label;a.append(img);const article=document.createElement('article');article.textContent=label;card.append(a,article);grid.append(card);
 }
 const note=document.createElement('p');note.textContent='Shared pack conversions preserve object proportions and relative sizes. Reference floor counts are editable defaults, not inferred measurements. Seat/handle anchors and runtime foot IK still need separate authoring.';
 section.append(title,text,grid,note);document.getElementById('scale-tests').append(section);
})().catch(()=>{});
