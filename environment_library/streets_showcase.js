(async () => {
  const r = await fetch('/demos/latest-streets.json', {cache:'no-store'});
  if (!r.ok) return;
  const data = await r.json();
  if (!/^StreetKit_[0-9_]+$/.test(data.id)) return;
  const section = document.createElement('section');section.style.order='7'; section.className='panel';
  const title=document.createElement('h2');title.textContent='Modular environment kit — architecture';
  const text=document.createElement('p');text.textContent='Connected straight roads, corners, T-junctions and crossroads. Two 3.5 metre lanes, 1.5 metre pavements and junction crossings. The demo has eight matched connections and four open ends. Traffic, curb ramps and navigation remain future work';
  const grid=document.createElement('div');grid.className='grid';
  for (const view of ['overview','street']) {
    const link=document.createElement('a');link.href='/demos/'+data.id+'/'+view+'.png';link.target='_blank';
    const img=document.createElement('img');img.src=link.href;img.alt='Street kit '+view;img.style.width='100%';link.append(img);grid.append(link);
  }
  const recipe=document.createElement('a');recipe.href='/demos/'+data.id+'/recipe.json';recipe.textContent='View assembly recipe';recipe.target='_blank';
  section.append(title,text,grid,recipe);document.getElementById('street-kit').append(section);
})().catch(console.error);
