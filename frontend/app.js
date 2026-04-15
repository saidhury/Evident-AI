const form = document.getElementById('requestForm');
const statusEl = document.getElementById('status');
const decisionEl = document.getElementById('decision');
const evidenceEl = document.getElementById('evidence');
const resultSection = document.getElementById('result');
const insightsEl = document.getElementById('insights');
const policyChecksEl = document.getElementById('policyChecks');
const timelineEl = document.getElementById('timeline');
const roleSelect = document.getElementById('roleSelect');
const reviewerIdInput = document.getElementById('reviewerId');
const refreshQueueBtn = document.getElementById('refreshQueueBtn');
const exportQueueBtn = document.getElementById('exportQueueBtn');
const reviewQueueEl = document.getElementById('reviewQueue');
const reviewErrorEl = document.getElementById('reviewError');
const consumerListEl = document.getElementById('consumerList');
const consumerSearchEl = document.getElementById('consumerSearch');
const policyAlertsEl = document.getElementById('policyAlerts');
const integrationsListEl = document.getElementById('integrationsList');
const fairnessTableEl = document.getElementById('fairnessTable');
const modePillEl = document.getElementById('modePill');
const kpiEvidenceEl = document.getElementById('kpiEvidence');
const kpiRefusalsEl = document.getElementById('kpiRefusals');
const kpiOpenQueueEl = document.getElementById('kpiOpenQueue');
const kpiModeEl = document.getElementById('kpiMode');

const DEMO_CONSUMERS = [
  { id: 'C-1001', name: 'Alice Carter', credit_score: 720, debt_to_income: 0.31, annual_income: 98000, loan_amount: 240000, state: 'NY', segment: 'Prime' },
  { id: 'C-1002', name: 'Brian Hughes', credit_score: 658, debt_to_income: 0.43, annual_income: 86000, loan_amount: 220000, state: 'TX', segment: 'Near Prime' },
  { id: 'C-1003', name: 'Carla Mendes', credit_score: 590, debt_to_income: 0.47, annual_income: 64000, loan_amount: 205000, state: 'FL', segment: 'Rebuild' },
  { id: 'C-1004', name: 'Dev Patel', credit_score: 781, debt_to_income: 0.22, annual_income: 130000, loan_amount: 340000, state: 'CA', segment: 'Prime Plus' },
  { id: 'C-1005', name: 'Evelyn Ross', credit_score: 611, debt_to_income: 0.39, annual_income: 71000, loan_amount: 180000, state: 'OH', segment: 'Near Prime' },
  { id: 'C-1006', name: 'Farah Khan', credit_score: 735, debt_to_income: 0.29, annual_income: 112000, loan_amount: 310000, state: 'IL', segment: 'Prime' },
  { id: 'C-1007', name: 'George Whitman', credit_score: 548, debt_to_income: 0.56, annual_income: 58000, loan_amount: 165000, state: 'GA', segment: 'High Risk' },
  { id: 'C-1008', name: 'Hana Suzuki', credit_score: 694, debt_to_income: 0.35, annual_income: 102000, loan_amount: 265000, state: 'WA', segment: 'Prime' },
  { id: 'C-1009', name: 'Isaac Green', credit_score: 603, debt_to_income: 0.44, annual_income: 76000, loan_amount: 215000, state: 'NC', segment: 'Near Prime' },
  { id: 'C-1010', name: 'Julia Moreau', credit_score: 749, debt_to_income: 0.26, annual_income: 124000, loan_amount: 355000, state: 'MA', segment: 'Prime Plus' },
  { id: 'C-1011', name: 'Kenny Ortiz', credit_score: 572, debt_to_income: 0.49, annual_income: 61000, loan_amount: 175000, state: 'AZ', segment: 'Rebuild' },
  { id: 'C-1012', name: 'Lena Volkova', credit_score: 689, debt_to_income: 0.33, annual_income: 91000, loan_amount: 248000, state: 'CO', segment: 'Prime' },
];

