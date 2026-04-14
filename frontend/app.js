const form = document.getElementById('requestForm');
const statusEl = document.getElementById('status');
const decisionEl = document.getElementById('decision');
const evidenceEl = document.getElementById('evidence');
const resultSection = document.getElementById('result');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  resultSection.classList.add('hidden');
  const name = document.getElementById('name').value;
  const score = parseInt(document.getElementById('score').value, 10) || 0;
  const payload = { applicant: { name, credit_score: score } };
  statusEl.textContent = 'Processing...';
  decisionEl.textContent = '';
  evidenceEl.innerHTML = '';
  resultSection.classList.remove('hidden');

  try {
    const res = await fetch('/api/decide', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    const data = await res.json();
    if (data.status === 'refused') {
      statusEl.textContent = 'Refused — Human review required';
      decisionEl.textContent = JSON.stringify(data.flag, null, 2);
      return;
    }
    statusEl.textContent = data.status;
    decisionEl.textContent = JSON.stringify(data.decision, null, 2);
    const evidence = data.evidence || [];
    if (evidence.length === 0) {
      evidenceEl.innerHTML = '<div class="ev">No evidence returned.</div>';
    } else {
      evidence.forEach(ev => {
        const el = document.createElement('div');
        el.className = 'ev';
        el.innerHTML = `<div><strong>${ev.source || 'source'}</strong></div><div>${ev.text}</div>`;
        evidenceEl.appendChild(el);
      });
    }
  } catch (err) {
    statusEl.textContent = 'Error';
    decisionEl.textContent = String(err);
  }
});
