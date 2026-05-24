const COMMONS_FILE_URL = 'https://commons.wikimedia.org/wiki/Special:FilePath/';

/**
 * Creates an audio player for a Wikimedia Commons file.
 * Uses only safe DOM methods — no innerHTML.
 *
 * @param {object} example    - { file, title, artist, source }
 * @param {string} trackColor - hex color for play button
 * @returns {HTMLElement}
 */
export function createAudioPlayer(example, trackColor) {
  const audio = new Audio(`${COMMONS_FILE_URL}${encodeURIComponent(example.file)}`);

  const container = document.createElement('div');
  container.className = 'audio-player';

  const btn = document.createElement('button');
  btn.className = 'audio-play-btn';
  btn.style.background = `${trackColor}33`;
  btn.style.color = trackColor;
  btn.textContent = '▶';

  const info = document.createElement('div');
  info.style.cssText = 'flex:1;min-width:0;';

  const titleEl = document.createElement('div');
  titleEl.style.cssText = 'color:#e6edf3;font-size:11px;font-weight:bold;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;';
  titleEl.textContent = example.title;

  const metaEl = document.createElement('div');
  metaEl.style.cssText = 'color:#555;font-size:10px;margin-top:2px;';
  metaEl.textContent = example.artist;

  const link = document.createElement('a');
  link.href = `https://commons.wikimedia.org/wiki/File:${encodeURIComponent(example.file)}`;
  link.target = '_blank';
  link.rel = 'noopener noreferrer';
  link.style.cssText = 'color:#4fc3f7;font-size:10px;flex-shrink:0;';
  link.textContent = 'Commons ↗';

  info.appendChild(titleEl);
  info.appendChild(metaEl);
  container.appendChild(btn);
  container.appendChild(info);
  container.appendChild(link);

  let playing = false;
  btn.addEventListener('click', () => {
    if (playing) { audio.pause(); btn.textContent = '▶'; }
    else         { audio.play(); btn.textContent = '⏸'; }
    playing = !playing;
  });
  audio.addEventListener('ended', () => { btn.textContent = '▶'; playing = false; });

  container._pauseAudio = () => { audio.pause(); playing = false; btn.textContent = '▶'; };
  return container;
}
