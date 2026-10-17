// Show the latest completed scanned river set without changing the build workflow.
(async () => {
  const response = await fetch('/demos/latest-realistic-river.json', {cache: 'no-store'});
  if (!response.ok) return;
  const latest = await response.json();
  if (!/^RealisticRiver_[0-9_]+$/.test(latest.id)) return;
  const base = '/demos/' + latest.id + '/';
  const section = document.createElement('section');section.style.order='0';
  section.className = 'panel';
  const heading = document.createElement('h2');
  heading.textContent = 'Scanned forest and river — realistic set study';
  const description = document.createElement('p');
  description.textContent = 'Existing scanned trees, rocks and ground surfaces, layered shoreline vegetation, and clearer daylight. Inspect the three views and short editor camera study. This is a work-in-progress set, not a final film render.';
  const grid = document.createElement('div');
  grid.className = 'grid';
  for (const [file, label] of [['wide', 'Wide view'], ['character_height', 'Character height'], ['river_detail', 'Riverbank detail']]) {
    const card = document.createElement('figure');
    const link = document.createElement('a');
    link.href = base + file + '.png';
    link.target = '_blank';
    const img = document.createElement('img');
    img.src = link.href;
    img.alt = label;
    img.style.width = '100%';
    link.append(img);
    const caption = document.createElement('figcaption');
    caption.textContent = label;
    card.append(link, caption);
    grid.append(card);
  }
  const video = document.createElement('video');
  video.controls = true;
  video.preload = 'metadata';
  video.src = base + 'camera-study.mp4';
  video.poster = base + 'character_height.png';
  video.style.cssText = 'width:100%;max-width:960px;margin-top:20px';
  section.append(heading, description, grid, video);
  document.getElementById('nature-studies').append(section);
})().catch(() => {});
