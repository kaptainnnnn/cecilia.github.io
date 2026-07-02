---
layout: page
title: "OECD 经济学工作论文"
permalink: /oecd-working-papers/
---

<div id="oecd-papers-container">
  <p class="page-subtitle">来自 OECD 的经济学工作论文（Economics Department Working Papers 系列），每日自动更新。</p>

  <div style="margin-bottom: 20px;">
    <input type="text" id="oecd-search" placeholder="搜索论文标题或摘要…" style="width:100%;padding:10px 16px;border:1px solid #ddd;border-radius:8px;font-size:0.95rem;">
  </div>

  <div id="oecd-papers-list"></div>
  <div id="oecd-load-more-container" style="text-align:center;margin-top:20px;display:none;">
    <button id="oecd-load-more" style="padding:10px 30px;border:1px solid #ddd;border-radius:8px;background:#fff;cursor:pointer;font-size:0.95rem;">显示更多</button>
  </div>
</div>

<script>
const allOecdPapers = {{ site.data.oecd_papers | jsonify }};

let visibleCount = 20;
const loadMoreCount = 30;

function renderOecdPapers() {
  const container = document.getElementById('oecd-papers-list');
  const query = (document.getElementById('oecd-search').value || '').toLowerCase().trim();

  let filtered = allOecdPapers;
  if (query) {
    filtered = allOecdPapers.filter(p =>
      (p.title || '').toLowerCase().includes(query) ||
      (p.description || '').toLowerCase().includes(query) ||
      (p.authors || '').toLowerCase().includes(query)
    );
  }

  const toShow = filtered.slice(0, visibleCount);

  if (toShow.length === 0) {
    container.innerHTML = '<p style="color:#888;text-align:center;padding:40px 0;">没有找到匹配的论文。</p>';
    document.getElementById('oecd-load-more-container').style.display = 'none';
    return;
  }

  container.innerHTML = toShow.map(p => `
    <div style="border:2px solid #e0e0e0;border-radius:10px;padding:20px 24px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,0.06);">
      <h3 style="font-size:1rem;font-weight:600;margin-bottom:6px;line-height:1.5;">
        <a href="${p.url}" target="_blank" rel="noopener" style="color:#1d1d1f;text-decoration:none;">${p.title}</a>
      </h3>
      <div style="font-size:0.85rem;color:#6e6e73;margin-bottom:4px;">
        <span style="font-weight:600;color:#dc2626;">OECD</span>
        <span> · </span>
        <span>${p.date || ''}</span>
        ${p.authors ? `<span> · ${p.authors}</span>` : ''}
      </div>
      <div style="font-size:0.78rem;color:#9e9ea0;margin-bottom:6px;">
        ${p.series || ''}
      </div>
      ${p.description ? `<p style="font-size:0.88rem;color:#6e6e73;line-height:1.6;margin-top:8px;">${p.description.substring(0, 500)}${p.description.length > 500 ? '…' : ''}</p>` : ''}
      <div style="margin-top:8px;display:flex;flex-wrap:wrap;gap:6px;">
        <span style="background:#fef2f2;color:#dc2626;font-size:0.78rem;padding:2px 10px;border-radius:20px;">economics</span>
      </div>
    </div>
  `).join('');

  const moreBtn = document.getElementById('oecd-load-more-container');
  if (visibleCount >= filtered.length) {
    moreBtn.style.display = 'none';
  } else {
    moreBtn.style.display = 'block';
  }
}

document.getElementById('oecd-search').addEventListener('input', () => {
  visibleCount = 20;
  renderOecdPapers();
});

document.getElementById('oecd-load-more').addEventListener('click', () => {
  visibleCount += loadMoreCount;
  renderOecdPapers();
});

renderOecdPapers();
</script>
