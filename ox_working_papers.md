---
layout: page
title: "Oxford 经济学工作论文"
permalink: /oxford-working-papers/
---

<div id="ox-papers-container">
  <p class="page-subtitle">来自 University of Oxford 的经济学工作论文（Department of Economics / CSAE / Oxford Economic and Social History 系列），每日自动更新。</p>

  <div style="margin-bottom: 20px;">
    <input type="text" id="ox-search" placeholder="搜索论文标题、摘要或作者…" style="width:100%;padding:10px 16px;border:1px solid #ddd;border-radius:8px;font-size:0.95rem;">
  </div>

  <div id="ox-papers-list"></div>
  <div id="ox-load-more-container" style="text-align:center;margin-top:20px;display:none;">
    <button id="ox-load-more" style="padding:10px 30px;border:1px solid #ddd;border-radius:8px;background:#fff;cursor:pointer;font-size:0.95rem;">显示更多</button>
  </div>
</div>

<script>
const allOxPapers = {{ site.data.ox_papers | jsonify }};

let visibleCount = 20;
const loadMoreCount = 30;

function renderOxPapers() {
  const container = document.getElementById('ox-papers-list');
  const query = (document.getElementById('ox-search').value || '').toLowerCase().trim();

  let filtered = allOxPapers;
  if (query) {
    filtered = allOxPapers.filter(p =>
      (p.title || '').toLowerCase().includes(query) ||
      (p.description || '').toLowerCase().includes(query) ||
      (p.authors || '').toLowerCase().includes(query)
    );
  }

  const toShow = filtered.slice(0, visibleCount);

  if (toShow.length === 0) {
    container.innerHTML = '<p style="color:#888;text-align:center;padding:40px 0;">没有找到匹配的论文。</p>';
    document.getElementById('ox-load-more-container').style.display = 'none';
    return;
  }

  container.innerHTML = toShow.map(p => `
    <div style="border:1px solid #e0e0e0;border-radius:10px;padding:20px 24px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,0.06);">
      <h3 style="font-size:1.05rem;font-weight:600;margin-bottom:6px;line-height:1.5;">
        ${p.url ? `<a href="${p.url}" target="_blank" rel="noopener" style="color:#1d1d1f;text-decoration:none;">${p.title}</a>`
                : `<span style="color:#1d1d1f;">${p.title}</span>`}
      </h3>
      <div style="font-size:0.85rem;color:#6e6e73;margin-bottom:4px;">
        <span style="font-weight:600;color:#8b5cf6;">Oxford</span>
        <span> · </span>
        <span>${p.date || ''}</span>
        ${p.authors ? `<span> · ${p.authors}</span>` : ''}
      </div>
      <div style="font-size:0.78rem;color:#9e9ea0;margin-bottom:6px;">
        ${p.series || ''}
      </div>
      ${p.description ? `<p style="font-size:0.9rem;color:#6e6e73;line-height:1.6;margin-top:8px;">${p.description}</p>` : ''}
      <div style="margin-top:8px;display:flex;flex-wrap:wrap;gap:6px;">
        <span style="background:#f5f3ff;color:#7c3aed;font-size:0.78rem;padding:2px 10px;border-radius:20px;">economics</span>
      </div>
    </div>
  `).join('');

  const moreBtn = document.getElementById('ox-load-more-container');
  if (visibleCount >= filtered.length) {
    moreBtn.style.display = 'none';
  } else {
    moreBtn.style.display = 'block';
  }
}

document.getElementById('ox-search').addEventListener('input', () => {
  visibleCount = 20;
  renderOxPapers();
});

document.getElementById('ox-load-more').addEventListener('click', () => {
  visibleCount += loadMoreCount;
  renderOxPapers();
});

renderOxPapers();
</script>
