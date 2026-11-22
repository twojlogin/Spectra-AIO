(() => {
  const $ = (id) => document.getElementById(id);
  const output = $('output');
  const statusBox = $('statusBox');
  const healthDot = $('healthDot');
  const healthText = $('healthText');
  const logBuffer = [];

  function log(title, data) {
    const entry = { ts: new Date().toISOString(), title, data };
    logBuffer.unshift(entry);
    if (logBuffer.length > 200) logBuffer.pop();
    const body = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
    output.textContent = `[${new Date(entry.ts).toLocaleTimeString()}] ${title}\n${body}\n\n` + output.textContent;
  }

  async function api(path, opts = {}) {
    const res = await fetch(path, {
      headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) },
      ...opts,
    });
    const text = await res.text();
    let data;
    try { data = text ? JSON.parse(text) : null; } catch { data = { raw: text }; }
    if (!res.ok) {
      const msg = (data && (data.detail || data.error)) || `HTTP ${res.status}`;
      throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
    }
    return data;
  }

  function setHealth(ok, text) {
    healthDot.className = 'dot ' + (ok ? 'dot-on' : 'dot-off');
    healthText.textContent = text;
    const statHealth = $('statHealth');
    if (statHealth) statHealth.textContent = ok ? 'ONLINE' : 'OFFLINE';
  }

  function renderModules(modules) {
    const box = $('modulesList');
    if (!box) return;
    box.innerHTML = '';
    if (!Array.isArray(modules) || !modules.length) {
      box.textContent = 'Brak modułów';
      return;
    }
    modules.forEach(m => {
      const el = document.createElement('div');
      el.className = 'module-chip';
      el.textContent = m;
      box.appendChild(el);
    });
  }

  async function refreshNetwork(check=false) {
    const box = $('netStatusBox');
    if (box) box.textContent = check ? 'Sprawdzanie połączenia...' : 'Ładowanie...';
    try {
      const data = await api('/api/network/status' + (check ? '?check=true' : ''));
      if (box) box.textContent = JSON.stringify(data, null, 2);
      return data;
    } catch (e) {
      if (box) box.textContent = 'Błąd: ' + e.message;
      log('ERR network', e.message);
    }
  }

  async function refreshStatus() {
    try {
      const [health, root, stats] = await Promise.all([api('/health'), api('/'), api('/api/stats').catch(() => null)]);
      setHealth(true, 'Backend online');
      statusBox.textContent = JSON.stringify({ health, root, stats }, null, 2);
      renderModules((stats && stats.modules) || root.modules || []);
      if ($('statModules')) $('statModules').textContent = String((stats && stats.module_count) ?? (root.modules || []).length);
      if ($('statProfiles')) $('statProfiles').textContent = String((stats && stats.profiles_count) ?? '-');
      refreshNetwork(false);
    } catch (e) {
      setHealth(false, 'Backend offline');
      statusBox.textContent = 'Błąd: ' + e.message;
      renderModules([]);
    }
  }

  function getTarget(fromDash = false) {
    const site = $(fromDash ? 'dashSite' : 'site').value.trim();
    const username = $(fromDash ? 'dashUsername' : 'username').value.trim();
    if (!site || !username) throw new Error('Podaj site i username');
    if (!fromDash) { $('dashSite').value = site; $('dashUsername').value = username; }
    else { $('site').value = site; $('username').value = username; }
    return { site, username };
  }

  async function runEndpoint(name, path) {
    try {
      log(`START ${name}`, path);
      const data = await api(path);
      log(`OK ${name}`, data);
      return data;
    } catch (e) {
      log(`ERR ${name}`, e.message);
      throw e;
    }
  }

  async function fullRecon(fromDash = false) {
    const { site, username } = getTarget(fromDash);
    const encS = encodeURIComponent(site), encU = encodeURIComponent(username);
    const report = { target: username, site, started_at: new Date().toISOString(), steps: {} };
    try {
      report.steps.cam_map = await runEndpoint('cam-map', `/osint/cam-map/${encS}/${encU}`);
      const socials = report.steps.cam_map?.discovered_socials || {};
      if (!Object.keys(socials).length) report.steps.search = await runEndpoint('search', `/osint/search/${encU}`);
      report.steps.ghost = await runEndpoint('ghost-scan', `/osint/ghost-scan/${encS}/${encU}`);
      report.steps.omni = await runEndpoint('omni-check', `/osint/check-user/${encU}`);
      const avatarUrl = report.steps.cam_map?.avatar_url;
      if (avatarUrl) report.steps.avatar = await runEndpoint('avatar', `/osint/avatar-check/${encS}/${encU}?avatar_url=${encodeURIComponent(avatarUrl)}`);
      report.finished_at = new Date().toISOString();
      log('FULL RECON SUMMARY', report);
    } catch (e) {
      report.error = e.message;
      report.finished_at = new Date().toISOString();
      log('FULL RECON FAILED', report);
    }
  }

  async function refreshProfiles() {
    try {
      const rows = await api('/api/profiles');
      const tbody = $('profilesBody');
      tbody.textContent = '';
      if (!Array.isArray(rows) || rows.length === 0) {
        const tr = document.createElement('tr'); const td = document.createElement('td');
        td.colSpan = 4; td.className = 'muted'; td.textContent = 'Brak profili'; tr.appendChild(td); tbody.appendChild(tr); return;
      }
      for (const r of rows) {
        const tr = document.createElement('tr');
        [r.id, r.name, r.platform, r.url].forEach(v => { const td = document.createElement('td'); td.textContent = v == null ? '' : String(v); tr.appendChild(td); });
        tbody.appendChild(tr);
      }
    } catch (e) { log('ERR profiles', e.message); }
  }

  async function addProfile() {
    const msg = $('profileMsg'); msg.textContent = '';
    const body = { name: $('pName').value.trim(), platform: $('pPlatform').value.trim(), url: $('pUrl').value.trim(), description: $('pDesc').value.trim() };
    try {
      const data = await api('/api/profiles/add', { method: 'POST', body: JSON.stringify(body) });
      msg.textContent = data.message || 'Zapisano';
      log('PROFILE ADD', data);
      ['pName','pPlatform','pUrl','pDesc'].forEach(id => $(id).value = '');
      await refreshProfiles(); await refreshStatus();
    } catch (e) { msg.textContent = 'Błąd: ' + e.message; }
  }

  function bindClick(id, fn) { const el = $(id); if (el) el.addEventListener('click', fn); }

  document.querySelectorAll('.nav-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      btn.classList.add('active');
      const tab = document.getElementById('tab-' + btn.dataset.tab);
      if (tab) tab.classList.add('active');
    });
  });

  bindClick('btnRefreshStatus', refreshStatus);
  bindClick('btnDashStatus', refreshStatus);
  bindClick('btnDashModules', refreshStatus);
  bindClick('btnNetRefresh', () => refreshNetwork(false));
  bindClick('btnNetCheck', () => refreshNetwork(true));
  bindClick('btnClearOutput', () => { output.textContent = 'Wyczyszczono.'; });
  bindClick('btnCopyOutput', async () => { try { await navigator.clipboard.writeText(output.textContent); log('COPY', 'Skopiowano output do schowka'); } catch(e){ log('ERR copy', e.message); } });
  bindClick('btnExportOutput', () => {
    const blob = new Blob([JSON.stringify(logBuffer, null, 2)], {type:'application/json'});
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'spectra-ui-log.json'; a.click(); URL.revokeObjectURL(a.href);
  });
  bindClick('btnRefreshProfiles', refreshProfiles);
  bindClick('btnAddProfile', addProfile);
  bindClick('btnFullRecon', () => fullRecon(false));
  bindClick('btnDashRecon', () => fullRecon(true));
  bindClick('btnCamMap', () => { const {site,username}=getTarget(false); runEndpoint('cam-map', `/osint/cam-map/${encodeURIComponent(site)}/${encodeURIComponent(username)}`); });
  bindClick('btnGhost', () => { const {site,username}=getTarget(false); runEndpoint('ghost-scan', `/osint/ghost-scan/${encodeURIComponent(site)}/${encodeURIComponent(username)}`); });
  bindClick('btnSearch', () => { const {username}=getTarget(false); runEndpoint('search', `/osint/search/${encodeURIComponent(username)}`); });
  bindClick('btnOmni', () => { const {username}=getTarget(false); runEndpoint('omni-check', `/osint/check-user/${encodeURIComponent(username)}`); });
  bindClick('btnEmail', () => { const email=$('email').value.trim(); if(!email) return log('ERR email','Podaj email'); runEndpoint('email-recon', `/osint/email-recon/${encodeURIComponent(email)}`); });
  bindClick('btnAvatar', () => { const {site,username}=getTarget(false); const url=$('avatarUrl').value.trim(); if(!url) return log('ERR avatar','Podaj avatar URL'); runEndpoint('avatar', `/osint/avatar-check/${encodeURIComponent(site)}/${encodeURIComponent(username)}?avatar_url=${encodeURIComponent(url)}`); });
  bindClick('btnTg', () => { const ch=$('tgChannel').value.trim(); if(!ch) return log('ERR tg','Podaj kanał'); runEndpoint('telegram', `/osint/telegram/${encodeURIComponent(ch)}`); });

  // rage theme
  const rageSel = $('rageLevel');
  const applyRage = (v) => { document.body.setAttribute('data-rage', String(v ?? '0')); };
  const savedRage = localStorage.getItem('spectra_rage') || '0';
  if (rageSel) { rageSel.value = savedRage; rageSel.addEventListener('change', () => { localStorage.setItem('spectra_rage', rageSel.value); applyRage(rageSel.value); }); }
  applyRage(savedRage);

  // opencode.ai easter egg
  const checkOpencode = () => {
    const vals = Array.from(document.querySelectorAll('input,textarea')).map(el => (el.value||'').toLowerCase());
    const hit = vals.some(v => v.includes('opencode.ai'));
    document.body.classList.toggle('opencode-pulse', hit);
  };
  document.addEventListener('input', (e) => { if (e.target && (e.target.matches('input,textarea'))) checkOpencode(); });

  refreshStatus();
  refreshProfiles();
})();
