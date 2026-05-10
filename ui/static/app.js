/* ── Panel navigation ──────────────────────────────────────────────────────── */
function showPanel(name) {
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.getElementById('panel-' + name).classList.add('active');
  if (name === 'list') loadList();
}

/* ── Ketcher iframe API helpers ───────────────────────────────────────────── */
// Ketcher exposes an async API on iframe.contentWindow.ketcher.
// It is only available after the iframe has fully loaded.

function getKetcher(iframeId) {
  const frame = document.getElementById(iframeId);
  if (!frame || !frame.contentWindow || !frame.contentWindow.ketcher) {
    alert('Ketcher editor is still loading — please wait a moment and try again.');
    return null;
  }
  return frame.contentWindow.ketcher;
}

async function getSmiles(iframeId) {
  const ketcher = getKetcher(iframeId);
  if (!ketcher) return null;
  try {
    const smiles = await ketcher.getSmiles();
    if (!smiles || smiles.trim() === '') {
      alert('No molecule drawn. Please draw a structure first.');
      return null;
    }
    return smiles.trim();
  } catch (e) {
    console.error('Ketcher getSmiles error:', e);
    alert('Could not export SMILES: ' + e.message);
    return null;
  }
}

async function importSmilesFromDrawing() {
  const smiles = await getSmiles('ketcher-add');
  if (smiles) document.getElementById('add-smiles').value = smiles;
}

/* ── Slider ───────────────────────────────────────────────────────────────── */
window.addEventListener('load', () => {
  const slider = document.getElementById('threshold');
  slider.addEventListener('input', e => {
    document.getElementById('threshold-val').textContent = e.target.value;
  });
});

/* ── API helpers ──────────────────────────────────────────────────────────── */
async function api(path, opts = {}) {
  const res = await fetch('/api' + path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.status === 204 ? null : res.json();
}

/* ── Render helpers ───────────────────────────────────────────────────────── */
function molCard(m, score = null) {
  return `
    <div class="mol-card" id="mol-${m.id}">
      <div class="mol-svg">${m.svg_cache || '<span class="no-struct">No structure</span>'}</div>
      <div class="mol-info">
        <strong class="mol-name">${escHtml(m.name)}</strong>
        ${m.cas_number ? `<span class="badge">CAS ${escHtml(m.cas_number)}</span>` : ''}
        ${m.project ? `<span class="badge">Project ${escHtml(m.project)}</span>` : ''}
        <span>Formula: <code>${m.molecular_formula ?? '—'}</code></span>
        <span>MW: ${m.molecular_weight ?? '—'} g/mol</span>
        <small class="smiles">${escHtml(m.smiles)}</small>
        ${score !== null ? `<span class="score">Tanimoto: ${score.toFixed(3)}</span>` : ''}
        ${m.notes ? `<p class="notes">${escHtml(m.notes)}</p>` : ''}
        <button class="danger" onclick="deleteMol(${m.id})">Delete</button>
      </div>
    </div>`;
}

function escHtml(s) {
  return String(s).replace(/[&<>"']/g, c =>
    ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

function renderList(selector, mols, getScore = null) {
  const el = document.getElementById(selector);
  if (!mols.length) { el.innerHTML = '<p class="empty">No results found.</p>'; return; }
  el.innerHTML = mols.map(m => molCard(m, getScore ? getScore(m) : null)).join('');
}

/* ── Text search ──────────────────────────────────────────────────────────── */
async function doSearch() {
  const q    = document.getElementById('search-input').value.trim();
  const type = document.getElementById('search-type').value;
  if (!q) return;
  try {
    const results = await api(`/search?${type}=${encodeURIComponent(q)}`);
    renderList('search-results', results);
  } catch (e) { showError('search-results', e.message); }
}

/* ── Structure search ─────────────────────────────────────────────────────── */
async function doStructureSearch() {
  const smiles = await getSmiles('ketcher-search');
  if (!smiles) return;
  const threshold = parseFloat(document.getElementById('threshold').value);
  const mode = document.querySelector('input[name="smode"]:checked').value;
  try {
    const results = await api('/search/structure', {
      method: 'POST',
      body: JSON.stringify({ smiles, threshold, mode }),
    });
    const scoreMap = {};
    results.forEach(r => { scoreMap[r.molecule.id] = r.score; });
    renderList('search-results', results.map(r => r.molecule), m => scoreMap[m.id]);
  } catch (e) { showError('search-results', e.message); }
}

/* ── Add molecule ─────────────────────────────────────────────────────────── */
async function submitAdd() {
  const payload = {
    name:       document.getElementById('add-name').value.trim(),
    smiles:     document.getElementById('add-smiles').value.trim(),
    cas_number: document.getElementById('add-cas').value.trim() || null,
    project:    document.getElementById('add-project').value.trim() || null,
    notes:      document.getElementById('add-notes').value.trim() || null,
  };
  if (!payload.name || !payload.smiles) {
    document.getElementById('add-result').innerHTML = '<p class="err">Name and SMILES are required.</p>';
    return;
  }
  try {
    const mol = await api('/molecules', { method: 'POST', body: JSON.stringify(payload) });
    document.getElementById('add-result').innerHTML =
      `<p class="ok">✓ Saved: <strong>${escHtml(mol.name)}</strong> (id=${mol.id})</p>`;
    ['add-name','add-smiles','add-cas','add-project','add-notes'].forEach(id => {
      document.getElementById(id).value = '';
    });
  } catch (e) {
    document.getElementById('add-result').innerHTML = `<p class="err">✗ ${escHtml(e.message)}</p>`;
  }
}

/* ── List all ─────────────────────────────────────────────────────────────── */
async function loadList() {
  try {
    const mols = await api('/molecules?limit=200');
    renderList('list-results', mols);
  } catch (e) { showError('list-results', e.message); }
}

/* ── Delete ───────────────────────────────────────────────────────────────── */
async function deleteMol(id) {
  if (!confirm('Delete this molecule?')) return;
  try {
    await api(`/molecules/${id}`, { method: 'DELETE' });
    document.getElementById('mol-' + id)?.remove();
  } catch (e) { alert(e.message); }
}

/* ── Helpers ──────────────────────────────────────────────────────────────── */
function showError(containerId, msg) {
  document.getElementById(containerId).innerHTML = `<p class="err">Error: ${escHtml(msg)}</p>`;
}