const POLICY_ALERTS = [
  'Fair Lending Bulletin FL-2026-04 flagged for review cycle in 6 days.',
  'Income Verification Addendum IV-19 scheduled for retrieval index refresh.',
  'State-specific cap guidance pending legal sign-off for CA and NY products.',
];

const FAIRNESS_ROWS = [
  { segment: 'Prime', approvals: '78%', medianScore: 728, note: 'Stable' },
  { segment: 'Near Prime', approvals: '52%', medianScore: 639, note: 'Watchlist' },
  { segment: 'Rebuild', approvals: '28%', medianScore: 584, note: 'Requires manual review' },
];

const INTEGRATIONS = [
  { name: 'Decision API', status: 'live' },
  { name: 'Review Queue API', status: 'live' },
  { name: 'LOS Adapter', status: 'placeholder' },
  { name: 'CRM Webhook', status: 'placeholder' },
  { name: 'Fairness Dashboard', status: 'placeholder' },
];

let appMode = 'demo';
let mockQueue = [
  {
    ticket_id: 'TICKET-DEMO-1',
    status: 'open',
    reason: 'Evidence confidence below threshold (0.17)',
    trace_id: 'demo-trace-001',
    actions: [],
  },
  {
    ticket_id: 'TICKET-DEMO-2',
    status: 'open',
    reason: 'Policy contradiction detected in placeholder LOS feed',
    trace_id: 'demo-trace-002',
    actions: [],
  },
];

const metrics = {
  decisions: 0,
  refusals: 0,
  evidenceQuality: 0,
  openQueue: 0,
};

function setStatus(text, variant = 'processing') {
  statusEl.textContent = text;
  statusEl.className = `status status-${variant}`;
}

function updateMode(mode) {
  appMode = mode;
  const upper = mode.toUpperCase();
  modePillEl.textContent = `${upper} FLOW`;
  modePillEl.className = `mode-pill mode-${mode}`;
  kpiModeEl.textContent = upper;
}

function reviewHeaders() {
  return {
    'Content-Type': 'application/json',
    'X-Reviewer-Role': roleSelect.value,
    'X-Reviewer-Id': reviewerIdInput.value || 'reviewer-ui',
  };
}

function showReviewError(message = '') {
  if (!message) {
    reviewErrorEl.textContent = '';
    reviewErrorEl.classList.add('hidden');
    return;
  }
  reviewErrorEl.textContent = message;
  reviewErrorEl.classList.remove('hidden');
}

function calculateRefusalRate() {
  if (metrics.decisions === 0) {
    return '0%';
  }
  return `${Math.round((metrics.refusals / metrics.decisions) * 100)}%`;
}

function refreshKpis() {
  kpiEvidenceEl.textContent = metrics.evidenceQuality.toFixed(2);
  kpiRefusalsEl.textContent = calculateRefusalRate();
  kpiOpenQueueEl.textContent = String(metrics.openQueue);
}

function renderInsights(meta) {
  const counterfactual = meta && meta.counterfactual;
  if (!counterfactual || !counterfactual.available || !Array.isArray(counterfactual.suggestions) || counterfactual.suggestions.length === 0) {
    insightsEl.innerHTML = '';
    insightsEl.classList.add('hidden');
    return;
  }

  const items = counterfactual.suggestions
    .map((s) => `<li><strong>${s.field}</strong>: ${s.why}</li>`)
    .join('');
  insightsEl.innerHTML = `<h4>Counterfactual Guidance</h4><ul>${items}</ul>`;
  insightsEl.classList.remove('hidden');
}

function renderPolicyChecks(data, payload) {
  const meta = data.meta || {};
  const checks = [
    { label: 'Policy Version', value: meta.policy_version || 'placeholder-policy-v1' },
    { label: 'Config Fingerprint', value: meta.config_fingerprint || 'placeholder-fingerprint' },
    { label: 'Applicant DTI', value: Number(payload.applicant.debt_to_income || 0).toFixed(2) },
    { label: 'Evidence Quality', value: Number(meta.evidence_quality || 0).toFixed(2) },
  ];

  policyChecksEl.innerHTML = checks
    .map((item) => `<div class="stack-item"><span>${item.label}</span><strong>${item.value}</strong></div>`)
    .join('');
}

