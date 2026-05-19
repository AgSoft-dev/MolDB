/* ── DB state & panel navigation ─────────────────────────────────────────── */
let dbLoaded = false;

function showPanel(name) {
  if (name === 'add' && !isAdvancedMode()) {
    return; // Prevent showing add panel if not advanced
  }
  if (name !== 'add' && !dbLoaded) {
    return; // Block browse when no DB is loaded
  }
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.getElementById('panel-' + name).classList.add('active');
  if (name === 'browse') loadBrowse();
}

function isAdvancedMode() {
  return window.localStorage.getItem('advancedMode') === 'true';
}

function setAdvancedMode(enabled) {
  window.localStorage.setItem('advancedMode', enabled ? 'true' : 'false');
  updateAdvancedUI();
}

function updateAdvancedUI() {
  const advanced = isAdvancedMode();
  const addBtn = document.getElementById('add-nav-btn');
  const browseBtn = document.getElementById('browse-nav-btn');
  const statusBtn = document.getElementById('db-status-btn');
  if (addBtn) addBtn.style.display = advanced && dbLoaded ? 'inline-block' : 'none';
  if (browseBtn) browseBtn.style.display = dbLoaded ? 'inline-block' : 'none';
  if (statusBtn) statusBtn.style.display = 'inline-block';
  const advancedActions = document.getElementById('db-advanced-actions');
  if (advancedActions) {
    advancedActions.style.display = isAdvancedMode() ? 'flex' : 'none';
  }
  const createBtn = document.getElementById('db-create-btn');
  const migrateBtn = document.getElementById('db-migrate-btn');
  if (createBtn) {
    createBtn.style.display = isAdvancedMode() && !dbLoaded ? 'inline-block' : 'none';
  }
  if (migrateBtn) {
    migrateBtn.style.display = isAdvancedMode() && dbLoaded && pendingMigrations > 0 ? 'inline-block' : 'none';
  }

  if (!dbLoaded) {
    document.getElementById('search-input-area').style.display = 'none';
    document.getElementById('structure-search-box').style.display = 'none';
    document.getElementById('db-required-notice').style.display = 'block';
  } else {
    document.getElementById('search-input-area').style.display = 'flex';
    document.getElementById('structure-search-box').style.display = 'block';
    document.getElementById('db-required-notice').style.display = 'none';
  }

  // If add panel is active and advanced disabled, switch to browse
  if (!advanced && document.getElementById('panel-add').classList.contains('active')) {
    showPanel('browse');
  }
  // Re-render lists to show/hide delete buttons
  if (document.getElementById('panel-browse').classList.contains('active')) {
    loadBrowse();
  }
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
  // Handle manual path input — trigger on blur or Enter key.
  // Note: the Browse button / file picker cannot provide real filesystem paths
  // due to browser security restrictions. Type the path (relative to app.py's
  // directory, or absolute) directly into the text field.
  const pathInput = document.getElementById('db-path-input');
  if (pathInput) {
    pathInput.addEventListener('change', setDbPath);
    pathInput.addEventListener('keydown', e => {
      if (e.key === 'Enter') { e.preventDefault(); setDbPath(); }
    });
  }

  // Advanced mode
  const advancedCheckbox = document.getElementById('advanced-mode');
  if (advancedCheckbox) {
    advancedCheckbox.checked = isAdvancedMode();
    advancedCheckbox.addEventListener('change', e => {
      setAdvancedMode(e.target.checked);
    });
  }
  refreshDbStatus();
  updateAdvancedUI();
});

function setDbReady(ready) {
  dbLoaded = ready;
  const statusBtn = document.getElementById('db-status-btn');
  if (!statusBtn) return;
  if (ready) {
    statusBtn.textContent = 'DB online';
    statusBtn.classList.remove('offline');
    statusBtn.classList.add('online');
    statusBtn.title = 'Database is loaded';
  } else {
    statusBtn.textContent = 'DB offline';
    statusBtn.classList.remove('online');
    statusBtn.classList.add('offline');
    statusBtn.title = 'No database loaded';
  }
  updateAdvancedUI();
}

async function refreshDbStatus() {
  try {
    const data = await api('/db/path');
    const path = data?.path || '';
    if (path) {
      document.getElementById('db-path-input').value = path;
      document.getElementById('db-path-result').textContent = `✓ Using: ${path}`;
      setDbReady(true);
      await refreshMigrationStatus();
    } else {
      setDbReady(false);
    }
  } catch (e) {
    setDbReady(false);
    document.getElementById('db-path-result').textContent = `DB offline: ${escHtml(e.message)}`;
  }
}

let pendingMigrations = 0;

