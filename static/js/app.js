// OMEN - Artifact Toolkit Builder Frontend
let currentGenerator = null;
let generators = {};
let currentResult = null;
let generationCount = 0;

document.addEventListener('DOMContentLoaded', function() {
    loadGenerators();
    setupObfuscation();
    setupKeyboardShortcuts();
});

function loadGenerators() {
    fetch('/api/generators')
        .then(r => r.json())
        .then(data => {
            generators = data;
            renderGeneratorList(data);
            updateStat('stat-generators', Object.keys(data).length);
        })
        .catch(err => {
            document.getElementById('generator-list').innerHTML =
                '<div class="placeholder-text">Failed to load generators</div>';
        });
}

function renderGeneratorList(gens) {
    const list = document.getElementById('generator-list');
    list.innerHTML = '';
    Object.entries(gens).forEach(([key, gen]) => {
        const item = document.createElement('div');
        item.className = 'generator-item';
        item.dataset.key = key;
        item.innerHTML = `
            <div class="gen-name">${gen.name}</div>
            <div class="gen-desc">${gen.description || ''}</div>
        `;
        item.onclick = () => selectGenerator(key);
        list.appendChild(item);
    });
}

function selectGenerator(key) {
    document.querySelectorAll('.generator-item').forEach(el => el.classList.remove('active'));
    const item = document.querySelector(`.generator-item[data-key="${key}"]`);
    if (item) item.classList.add('active');

    currentGenerator = key;
    currentResult = null;
    document.getElementById('output-area').innerHTML = '<span class="placeholder">Configure and generate...</span>';
    document.getElementById('output-stats').style.display = 'none';
    document.getElementById('generate-btn').disabled = false;

    const gen = generators[key];
    document.getElementById('config-title').textContent = gen.name;
    renderConfigOptions(gen.options || {});
}

function renderConfigOptions(options) {
    const container = document.getElementById('config-options');
    container.innerHTML = '';

    if (!options || Object.keys(options).length === 0) {
        container.innerHTML = '<p class="placeholder-text">No configuration options available.</p>';
        return;
    }

    Object.entries(options).forEach(([optKey, opt]) => {
        const group = document.createElement('div');
        group.className = 'config-group';
        group.dataset.optKey = optKey;

        const label = document.createElement('label');
        label.textContent = opt.label || optKey;
        group.appendChild(label);

        let input;
        if (opt.type === 'select') {
            input = document.createElement('select');
            (opt.options || []).forEach(o => {
                const option = document.createElement('option');
                option.value = o;
                option.textContent = o;
                if (o === opt.default) option.selected = true;
                input.appendChild(option);
            });
        } else if (opt.type === 'checkbox') {
            const wrapper = document.createElement('div');
            wrapper.className = 'checkbox-group';
            input = document.createElement('input');
            input.type = 'checkbox';
            input.checked = opt.default || false;
            wrapper.appendChild(input);
            group.appendChild(wrapper);
        } else if (opt.type === 'number') {
            input = document.createElement('input');
            input.type = 'number';
            input.value = opt.default || 0;
            input.step = '1';
        } else {
            input = document.createElement('input');
            input.type = 'text';
            input.value = opt.default || '';
        }

        if (input) {
            input.id = `opt-${optKey}`;
            input.name = optKey;
            if (opt.description) {
                const desc = document.createElement('div');
                desc.className = 'description';
                desc.textContent = opt.description;
                if (input.type !== 'checkbox') group.appendChild(input);
                group.appendChild(desc);
                if (input.type === 'checkbox') {
                    group.querySelector('.checkbox-group').appendChild(input);
                }
            } else {
                group.appendChild(input);
            }
        }

        // Handle conditional visibility
        if (opt.show_if) {
            group.dataset.depends = Object.keys(opt.show_if)[0];
            group.dataset.dependsValues = JSON.stringify(opt.show_if[Object.keys(opt.show_if)[0]]);
            group.style.display = 'none';
        }

        container.appendChild(group);
    });

    // Handle conditional visibility on change
    container.querySelectorAll('select, input').forEach(el => {
        el.addEventListener('change', updateConditionalVisibility);
        el.addEventListener('input', updateConditionalVisibility);
    });

    updateConditionalVisibility();
}

