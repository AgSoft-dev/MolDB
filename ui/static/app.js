/* ── Panel navigation ──────────────────────────────────────────────────────── */
function showPanel(name) {
  if (name === 'add' && !isAdvancedMode()) {
    return; // Prevent showing add panel if not advanced
  }
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.getElementById('panel-' + name).classList.add('active');
  if (name === 'list') loadList();
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
  if (addBtn) addBtn.style.display = advanced ? 'inline-block' : 'none';
  // If add panel is active and advanced disabled, switch to search
  if (!advanced && document.getElementById('panel-add').classList.contains('active')) {
    showPanel('search');
  }
  // Re-render lists to show/hide delete buttons
  if (document.getElementById('panel-list').classList.contains('active')) {
    loadList();
  }
  if (document.getElementById('panel-search').classList.contains('active')) {
    // Toggle delete visibility on existing search results
    document.querySelectorAll('.mol-card button.danger').forEach(btn => {
      btn.style.display = advanced ? 'inline-block' : 'none';
    });
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
  loadDbPath();

  // Handle file selection for DB path
  const fileInput = document.getElementById('db-file-input');
  if (fileInput) {
    fileInput.addEventListener('change', e => {
      const file = e.target.files[0];
      if (file) {
        document.getElementById('db-path-input').value = file.name;
        setDbPath();  // Automatically set the DB path
      }
    });
  }

  // Handle manual path input
  const pathInput = document.getElementById('db-path-input');
  if (pathInput) {
    pathInput.addEventListener('change', setDbPath);
  }

  // Advanced mode
  const advancedCheckbox = document.getElementById('advanced-mode');
  if (advancedCheckbox) {
    advancedCheckbox.checked = isAdvancedMode();
    advancedCheckbox.addEventListener('change', e => {
      setAdvancedMode(e.target.checked);
    });
  }
  updateAdvancedUI();
});

function getStoredDbPath() {
  return window.localStorage.getItem('moldb_db_path') || '';
}

function setStoredDbPath(path) {
  window.localStorage.setItem('moldb_db_path', path);
}

async function loadDbPath() {
  const savedPath = getStoredDbPath();
  const input = document.getElementById('db-path-input');
  if (!input) return;
  input.value = savedPath;
  if (savedPath) {
    document.getElementById('db-path-result').textContent = `Saved path: ${savedPath}`;
  }
}

async function setDbPath() {
  const input = document.getElementById('db-path-input');
  const result = document.getElementById('db-path-result');
  const path = input.value.trim();
  if (!path) {
    result.textContent = 'Please enter a database path.';
    return;
  }
  try {
    await api('/db/path', {
      method: 'POST',
      body: JSON.stringify({ path }),
    });
    setStoredDbPath(path);
    result.textContent = `Using DB: ${path}`;
  } catch (e) {
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

/* ── Text search ──────────────────────────────────────────────────────────── */
let searchTimeout;
document.getElementById('search-input').addEventListener('input', () => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(doSearch, 300); // Debounce search
});

async function doSearch() {
  const q = document.getElementById('search-input').value.trim();
  if (!q) {
    document.getElementById('search-results').innerHTML = '';
    return;
  }
  try {
    const results = await api(`/search?q=${encodeURIComponent(q)}`);
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

/* ── Global state ─────────────────────────────────────────────────────────── */
let editMode = null; // null or {id: number}
let allMols = []; // For list filtering

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
      if (document.getElementById('panel-list').classList.contains('active')) {
        loadList();
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

/* ── List all ─────────────────────────────────────────────────────────────── */
async function loadList() {
  try {
    allMols = await api('/molecules?limit=10000'); // Load more for filtering
    document.getElementById('list-search-input').value = '';
    renderList('list-results', allMols);
  } catch (e) { showError('list-results', e.message); }
}

/* ── List filtering ───────────────────────────────────────────────────────── */
let listFilterTimeout;
document.getElementById('list-search-input').addEventListener('input', () => {
  clearTimeout(listFilterTimeout);
  listFilterTimeout = setTimeout(filterList, 300);
});

function filterList() {
  const q = document.getElementById('list-search-input').value.trim().toLowerCase();
  if (!q) {
    renderList('list-results', allMols);
    return;
  }
  const filtered = allMols.filter(m =>
    (m.name || '').toLowerCase().includes(q) ||
    (m.cas_number || '').toLowerCase().includes(q) ||
    (m.smiles || '').toLowerCase().includes(q) ||
    (m.project || '').toLowerCase().includes(q) ||
    (m.notes || '').toLowerCase().includes(q)
  );
  renderList('list-results', filtered);
}

function clearListFilter() {
  document.getElementById('list-search-input').value = '';
  renderList('list-results', allMols);
}

/* ── Delete ───────────────────────────────────────────────────────────────── */
async function deleteMol(id) {
  if (!confirm('Delete this molecule?')) return;
  try {
    await api(`/molecules/${id}`, { method: 'DELETE' });
    allMols = allMols.filter(m => m.id !== id);
    document.getElementById('mol-' + id)?.remove();
  } catch (e) { alert(e.message); }
}

/* ── Helpers ──────────────────────────────────────────────────────────────── */
function showError(containerId, msg) {
  document.getElementById(containerId).innerHTML = `<p class="err">Error: ${escHtml(msg)}</p>`;
}