async function refreshMigrationStatus() {
  if (!dbLoaded) {
    pendingMigrations = 0;
    updateAdvancedUI();
    return;
  }
  try {
    const status = await api('/db/migrate');
    pendingMigrations = status.pending || 0;
  } catch (e) {
    pendingMigrations = 0;
  }
  const migrateBtn = document.getElementById('db-migrate-btn');
  if (migrateBtn) {
    if (pendingMigrations > 0) {
      migrateBtn.textContent = `${pendingMigrations} migration available, click to apply`;
    } else {
      migrateBtn.textContent = 'No migrations pending';
    }
  }
  updateAdvancedUI();
}

function ensureSqliteExt(p) {
  if (!p) return p;
  return p.endsWith('.sqlite') || p.endsWith('.db') ? p : p + '.sqlite';
}

async function createDb() {
  const input = document.getElementById('db-path-input');
  const result = document.getElementById('db-path-result');
  // Default to a timestamped name if the field is blank
  let path = input.value.trim();
  if (!path) {
    const ts = new Date().toISOString().slice(0,10); // e.g. 2025-05-19
    path = `molecules_${ts}.sqlite`;
  }
  path = ensureSqliteExt(path);
  input.value = path; // reflect normalised name back into the field
  try {
    const data = await api('/db/path', {
      method: 'POST',
      body: JSON.stringify({ path, create: true, migrate: false }),
    });
    location.reload();
  } catch (e) {
    setDbReady(false);
    result.textContent = `Failed to create DB: ${escHtml(e.message)}`;
  }
}

async function applyMigration() {
  const result = document.getElementById('db-path-result');
  try {
    const status = await api('/db/migrate', { method: 'POST' });
    pendingMigrations = status.pending || 0;
    if (pendingMigrations === 0) {
      result.textContent = 'Migration applied successfully.';
    } else {
      result.textContent = `Still ${pendingMigrations} migrations pending.`;
    }
  } catch (e) {
    result.textContent = `Migration failed: ${escHtml(e.message)}`;
  }
  await refreshMigrationStatus();
}

async function setDbPath() {
  const input = document.getElementById('db-path-input');
  const result = document.getElementById('db-path-result');
  let path = input.value.trim();
  if (!path) {
    result.textContent = 'Please enter a database path.';
    return;
  }
  path = ensureSqliteExt(path);
  input.value = path;
  try {
    const data = await api('/db/path', {
      method: 'POST',
      body: JSON.stringify({ path, create: false, migrate: false }),
    });
    location.reload();
  } catch (e) {
    setDbReady(false);
    result.textContent = `Failed to set DB: ${escHtml(e.message)}`;
  }
}

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
  const advanced = isAdvancedMode();
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
        ${advanced ? `<button class="secondary" onclick="editMol(${m.id})">Edit</button> <button class="danger" onclick="deleteMol(${m.id})">Delete</button>` : ''}
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

const PAGE_SIZE = 20;
let activeResults = [];
let currentPage = 1;

function getPageCount() {
  return Math.max(1, Math.ceil(activeResults.length / PAGE_SIZE));
}

function renderPagination() {
  const pagination = document.getElementById('browse-pagination');
  if (!pagination) return;
  const pageCount = getPageCount();
  if (pageCount <= 1) {
    pagination.innerHTML = '';
    return;
  }
  pagination.innerHTML = `
    <div class="pagination-controls">
      <button class="secondary" ${currentPage === 1 ? 'disabled' : ''} onclick="changePage(${currentPage - 1})">Prev</button>
      <span>Page ${currentPage} / ${pageCount}</span>
      <button class="secondary" ${currentPage === pageCount ? 'disabled' : ''} onclick="changePage(${currentPage + 1})">Next</button>
    </div>
  `;
}

function renderPage(getScore = null) {
  if (currentPage < 1) currentPage = 1;
  const pageCount = getPageCount();
  if (currentPage > pageCount) currentPage = pageCount;
  const start = (currentPage - 1) * PAGE_SIZE;
  const pageItems = activeResults.slice(start, start + PAGE_SIZE);
  renderList('browse-results', pageItems, getScore);
  renderPagination();
}

function changePage(page) {
  const pageCount = getPageCount();
  if (page < 1 || page > pageCount) return;
  currentPage = page;
  renderPage();
}

/* ── Text search ──────────────────────────────────────────────────────────── */
let searchTimeout;
document.getElementById('search-input').addEventListener('input', () => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(doSearch, 300); // Debounce search
});