function updateConditionalVisibility() {
    document.querySelectorAll('.config-group[data-depends]').forEach(group => {
        const depKey = group.dataset.depends;
        const depValues = JSON.parse(group.dataset.dependsValues);
        const depEl = document.getElementById(`opt-${depKey}`);
        if (depEl) {
            const val = depEl.value !== undefined ? depEl.value : (depEl.checked ? true : false);
            group.style.display = depValues.includes(val) ? 'block' : 'none';
        }
    });
}

function getConfigValues() {
    const values = {};
    document.querySelectorAll('.config-group').forEach(group => {
        const key = group.dataset.optKey;
        if (!key) return;
        const el = document.getElementById(`opt-${key}`);
        if (el) {
            values[key] = el.type === 'checkbox' ? el.checked : el.value;
        }
    });
    return values;
}

function generate() {
    if (!currentGenerator) {
        showToast('Please select a generator first', 'error');
        return;
    }

    const obfuscation = document.getElementById('obfuscation-level').value;
    const options = getConfigValues();

    document.getElementById('generate-btn').disabled = true;
    document.getElementById('generate-btn').textContent = '⏳ Generating...';

    fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            generator: currentGenerator,
            options: options,
            obfuscation: obfuscation
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) {
            showToast('Error: ' + data.error, 'error');
            return;
        }
        currentResult = data;
        displayResult(data);
        generationCount++;
        updateStat('stat-generated', generationCount);
        showToast('Artifact generated: ' + data.filename, 'success');
    })
    .catch(err => {
        showToast('Request failed: ' + err.message, 'error');
    })
    .finally(() => {
        document.getElementById('generate-btn').disabled = false;
        document.getElementById('generate-btn').textContent = '⚡ Generate Artifact';
    });
}

function displayResult(data) {
    const output = document.getElementById('output-area');
    output.innerHTML = '';

    if (data.content) {
        // Truncate for display
        const maxDisplay = 5000;
        const display = data.content.length > maxDisplay
            ? data.content.substring(0, maxDisplay) + '\n\n... [output truncated, download for full]'
            : data.content;
        output.textContent = display;

        // Show warnings
        if (data.warnings && data.warnings.length > 0) {
            const ws = document.createElement('div');
            ws.style.marginTop = '12px';
            data.warnings.forEach(w => {
                const badge = document.createElement('span');
                badge.className = 'warning-badge';
                badge.textContent = '⚠ ' + w;
                ws.appendChild(badge);
            });
            output.appendChild(ws);
        }
    } else {
        output.innerHTML = '<span class="placeholder">No output generated.</span>';
    }

    // Stats
    const stats = document.getElementById('output-stats');
    stats.style.display = 'block';
    let statHtml = `📄 ${data.filename} | `;
    statHtml += `📏 ${formatBytes(data.size_bytes || 0)} | `;
    statHtml += `🔒 ${data.obfuscation || 'none'}`;
    if (data.analysis) {
        if (data.analysis.line_count) statHtml += ` | 📝 ${data.analysis.line_count} lines`;
        if (data.analysis.risk_score !== undefined) statHtml += ` | ⚠ Risk: ${data.analysis.risk_score}%`;
    }
    stats.innerHTML = statHtml;
}

function previewRequest() {
    if (!currentGenerator) return;

    const options = getConfigValues();
    const obfuscation = document.getElementById('obfuscation-level').value;

    fetch('/api/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            generator: currentGenerator,
            options: options,
            obfuscation: obfuscation
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) { showToast(data.error, 'error'); return; }
        const modal = document.getElementById('modal-overlay');
        document.getElementById('modal-title').textContent = 'Preview - ' + formatBytes(data.size_bytes || 0);
        document.getElementById('modal-body').textContent = data.preview || 'No preview available';
        modal.classList.add('show');
    })
    .catch(err => showToast('Preview failed', 'error'));
}

function closeModal() {
    document.getElementById('modal-overlay').classList.remove('show');
}

function copyOutput() {
    if (!currentResult || !currentResult.content) {
        showToast('Nothing to copy', 'info');
        return;
    }
    navigator.clipboard.writeText(currentResult.content)
        .then(() => showToast('Copied to clipboard', 'success'))
        .catch(() => {
            // Fallback
            const ta = document.createElement('textarea');
            ta.value = currentResult.content;
            document.body.appendChild(ta);
            ta.select();
            document.execCommand('copy');
            ta.remove();
            showToast('Copied to clipboard', 'success');
        });
}

