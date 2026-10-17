(async () => {
  const response = await fetch('/demos/latest-house.json', {cache:'no-store'});
  if (!response.ok) return;
  const latest = await response.json();
  if (!/^ModernHouse_[0-9_]+$/.test(latest.id)) return;
  const section = document.createElement('section');section.style.order='2';
  section.className = 'panel';
  const heading = document.createElement('h2');
  heading.textContent = 'Modern house — connected interior and exterior';
  const text = document.createElement('p');
  text.textContent = 'One 8 × 6 metre architectural layout with a dining area, built-in kitchen, open entrance, window openings and terrace. Free CC0 wood and plaster maps from Poly Haven. This is a procedural set study; furniture detail, glazing and additional rooms remain future work.';
  const grid = document.createElement('div');
  grid.className = 'grid';
  for (const view of ['interior','exterior']) {
    const card = document.createElement('section');
    card.className = 'card';
    const a = document.createElement('a');
    a.href = '/demos/' + latest.id + '/' + view + '.png';
    a.target = '_blank';
    const img = document.createElement('img');
    img.src = a.href;
    img.alt = 'House ' + view;
    a.append(img);
    const article = document.createElement('article');
    article.textContent = view === 'interior' ? 'Dining and kitchen interior' : 'Matching exterior and terrace';
    card.append(a,article);
    grid.append(card);
  }
  section.append(heading,text,grid);
  document.getElementById('building-studies').append(section);
})().catch(() => {});
