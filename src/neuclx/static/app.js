(() => {
const journey = document.querySelector('#journey');
const chat = document.querySelector('#chat');
const promptInput = document.querySelector('#prompt');
const factInput = document.querySelector('#fact');
const agentSelect = document.querySelector('#agent-name');
const agentQuestion = document.querySelector('#agent-question');
const agentRun = document.querySelector('#agent-run');
const agentOutput = document.querySelector('#agent-output');
const reasoningTask = document.querySelector('#reasoning-task');
const reasoningContext = document.querySelector('#reasoning-context');
const reasoningRunSource = document.querySelector('#reasoning-run');
const reasoningRun = reasoningRunSource ? reasoningRunSource.cloneNode(true) : null;
if (reasoningRunSource && reasoningRun) reasoningRunSource.replaceWith(reasoningRun);
const reasoningOutput = document.querySelector('#reasoning-output');

let platformSummary = document.querySelector('#platform-summary');
let platformFlags = document.querySelector('#platform-flags');
let registrySummary = document.querySelector('#registry-summary');
let registryFlags = document.querySelector('#registry-flags');
let hvoSummary = document.querySelector('#hvo-summary');
let hvoFlags = document.querySelector('#hvo-flags');

const esc = (value) => String(value ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

function badgeLabel(state, achievement) {
  if (state === 'unavailable' || state === 'not_implemented') return 'recorded';
  if (state === 'declared') return 'sandbox';
  return achievement || 'success';
}

function formatList(items) {
  return `<ul>${(items || []).map((item) => `<li>${esc(item)}</li>`).join('')}</ul>`;
}

function formatMetadata(metadata) {
  if (!metadata || typeof metadata !== 'object' || !Object.keys(metadata).length) {
    return '<div class="chain"><h4>Evidence chain</h4><div>Pa metadata të ruajtur.</div></div>';
  }

  const evidenceChain = Array.isArray(metadata.evidence_chain)
    ? metadata.evidence_chain
        .map((step) => `<li>${esc(step.source_digest || step.source || 'source')}${step.matching_terms ? ` · ${esc(step.matching_terms.join(', '))}` : ''}${typeof step.score === 'number' ? ` · ${esc(step.score.toFixed(2))}` : ''}</li>`)
        .join('')
    : '';

  const inputEvidence = Array.isArray(metadata.input_evidence) ? formatList(metadata.input_evidence) : '';
  const derivedFacts = Array.isArray(metadata.derived_facts) ? formatList(metadata.derived_facts) : '';
  const operations = Array.isArray(metadata.operations)
    ? `<ul>${metadata.operations.map((operation) => `<li><b>${esc(operation.reasoning_type || 'step')}</b>${operation.operation ? ` · ${esc(operation.operation)}` : ''}${operation.result ? ` = ${esc(operation.result)}` : ''}</li>`).join('')}</ul>`
    : '';
  const confidence = metadata.confidence_breakdown && typeof metadata.confidence_breakdown === 'object'
    ? `<div class="panel-kv">${Object.entries(metadata.confidence_breakdown).map(([key, value]) => `<div><span>${esc(key)}</span><b>${esc(value)}</b></div>`).join('')}</div>`
    : '';

  return `
    <div class="chain">
      <h4>Evidence chain</h4>
      ${evidenceChain ? `<ul>${evidenceChain}</ul>` : '<div>Pa gjurmë të strukturuara.</div>'}
      ${inputEvidence ? `<h4>Input evidence</h4>${inputEvidence}` : ''}
      ${derivedFacts ? `<h4>Derived facts</h4>${derivedFacts}` : ''}
      ${operations ? `<h4>Operations</h4>${operations}` : ''}
      ${confidence ? `<h4>Confidence breakdown</h4>${confidence}` : ''}
    </div>`;
}

function ensureInsightsPanel() {
  if (platformSummary && registrySummary && hvoSummary) return;
  const journeySection = document.querySelector('#journey');
  if (!journeySection) return;
  const grid = document.createElement('section');
  grid.className = 'insight-grid';
  grid.setAttribute('aria-label', 'System insights');
  grid.innerHTML = `
    <article class="insight-card">
      <div class="agent-header"><h2>Platform profile</h2><span id="platform-flags">duke u ngarkuar</span></div>
      <div id="platform-summary">Pritet metadata e platformës.</div>
    </article>
    <article class="insight-card">
      <div class="agent-header"><h2>Open data registry</h2><span id="registry-flags">duke u ngarkuar</span></div>
      <div id="registry-summary">Pritet lista e burimeve të dhënave të vërteta.</div>
    </article>
    <article class="insight-card">
      <div class="agent-header"><h2>HVO dimensions</h2><span id="hvo-flags">duke u ngarkuar</span></div>
      <div id="hvo-summary">Priten dimensionet e alfabetit HVO.</div>
    </article>`;
  journeySection.before(grid);
  platformSummary = document.querySelector('#platform-summary');
  platformFlags = document.querySelector('#platform-flags');
  registrySummary = document.querySelector('#registry-summary');
  registryFlags = document.querySelector('#registry-flags');
  hvoSummary = document.querySelector('#hvo-summary');
  hvoFlags = document.querySelector('#hvo-flags');
}

function renderStone(stone) {
  const response = stone.response || {};
  const metadata = response.metadata || {};
  const state = String(response.state || 'unknown');
  const value = response.value === null ? 'Nuk ka ende rezultat të disponueshëm.' : JSON.stringify(response.value);
  const article = document.createElement('article');
  article.className = 'stone';
  article.innerHTML = `
    <div class="num">#${String(stone.number).padStart(3, '0')}</div>
    <div>
      <h3>${esc(stone.prompt)}</h3>
      <p>${esc(value)}</p>
      <p><small>${esc(response.source || 'unknown-source')} · ${esc(response.method || 'unknown-method')}</small></p>
      ${formatMetadata(metadata)}
    </div>
    <span class="badge">✓ ${esc(badgeLabel(state, stone.achievement))} · ${esc(state)}</span>`;
  journey.append(article);
}

async function loadJourney() {
  const response = await fetch('/api/journey');
  const data = await response.json();
  journey.replaceChildren();
  (data.stones || []).forEach(renderStone);
}

async function loadInsights() {
  ensureInsightsPanel();
  if (!platformSummary || !registrySummary || !hvoSummary || !platformFlags || !registryFlags || !hvoFlags) return;
  const [platformResponse, registryResponse] = await Promise.all([fetch('/api/platform'), fetch('/api/registry')]);
  const platform = await platformResponse.json();
  const registry = await registryResponse.json();

  platformFlags.textContent = `${platform.multilingual ? 'multilingual' : 'mono'} · ${platform.layers} layers`;
  platformSummary.innerHTML = `
    <div class="panel-kv">
      <div><span>Agents</span><b>${esc((platform.agents || []).join(', '))}</b></div>
      <div><span>HVO axes</span><b>${esc((platform.hvo_axes || []).join(', '))}</b></div>
      <div><span>API endpoints</span><b>${esc((platform.saas_api?.endpoints || []).length)}</b></div>
    </div>`;

  registryFlags.textContent = `${registry.summary?.total_sources || 0} sources`;
  registrySummary.innerHTML = `
    <div class="panel-kv">
      <div><span>Active</span><b>${esc(registry.summary?.active_sources ?? 0)}</b></div>
      <div><span>Regions</span><b>${esc(Object.keys(registry.summary?.regions || {}).join(', '))}</b></div>
    </div>
    ${formatList((registry.sources || []).slice(0, 5).map((source) => `${source.name} · ${source.source_type} · ${source.region}`))}`;

  hvoFlags.textContent = `${(platform.hvo_axes || []).length} dimensions`;
  hvoSummary.innerHTML = `<div class="panel-kv">${(platform.hvo_axes || []).map((axis) => `<div><span>${esc(axis)}</span><b>active</b></div>`).join('')}</div>`;
}

async function runAgent() {
  const agent = agentSelect.value;
  const question = agentQuestion.value.trim();
  if (!question) {
    agentOutput.textContent = 'Shkruaj një pyetje reale para se të dërgosh.';
    return;
  }
  const response = await fetch(`/api/agents?agent=${encodeURIComponent(agent)}&question=${encodeURIComponent(question)}`);
  const payload = await response.json();
  if (!response.ok) {
    agentOutput.textContent = payload.detail || payload.error || 'Keni gabim në agent.';
    return;
  }
  agentOutput.textContent = `${payload.agent.toUpperCase()}: ${payload.answer}`;
}

chat.addEventListener('submit', async (event) => {
  event.preventDefault();
  const question = promptInput.value.trim();
  if (!question) return;
  const facts = factInput.value.trim() ? [factInput.value.trim()] : [];
  const response = await fetch('/api/respond', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt: question, facts }),
  });
  const payload = await response.json();
  if (!response.ok) {
    alert(payload.detail || payload.error || 'Gabim');
    return;
  }
  promptInput.value = '';
  factInput.value = '';
  await loadJourney();
});

