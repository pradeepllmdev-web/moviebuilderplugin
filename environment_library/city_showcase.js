(async () => {
  const response = await fetch('/demos/latest-city.json',{cache:'no-store'});
  if (!response.ok) return;
  const latest = await response.json();
  if (!/^SkyscraperCity_[0-9_]+$/.test(latest.id)) return;
  const section = document.createElement('section');section.style.order='3';section.className='panel';
  const heading = document.createElement('h2');heading.textContent='Skyscraper city — 600 metre landmark';
  const text = document.createElement('p');
  text.textContent='25 procedural towers with a stepped landmark, façade grids, rooftop equipment and street corridors. Skyline and pedestrian-height views share the same saved level. This is a scale and layout study; detailed architecture, storefronts, traffic and crowds remain to be added.';
  const grid = document.createElement('div');grid.className='grid';
  for (const view of ['skyline','street']) {
    const card=document.createElement('section');card.className='card';
    const a=document.createElement('a');a.href='/demos/'+latest.id+'/'+view+'.png';a.target='_blank';
    const img=document.createElement('img');img.src=a.href;img.alt=view==='skyline'?'City skyline':'Street-level view looking up';
    a.append(img);const article=document.createElement('article');article.textContent=img.alt;
    card.append(a,article);grid.append(card);
  }
  section.append(heading,text,grid);document.getElementById('building-studies').append(section);
})().catch(()=>{});