async function doSearch() {
  if (!dbLoaded) {
    showError('browse-results', 'Database not loaded. Select a valid SQLite file first.');
    return;
  }
  const q = document.getElementById('search-input').value.trim();
  if (!q) {
    await loadBrowse();
    return;
  }
  try {
    const results = await api(`/search?q=${encodeURIComponent(q)}`);
    currentResults = results;
    activeResults = results;
    currentPage = 1;
    renderPage();
  } catch (e) { showError('browse-results', e.message); }
}

/* ── Structure search ─────────────────────────────────────────────────────── */
async function doStructureSearch() {
  if (!dbLoaded) {
    showError('browse-results', 'Database not loaded. Select a valid SQLite file first.');
    return;
  }
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
    currentResults = results.map(r => r.molecule);
    activeResults = currentResults;
    currentPage = 1;
    renderPage(m => scoreMap[m.id]);
  } catch (e) { showError('browse-results', e.message); }
}

/* ── Global state ─────────────────────────────────────────────────────────── */
let editMode = null; // null or {id: number}
let currentResults = []; // For filtering

/* ── Edit molecule ─────────────────────────────────────────────────────────── */
async function editMol(id) {
  try {
    const mol = await api(`/molecules/${id}`);
    // Populate form
    document.getElementById('add-name').value = mol.name || '';
    document.getElementById('add-smiles').value = mol.smiles || '';
    document.getElementById('add-cas').value = mol.cas_number || '';
    document.getElementById('add-project').value = mol.project || '';
    document.getElementById('add-notes').value = mol.notes || '';
    // Switch to add panel
    showPanel('add');
    // Set edit mode
    editMode = { id };
    document.getElementById('submit-btn').textContent = 'Update Molecule';
    document.getElementById('cancel-btn').style.display = 'inline-block';
    document.getElementById('add-result').innerHTML = `<p>Editing molecule ID ${id}</p>`;
  } catch (e) {
    alert('Failed to load molecule for editing: ' + e.message);
  }
}

function cancelEdit() {
  editMode = null;
  document.getElementById('submit-btn').textContent = 'Save Molecule';
  document.getElementById('cancel-btn').style.display = 'none';
  document.getElementById('add-result').innerHTML = '';
  // Clear form
  ['add-name','add-smiles','add-cas','add-project','add-notes'].forEach(id => {
    document.getElementById(id).value = '';
  });
}
/* ── Add/Update molecule ───────────────────────────────────────────────────── */
async function submitAddOrUpdate() {
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
    let mol;
    if (editMode) {
      // Update
      mol = await api(`/molecules/${editMode.id}`, { method: 'PUT', body: JSON.stringify(payload) });
      document.getElementById('add-result').innerHTML = `<p class="ok">✓ Updated: <strong>${escHtml(mol.name)}</strong> (id=${mol.id})</p>`;
      // Reset edit mode
      editMode = null;
      document.getElementById('submit-btn').textContent = 'Save Molecule';
      document.getElementById('cancel-btn').style.display = 'none';
      // Clear form
      ['add-name','add-smiles','add-cas','add-project','add-notes'].forEach(id => {
        document.getElementById(id).value = '';
      });
      // Refresh lists if needed
      if (document.getElementById('panel-browse').classList.contains('active')) {
        loadBrowse();
      }
    } else {
      // Add
      mol = await api('/molecules', { method: 'POST', body: JSON.stringify(payload) });
      document.getElementById('add-result').innerHTML = `<p class="ok">✓ Saved: <strong>${escHtml(mol.name)}</strong> (id=${mol.id})</p>`;
      // Clear form
      ['add-name','add-smiles','add-cas','add-project','add-notes'].forEach(id => {
        document.getElementById(id).value = '';
      });
    }
  } catch (e) {
    document.getElementById('add-result').innerHTML = `<p class="err">✗ ${escHtml(e.message)}</p>`;
  }
}

/* ── Browse all ────────────────────────────────────────────────────── */
async function loadBrowse() {
  try {
    currentResults = await api('/molecules?limit=10000'); // Load more for pagination
    activeResults = currentResults;
    currentPage = 1;
    renderPage();
  } catch (e) { showError('browse-results', e.message); }
}

/* ── Delete ───────────────────────────────────────────────────────────────── */
async function deleteMol(id) {
  if (!confirm('Delete this molecule?')) return;
  try {
    await api(`/molecules/${id}`, { method: 'DELETE' });
    currentResults = currentResults.filter(m => m.id !== id);
    activeResults = activeResults.filter(m => m.id !== id);
    renderPage();
  } catch (e) { alert(e.message); }
}

/* ── Helpers ──────────────────────────────────────────────────────────────── */
function showError(containerId, msg) {
  document.getElementById(containerId).innerHTML = `<p class="err">Error: ${escHtml(msg)}</p>`;
}