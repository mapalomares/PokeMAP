let pokemonRows = [];

const resultEl = document.getElementById('result');
const errorEl = document.getElementById('error');
const inputEl = document.getElementById('pokemonName');
const btnEl = document.getElementById('searchBtn');

const usageText = {
  pve: 'Excelente para contenido PvE (raids offline)',
  pvp_gl: 'Muy bueno para PvP Gran Liga',
  pvp_ul: 'Excelente para PvP Ultra Liga',
  raid: 'Ahora mismo aparece en raids',
  coleccionable: 'Principalmente para colección'
};

function csvToRows(text) {
  const rows = [];
  let cur = '';
  let inQuotes = false;
  let row = [];

  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];

    if (ch === '"') {
      if (inQuotes && text[i + 1] === '"') {
        cur += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (ch === ',' && !inQuotes) {
      row.push(cur);
      cur = '';
    } else if ((ch === '\n' || ch === '\r') && !inQuotes) {
      if (ch === '\r' && text[i + 1] === '\n') i += 1;
      if (cur.length || row.length) {
        row.push(cur);
        rows.push(row);
      }
      row = [];
      cur = '';
    } else {
      cur += ch;
    }
  }

  if (cur.length || row.length) {
    row.push(cur);
    rows.push(row);
  }

  const headers = rows[0] || [];
  return rows.slice(1).map((r) => {
    const obj = {};
    headers.forEach((h, idx) => {
      obj[h] = r[idx] || '';
    });
    return obj;
  });
}

function scoreClass(score) {
  const s = Number(score || 0);
  if (s >= 80) return 'high';
  if (s >= 60) return 'mid';
  if (s >= 40) return 'low';
  return 'bad';
}

function scoreRow(label, value) {
  const cls = scoreClass(value);
  const safe = Number(value || 0);
  return `
    <div class="score">
      <strong>${label}</strong>
      <div class="bar"><div class="fill ${cls}" style="width:${safe}%;"></div></div>
      <span>${safe}/100</span>
    </div>
  `;
}

function tagList(raw) {
  if (!raw) return '<span class="tag">sin etiquetas</span>';
  return raw
    .split(',')
    .map((x) => x.trim())
    .filter(Boolean)
    .map((x) => `<span class="tag">${x}</span>`)
    .join('');
}

function findPokemon(query) {
  const q = query.trim().toLowerCase();
  if (!q) return { type: 'error', msg: 'Escribe un nombre de Pokémon.' };

  const exact = pokemonRows.find((r) => (r.Nombre || '').toLowerCase() === q);
  if (exact) return { type: 'ok', row: exact };

  const partial = pokemonRows.filter((r) => (r.Nombre || '').toLowerCase().includes(q));
  if (partial.length === 0) return { type: 'error', msg: `No encontré resultados para "${query}".` };
  if (partial.length > 1) {
    const names = partial.slice(0, 10).map((r) => r.Nombre).join(', ');
    return { type: 'error', msg: `Hay varias coincidencias: ${names}` };
  }
  return { type: 'ok', row: partial[0] };
}

function render(row) {
  const evolutionCost = row.CosteCaramelosEvolucionRecomendada
    ? `${row.CosteCaramelosEvolucionRecomendada} caramelos`
    : 'n/a';

  const evoItem = row.ObjetosEvolucionRecomendada || 'ninguno';
  const evoTarget = row.EvolucionRecomendada || 'mantener actual';
  const evoUse = row.UsoEvolucionRecomendada ? (usageText[row.UsoEvolucionRecomendada] || row.UsoEvolucionRecomendada) : 'sin mejora clara';

  resultEl.innerHTML = `
    <h2 class="result-title">${row.Nombre}</h2>
    <p class="kicker">${row.Tipo} · ${row.CategoriaGO} · uso principal: ${usageText[row.UsoPrincipal] || row.UsoPrincipal}</p>

    <div class="grid">
      <article class="panel">
        <h3>Clasificación</h3>
        <p class="kv"><strong>Nivel base:</strong> ${row.NivelBase}</p>
        <p class="kv"><strong>Etiquetas:</strong> ${tagList(row.EtiquetasGO)}</p>
        <p class="kv"><strong>Bebé:</strong> ${row.esBebe}</p>
        <p class="kv"><strong>Región:</strong> ${row.Region || 'global'}</p>
        <p class="kv"><strong>En raids:</strong> ${row.EsRaid}</p>
      </article>

      <article class="panel">
        <h3>Stats Base</h3>
        <p class="kv"><strong>Ataque:</strong> ${row['Ataque Base']}</p>
        <p class="kv"><strong>Defensa:</strong> ${row['Defensa Base']}</p>
        <p class="kv"><strong>Stamina:</strong> ${row['Stamina Base']}</p>
        <p class="kv"><strong>Contadores:</strong> ${row.Contadores || '—'}</p>
      </article>

      <article class="panel">
        <h3>Utilidad</h3>
        ${scoreRow('PvE', row.ScorePvE)}
        ${scoreRow('PvP GL', row.ScorePvP_GL)}
        ${scoreRow('PvP UL', row.ScorePvP_UL)}
      </article>

      <article class="panel">
        <h3>Evolución Recomendada</h3>
        <p class="kv"><strong>Evoluciona a:</strong> ${row.EvolucionaA || '—'}</p>
        <p class="kv"><strong>Objetivo:</strong> ${evoTarget}</p>
        <p class="kv"><strong>Uso tras evolucionar:</strong> ${evoUse}</p>
        <p class="kv"><strong>Score objetivo:</strong> ${row.ScoreEvolucionRecomendada || '—'}</p>
        <p class="kv"><strong>Coste:</strong> ${evolutionCost}</p>
        <p class="kv"><strong>Objeto:</strong> ${evoItem}</p>
      </article>
    </div>
  `;

  resultEl.classList.remove('hidden');
  errorEl.classList.add('hidden');
}

function renderError(msg) {
  errorEl.textContent = msg;
  errorEl.classList.remove('hidden');
  resultEl.classList.add('hidden');
}

function onSearch() {
  const found = findPokemon(inputEl.value);
  if (found.type === 'error') {
    renderError(found.msg);
    return;
  }
  render(found.row);
}

async function boot() {
  try {
    const resp = await fetch('./data/pokeMAP.csv');
    const csv = await resp.text();
    pokemonRows = csvToRows(csv);
  } catch (err) {
    renderError('No pude cargar la base de datos local.');
    return;
  }

  btnEl.addEventListener('click', onSearch);
  inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') onSearch();
  });

  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('./sw.js').catch(() => {});
  }
}

boot();
