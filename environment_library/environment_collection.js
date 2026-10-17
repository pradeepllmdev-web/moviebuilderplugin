(async () => {
  const response = await fetch('/demos/environment-collection.json', {cache:'no-store'});
  if (!response.ok) return;
  const items = await response.json();
  const section = document.createElement('section');section.style.order='1';
  section.className = 'panel';
  const heading = document.createElement('h2');
  heading.textContent = 'More movie locations';
  const text = document.createElement('p');
  text.textContent = 'Broadleaf woodland, open countryside, and a rocky highland pass. Built from installed scanned vegetation and surfaces; the highland mountains are procedural. These are editable set studies awaiting further art direction.';
  const grid = document.createElement('div');
  grid.className = 'grid';
  for (const item of items) {
    if (!/^\/demos\/[A-Za-z0-9_]+\/preview\.png$/.test(item.preview)) continue;
    const card = document.createElement('section');
    card.className = 'card';
    const link = document.createElement('a');
    link.href = item.preview;
    link.target = '_blank';
    const img = document.createElement('img');
    img.src = item.preview;
    img.alt = item.title;
    link.append(img);
    const article = document.createElement('article');
    const title = document.createElement('h3');
    title.textContent = item.title;
    const level = document.createElement('small');
    level.textContent = item.level;
    article.append(title,level);
    card.append(link,article);
    grid.append(card);
  }
  section.append(heading,text,grid);
  document.getElementById('nature-studies').append(section);
})().catch(() => {});