function renderTimeline(data) {
  const timelineItems = [
    'Payload received and normalized',
    'Policy engine evaluated rule thresholds',
    'Retriever executed evidence search',
    data.status === 'refused' ? 'Refusal handler raised review ticket' : 'Evidence validator accepted decision',
  ];

  timelineEl.innerHTML = timelineItems
    .map((item) => `<div class="timeline-item">${item}</div>`)
    .join('');
}

function renderEvidence(evidence = []) {
  evidenceEl.innerHTML = '';
  if (!Array.isArray(evidence) || evidence.length === 0) {
    evidenceEl.innerHTML = '<div class="ev">No evidence returned.</div>';
    return;
  }
  evidence.forEach((ev, index) => {
    const el = document.createElement('div');
    el.className = 'ev';
    el.style.animationDelay = `${index * 80}ms`;
    el.innerHTML = `<div><strong>${ev.source || 'source'}</strong></div><div>${ev.text || ''}</div><div class="ev-score">score: ${Number(ev.score || 0).toFixed(3)}</div>`;
    evidenceEl.appendChild(el);
  });
}

function ticketTemplate(ticket) {
  const statusCls = ticket.status === 'closed' ? 'closed' : 'open';
  return `
    <div class="ticket" data-ticket-id="${ticket.ticket_id}">
      <div class="ticket-head">
        <span class="ticket-id">${ticket.ticket_id}</span>
        <span class="ticket-status ${statusCls}">${ticket.status}</span>
      </div>
      <div class="ticket-reason">${ticket.reason || 'No reason provided'}</div>
      <div class="ticket-actions">
        <button class="btn ghost" data-action="comment">Comment</button>
        <button class="btn ghost" data-action="approve_override">Approve Override</button>
        <button class="btn ghost" data-action="reject">Reject</button>
      </div>
    </div>
  `;
}

function renderQueue(items) {
  const queue = Array.isArray(items) ? items : [];
  metrics.openQueue = queue.filter((item) => item.status === 'open').length;
  refreshKpis();

  if (queue.length === 0) {
    reviewQueueEl.innerHTML = '<div class="ticket">No tickets in queue.</div>';
    return;
  }
  reviewQueueEl.innerHTML = queue.slice().reverse().map(ticketTemplate).join('');
}

function simulateDecision(payload) {
  const applicant = payload.applicant || {};
  const credit = Number(applicant.credit_score || 0);
  const dti = Number(applicant.debt_to_income || 0);
  const shouldRefuse = credit < 570 || dti > 0.5;
  const deniedByPolicy = credit < 600 || dti > 0.45;
  const evidenceQuality = shouldRefuse ? 0.12 : deniedByPolicy ? 0.28 : 0.86;

  const baseMeta = {
    trace_id: `demo-trace-${Date.now()}`,
    policy_version: '2026-04-15',
    config_fingerprint: 'demo-fingerprint',
    evidence_quality: evidenceQuality,
    counterfactual: {
      available: deniedByPolicy,
      suggestions: [
        credit < 600
          ? {
              field: 'credit_score',
              why: 'Meets minimum policy score threshold',
            }
          : null,
        dti > 0.45
          ? {
              field: 'debt_to_income',
              why: 'Falls within DTI policy cap',
            }
          : null,
      ].filter(Boolean),
    },
  };

  if (shouldRefuse) {
    const ticket = {
      ticket_id: `TICKET-DEMO-${mockQueue.length + 1}`,
      status: 'open',
      reason: 'No supporting citations found with sufficient confidence',
      trace_id: baseMeta.trace_id,
      actions: [],
    };
    mockQueue.push(ticket);
    return {
      decision: null,
      status: 'refused',
      flag: {
        status: 'flagged',
        ticket_id: ticket.ticket_id,
        reason: ticket.reason,
      },
      meta: baseMeta,
    };
  }

  return {
    decision: {
      decision: deniedByPolicy ? 'deny' : 'approve',
      rationale: deniedByPolicy ? 'Policy threshold exceeded' : 'Meets score and DTI thresholds',
      policy_rule: deniedByPolicy ? (credit < 600 ? 'CREDIT_SCORE_MIN' : 'DTI_MAX') : 'PASS',
    },
    status: 'approved_with_evidence',
    evidence: [
      {
        source: 'fair_lending_playbook.pdf#p12',
        text: 'Applicants must be evaluated solely on objective creditworthiness criteria.',
        score: Math.max(0.21, evidenceQuality - 0.1),
      },
      {
        source: 'income_verification_manual.pdf#p34',
        text: 'Income verification requires matching payroll data, statements, and tax filings.',
        score: Math.max(0.18, evidenceQuality - 0.13),
      },
    ],
    meta: baseMeta,
  };
}

