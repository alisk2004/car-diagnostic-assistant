const state = {
  selectedSymptoms: new Set(),
  selectedCodes: new Map(), // code -> description
};

function $(selector) { return document.querySelector(selector); }
function $all(selector) { return document.querySelectorAll(selector); }

function initTabs() {
  $all('.tab-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      $all('.tab-btn').forEach((b) => b.classList.remove('active'));
      $all('.tab-panel').forEach((p) => p.classList.remove('active'));
      btn.classList.add('active');
      $(`#tab-${btn.dataset.tab}`).classList.add('active');
      if (btn.dataset.tab === 'history') loadHistory();
    });
  });
}

function updateSelectionSummary() {
  $('#selected-symptom-count').textContent = state.selectedSymptoms.size;
  $('#selected-code-count').textContent = state.selectedCodes.size;
}

async function loadSymptoms() {
  const res = await fetch('/api/symptoms');
  const grouped = await res.json();
  const container = $('#symptom-groups');
  container.innerHTML = '';

  Object.keys(grouped).sort().forEach((category) => {
    const section = document.createElement('div');
    section.className = 'symptom-category';
    const heading = document.createElement('h3');
    heading.textContent = category;
    section.appendChild(heading);

    const list = document.createElement('div');
    list.className = 'symptom-list';
    grouped[category].forEach((symptom) => {
      const label = document.createElement('label');
      label.className = 'symptom-item';
      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.value = symptom.id;
      checkbox.addEventListener('change', () => {
        if (checkbox.checked) state.selectedSymptoms.add(symptom.id);
        else state.selectedSymptoms.delete(symptom.id);
        updateSelectionSummary();
      });
      label.appendChild(checkbox);
      label.appendChild(document.createTextNode(symptom.name));
      list.appendChild(label);
    });
    section.appendChild(list);
    container.appendChild(section);
  });
}

async function searchCodes(query) {
  const res = await fetch(`/api/dtc-codes?query=${encodeURIComponent(query || '')}`);
  const codes = await res.json();
  const container = $('#code-results');
  container.innerHTML = '';

  if (codes.length === 0) {
    container.innerHTML = '<p class="empty-state">No matching codes found.</p>';
    return;
  }

  codes.forEach((code) => {
    const row = document.createElement('div');
    row.className = 'code-row';
    const isSelected = state.selectedCodes.has(code.code);
    row.innerHTML = `
      <input type="checkbox" ${isSelected ? 'checked' : ''}>
      <span class="code-badge">${code.code}</span>
      <span>${code.description}</span>
      <span class="code-category">${code.category}</span>
    `;
    const checkbox = row.querySelector('input');
    checkbox.addEventListener('change', () => {
      if (checkbox.checked) state.selectedCodes.set(code.code, code.description);
      else state.selectedCodes.delete(code.code);
      updateSelectionSummary();
    });
    row.addEventListener('click', (e) => {
      if (e.target !== checkbox) checkbox.click();
    });
    container.appendChild(row);
  });
}

function severityCard(result) {
  const card = document.createElement('div');
  card.className = `result-card severity-${result.severity}`;
  const matchedTags = [
    ...result.matched_symptoms.map((s) => `<span class="matched-tag">Symptom: ${s}</span>`),
    ...result.matched_codes.map((c) => `<span class="matched-tag">Code: ${c}</span>`),
  ].join('');

  card.innerHTML = `
    <div class="result-header">
      <h3>#${result.rank} ${result.name}</h3>
      <span class="severity-badge severity-${result.severity}">${result.severity}</span>
    </div>
    <div class="confidence-track"><div class="confidence-fill" style="width:${result.confidence}%"></div></div>
    <div class="confidence-label">${result.confidence}% confidence</div>
    <p class="result-description">${result.description}</p>
    <p class="result-action"><strong>Recommended action:</strong> ${result.recommended_action}</p>
    <div class="matched-tags">${matchedTags}</div>
  `;
  return card;
}

async function runDiagnosis() {
  const resultsSection = $('#results');
  resultsSection.innerHTML = '';

  if (state.selectedSymptoms.size === 0 && state.selectedCodes.size === 0) {
    resultsSection.innerHTML = '<p class="error-banner">Select at least one symptom or DTC code first.</p>';
    return;
  }

  const payload = {
    symptom_ids: [...state.selectedSymptoms],
    dtc_codes: [...state.selectedCodes.keys()],
    vehicle: {
      make: $('#vehicle-make').value.trim() || null,
      model: $('#vehicle-model').value.trim() || null,
      year: $('#vehicle-year').value.trim() || null,
    },
  };

  const res = await fetch('/api/diagnose', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await res.json();

  if (!res.ok) {
    resultsSection.innerHTML = `<p class="error-banner">${data.error || 'Something went wrong.'}</p>`;
    return;
  }

  if (data.results.length === 0) {
    resultsSection.innerHTML = '<p class="empty-state">No matching faults found for this combination. Try adding more symptoms or codes.</p>';
    return;
  }

  data.results.forEach((result) => resultsSection.appendChild(severityCard(result)));
  resultsSection.scrollIntoView({ behavior: 'smooth' });
}

async function loadHistory() {
  const res = await fetch('/api/history');
  const sessions = await res.json();
  const list = $('#history-list');
  $('#history-detail').innerHTML = '';

  if (sessions.length === 0) {
    list.innerHTML = '<p class="empty-state">No diagnostic sessions yet. Run a diagnosis first.</p>';
    return;
  }

  const rows = sessions.map((s) => `
    <tr data-id="${s.id}">
      <td>#${s.id}</td>
      <td>${[s.vehicle_make, s.vehicle_model, s.vehicle_year].filter(Boolean).join(' ') || '—'}</td>
      <td>${new Date(s.created_at).toLocaleString()}</td>
    </tr>
  `).join('');

  list.innerHTML = `
    <table>
      <thead><tr><th>ID</th><th>Vehicle</th><th>Date</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
  `;

  list.querySelectorAll('tr[data-id]').forEach((row) => {
    row.addEventListener('click', () => loadHistoryDetail(row.dataset.id));
  });
}

async function loadHistoryDetail(id) {
  const res = await fetch(`/api/history/${id}`);
  const session = await res.json();
  const detail = $('#history-detail');
  detail.innerHTML = `<h3>Session #${session.id}</h3>`;

  if (session.results.length === 0) {
    detail.innerHTML += '<p class="empty-state">No faults were matched in this session.</p>';
    return;
  }

  session.results.forEach((result) => detail.appendChild(severityCard(result)));
}

function init() {
  initTabs();
  loadSymptoms();
  searchCodes('');
  updateSelectionSummary();

  $('#code-search').addEventListener('input', (e) => searchCodes(e.target.value));
  $('#run-diagnosis').addEventListener('click', runDiagnosis);
}

document.addEventListener('DOMContentLoaded', init);