if (reasoningRun) {
  reasoningRun.addEventListener('click', async () => {
    const task = reasoningTask.value.trim();
    const context = reasoningContext.value.split(/\n|\r\n/).map((line) => line.trim()).filter(Boolean);
    if (!task) {
      reasoningOutput.textContent = 'Shkruaj një pyetje reale para se të fillosh reasoning.';
      return;
    }

    reasoningOutput.innerHTML = '<strong>Po arsyetohet...</strong>';
    const response = await fetch('/api/reason', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task, facts: context }),
    });
    const payload = await response.json();
    if (!response.ok) {
      reasoningOutput.textContent = payload.detail || payload.error || 'Gabim në reason API';
      return;
    }

    const steps = (payload.trace?.steps || []).map((step, index) => `<div class="reason-step"><strong>Hapi ${index + 1}</strong> · ${esc(step.reasoning_type)} · ${esc(step.status)}<br><small>${esc(step.hypothesis || 'Pa hipotezë')}</small></div>`).join('');
    const evidence = (payload.evidence_path || []).map((item) => `<li>${esc(item)}</li>`).join('');
    const chain = formatMetadata({
      input_evidence: payload.input_evidence,
      derived_facts: payload.derived_facts,
      operations: payload.operations,
      confidence_breakdown: payload.confidence_breakdown,
      evidence_chain: payload.trace?.steps?.map((step) => ({ source: step.reasoning_type, matching_terms: [step.status], score: step.confidence })) || [],
    });

    reasoningOutput.innerHTML = `
      <div class="reasoning-summary">
        <div><strong>Intent:</strong> ${esc(payload.intent)}</div>
        <div><strong>Confidence:</strong> ${esc(payload.confidence)}</div>
      </div>
      <div><strong>Përfundim:</strong><br>${esc(payload.conclusion)}</div>
      <div><strong>Evidence path:</strong><ul>${evidence || '<li>Pa evidencë të shfaqur</li>'}</ul></div>
      ${chain}
      <div><strong>Trace:</strong>${steps || '<div>Pa hapa</div>'}</div>`;
  });
}

agentRun.addEventListener('click', runAgent);

loadJourney();
loadInsights();
})();