function downloadOutput() {
    if (!currentResult) {
        showToast('Nothing to download', 'info');
        return;
    }

    fetch('/api/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            generator: currentGenerator,
            options: getConfigValues(),
            obfuscation: document.getElementById('obfuscation-level').value
        })
    })
    .then(r => {
        if (r.headers.get('Content-Type') === 'application/json') return r.json().then(d => { throw new Error(d.error); });
        const disposition = r.headers.get('Content-Disposition') || '';
        const match = disposition.match(/filename="?(.+?)"?$/);
        const filename = match ? match[1] : (currentResult.filename || 'payload.bin');
        return r.blob().then(blob => ({ blob, filename }));
    })
    .then(({ blob, filename }) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
        showToast('Downloaded: ' + filename, 'success');
    })
    .catch(err => showToast('Download failed: ' + err.message, 'error'));
}

function downloadBatch() {
    if (Object.keys(generators).length === 0) return;

    const requests = Object.entries(generators).slice(0, 3).map(([key]) => ({
        generator: key,
        options: {},
        obfuscation: 'base64'
    }));

    fetch('/api/download/batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ requests: requests })
    })
    .then(r => {
        if (!r.ok) throw new Error('Download failed');
        return r.blob();
    })
    .then(blob => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'omen_batch.zip';
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
        showToast('Batch download complete', 'success');
    })
    .catch(err => showToast('Batch failed: ' + err.message, 'error'));
}

function analyzeCurrent() {
    if (!currentResult || !currentResult.content) {
        showToast('Generate something first', 'info');
        return;
    }

    fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: currentResult.content })
    })
    .then(r => r.json())
    .then(data => {
        let html = '<div class="risk-meter">';
        const riskClass = data.risk_score >= 70 ? 'high' : (data.risk_score >= 40 ? 'medium' : 'low');
        html += `<div class="risk-score ${riskClass}">${data.risk_score}%</div>`;
        html += `<div class="risk-bar"><div class="risk-fill ${riskClass}" style="width:${data.risk_score}%"></div></div>`;
        html += '</div>';
        html += `<div style="font-size:13px;color:var(--text-secondary);margin-bottom:8px">${data.assessment || ''}</div>`;
        if (data.indicators && data.indicators.length > 0) {
            html += '<div style="font-size:12px"><strong>Indicators found:</strong><ul>';
            data.indicators.forEach(ind => {
                html += `<li style="margin:4px 0;padding-left:12px">${ind.pattern} — ${ind.description}</li>`;
            });
            html += '</ul></div>';
        }
        if (data.suggestions && data.suggestions.length > 0) {
            html += '<div style="font-size:12px;margin-top:8px"><strong>Suggestions:</strong><ul>';
            data.suggestions.forEach(s => html += `<li style="margin:4px 0;padding-left:12px">→ ${s}</li>`);
            html += '</ul></div>';
        }

        const modal = document.getElementById('modal-overlay');
        document.getElementById('modal-title').textContent = 'Risk Analysis';
        document.getElementById('modal-body').innerHTML = html;
        modal.classList.add('show');
    })
    .catch(err => showToast('Analysis failed', 'error'));
}

function clearOutput() {
    currentResult = null;
    document.getElementById('output-area').innerHTML = '<span class="placeholder">Artifact output will appear here...</span>';
    document.getElementById('output-stats').style.display = 'none';
    showToast('Output cleared', 'info');
}

function showToast(msg, type) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = 'toast ' + (type || 'info');
    toast.textContent = msg;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function updateStat(id, value) {
    const el = document.getElementById(id);
    if (el) el.querySelector('.stat-value').textContent = value;
}

function formatBytes(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
}

function setupObfuscation() {
    document.getElementById('obfuscation-level').addEventListener('change', function() {
        if (currentResult) {
            showToast('Obfuscation level changed. Re-generate to apply.', 'info');
        }
    });
}

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') closeModal();
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') generate();
        if ((e.ctrlKey || e.metaKey) && e.key === 'd') downloadOutput();
    });
}