function buildPayload() {
  const name = document.getElementById('name').value;
  const score = parseInt(document.getElementById('score').value, 10) || 0;
  const debtToIncome = parseFloat(document.getElementById('dti').value) || 0;
  const annualIncome = parseInt(document.getElementById('income').value, 10) || 0;
  const loanAmount = parseInt(document.getElementById('loanAmount').value, 10) || 0;
  const state = document.getElementById('state').value;

  return {
    applicant: {
      name,
      credit_score: score,
      debt_to_income: debtToIncome,
      annual_income: annualIncome,
      loan_amount: loanAmount,
      state,
    },
  };
}

async function runDecision(payload) {
  try {
    const res = await fetch('/api/decide', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.message || data.error || `Decision failed (${res.status})`);
    }
    updateMode('live');
    return data;
  } catch (_err) {
    updateMode('demo');
    return simulateDecision(payload);
  }
}

async function runReviewAction(ticketId, action) {
  const notes = window.prompt(`Add notes for ${action} on ${ticketId}:`, 'reviewed from UI') || '';
  if (appMode === 'live') {
    const payload = { action, reviewer: reviewerIdInput.value || 'reviewer-ui', notes };
    const res = await fetch(`/api/review/${ticketId}/action`, {
      method: 'POST',
      headers: reviewHeaders(),
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.message || data.error || `Action failed (${res.status})`);
    }
    return data;
  }

  mockQueue = mockQueue.map((ticket) => {
    if (ticket.ticket_id !== ticketId) {
      return ticket;
    }
    const actions = Array.isArray(ticket.actions) ? ticket.actions.slice() : [];
    actions.push({ action, reviewer: reviewerIdInput.value || 'reviewer-ui', notes, timestamp: new Date().toISOString() });
    return {
      ...ticket,
      status: action === 'approve_override' || action === 'reject' ? 'closed' : ticket.status,
      actions,
    };
  });
  return { ok: true };
}

async function loadReviewQueue() {
  showReviewError('');
  try {
    const res = await fetch('/api/review/queue', { headers: reviewHeaders() });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.message || data.error || `Queue fetch failed (${res.status})`);
    }
    updateMode('live');
    renderQueue(data.items || []);
  } catch (_err) {
    updateMode('demo');
    renderQueue(mockQueue);
    showReviewError('Live queue unavailable, showing demo queue data.');
  }
}

