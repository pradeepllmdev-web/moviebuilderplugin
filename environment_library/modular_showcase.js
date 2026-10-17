(async () => {
  const r = await fetch('/demos/latest-modular.json', {cache:'no-store'});
  if (!r.ok) return;
  const data = await r.json();
  if (!/^ModularKit_[0-9_]+$/.test(data.id)) return;
  const section = document.createElement('section');section.style.order='6'; section.className='panel';
  const title=document.createElement('h2');title.textContent='Modular environment kit — architecture';
  const text=document.createElement('p');text.textContent='Reusable walls, doors, windows, floors, roofs, corners and stairs assembled from a centimetre-based recipe. Door clearance: 100 × 220 cm. Height references: lion 185 cm and cat 150 cm. This is an architecture blockout; automatic dressing, glazing and full path validation remain future work.';
  const grid=document.createElement('div');grid.className='grid';
  for (const view of ['overview','doorway']) {
    const link=document.createElement('a');link.href='/demos/'+data.id+'/'+view+'.png';link.target='_blank';
    const img=document.createElement('img');img.src=link.href;img.alt='Modular kit '+view;img.style.width='100%';link.append(img);grid.append(link);
  }
  const recipe=document.createElement('a');recipe.href='/demos/'+data.id+'/recipe.json';recipe.textContent='View assembly recipe';recipe.target='_blank';
  section.append(title,text,grid,recipe);document.getElementById('architecture-kit').append(section);
})().catch(console.error);