function exportQueueData(items) {
  const payload = {
    count: items.length,
    status_filter: null,
    items,
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'review-queue-export.json';
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function renderConsumers(items) {
  if (!items.length) {
    consumerListEl.innerHTML = '<div class="consumer-card">No matching consumers</div>';
    return;
  }

  consumerListEl.innerHTML = items
    .map(
      (consumer) => `
      <div class="consumer-card" data-consumer-id="${consumer.id}">
        <div class="consumer-top">
          <strong>${consumer.name}</strong>
          <span>${consumer.segment}</span>
        </div>
        <div class="consumer-meta">
          <span>Score ${consumer.credit_score}</span>
          <span>DTI ${consumer.debt_to_income}</span>
          <span>${consumer.state}</span>
        </div>
        <button class="btn ghost" data-consumer-load="${consumer.id}">Load Profile</button>
      </div>
    `
    )
    .join('');
}

function renderStaticSections() {
  policyAlertsEl.innerHTML = POLICY_ALERTS.map((alert) => `<li>${alert}</li>`).join('');
  integrationsListEl.innerHTML = INTEGRATIONS
    .map((item) => `<li><span>${item.name}</span><span class="mini-pill mini-${item.status}">${item.status}</span></li>`)
    .join('');

  fairnessTableEl.innerHTML = FAIRNESS_ROWS.map((row) => `
    <div class="fairness-row">
      <span>${row.segment}</span>
      <span>${row.approvals}</span>
      <span>${row.medianScore}</span>
      <span>${row.note}</span>
    </div>
  `).join('');
}

function loadConsumer(consumerId) {
  const consumer = DEMO_CONSUMERS.find((item) => item.id === consumerId);
  if (!consumer) {
    return;
  }

  document.getElementById('name').value = consumer.name;
  document.getElementById('score').value = consumer.credit_score;
  document.getElementById('dti').value = consumer.debt_to_income;
  document.getElementById('income').value = consumer.annual_income;
  document.getElementById('loanAmount').value = consumer.loan_amount;
  document.getElementById('state').value = consumer.state;
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  resultSection.classList.add('hidden');
  setStatus('Processing...', 'processing');
  decisionEl.textContent = '';
  insightsEl.innerHTML = '';
  policyChecksEl.innerHTML = '';
  timelineEl.innerHTML = '';
  insightsEl.classList.add('hidden');
  evidenceEl.innerHTML = '';
  resultSection.classList.remove('hidden');

  const payload = buildPayload();
  const data = await runDecision(payload);
  metrics.decisions += 1;
  metrics.evidenceQuality = Number(data.meta?.evidence_quality || 0);

  if (data.status === 'refused') {
    metrics.refusals += 1;
    setStatus('Refused — Human review required', 'refused');
    decisionEl.textContent = JSON.stringify(data.flag, null, 2);
    renderEvidence([]);
    await loadReviewQueue();
  } else {
    setStatus(data.status, 'approved');
    decisionEl.textContent = JSON.stringify(data.decision, null, 2);
    renderEvidence(data.evidence || []);
  }

  renderInsights(data.meta);
  renderPolicyChecks(data, payload);
  renderTimeline(data);
  refreshKpis();
});

refreshQueueBtn.addEventListener('click', () => {
  loadReviewQueue();
});

exportQueueBtn.addEventListener('click', async () => {
  showReviewError('');
  if (appMode === 'live') {
    try {
      const res = await fetch('/api/review/queue/export', { headers: reviewHeaders() });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.message || data.error || `Export failed (${res.status})`);
      }
      exportQueueData(data.items || []);
      return;
    } catch (_err) {
      updateMode('demo');
    }
  }
  exportQueueData(mockQueue);
  showReviewError('Exported demo queue because live export is unavailable.');
});

reviewQueueEl.addEventListener('click', async (event) => {
  const button = event.target.closest('button[data-action]');
  if (!button) {
    return;
  }
  const ticketEl = event.target.closest('[data-ticket-id]');
  if (!ticketEl) {
    return;
  }
  const ticketId = ticketEl.getAttribute('data-ticket-id');
  const action = button.getAttribute('data-action');
  try {
    await runReviewAction(ticketId, action);
    await loadReviewQueue();
  } catch (err) {
    showReviewError(String(err));
  }
});

consumerListEl.addEventListener('click', (event) => {
  const button = event.target.closest('button[data-consumer-load]');
  if (!button) {
    return;
  }
  const consumerId = button.getAttribute('data-consumer-load');
  loadConsumer(consumerId);
});

consumerSearchEl.addEventListener('input', () => {
  const q = consumerSearchEl.value.trim().toLowerCase();
  const filtered = DEMO_CONSUMERS.filter((consumer) => {
    const haystack = `${consumer.name} ${consumer.segment} ${consumer.state}`.toLowerCase();
    return haystack.includes(q);
  });
  renderConsumers(filtered);
});

renderConsumers(DEMO_CONSUMERS);
renderStaticSections();
loadReviewQueue();
refreshKpis();
