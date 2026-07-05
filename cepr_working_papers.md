---
layout: page
title: "CEPR Discussion Papers"
permalink: /cepr-discussion-papers/
---

<div id="cepr-papers-container">
  <p class="page-subtitle">来自 Centre for Economic Policy Research 的 Discussion Papers，每日自动更新。</p>

  <div style="margin-bottom: 20px;">
    <input type="text" id="cepr-search" placeholder="搜索论文标题、摘要或作者…" style="width:100%;padding:10px 16px;border:1px solid #ddd;border-radius:8px;font-size:0.95rem;">
  </div>

  <div id="cepr-papers-list"></div>
  <div id="cepr-load-more-container" style="text-align:center;margin-top:20px;display:none;">
    <button id="cepr-load-more" style="padding:10px 30px;border:1px solid #ddd;border-radius:8px;background:#fff;cursor:pointer;font-size:0.95rem;">显示更多</button>
  </div>
</div>

<script>
const allPapers = {{ site.data.cepr_papers | jsonify }};

let visibleCount = 20;
const loadMoreCount = 30;

function renderPapers() {
  const container = document.getElementById('cepr-papers-list');
  const query = (document.getElementById('cepr-search').value || '').toLowerCase().trim();

  let filtered = allPapers;
  if (query) {
    filtered = allPapers.filter(p =>
      (p.title || '').toLowerCase().includes(query) ||
      (p.authors || '').toLowerCase().includes(query) ||
      (p.topics || []).join(' ').toLowerCase().includes(query)
    );
  }

  const toShow = filtered.slice(0, visibleCount);

  if (toShow.length === 0) {
    container.innerHTML = '<p style="color:#888;text-align:center;padding:40px 0;">没有找到匹配的论文。</p>';
    document.getElementById('cepr-load-more-container').style.display = 'none';
    return;
  }

  container.innerHTML = toShow.map(p => {
    const topics = (p.topics || []).filter(t => !/^[A-Z]\d+/.test(t)).slice(0, 3);
    const jelCodes = (p.topics || []).filter(t => /^[A-Z]\d+/.test(t)).slice(0, 5);

    return `
    <div style="border:2px solid #e0e0e0;border-radius:10px;padding:20px 24px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,0.06);">
      <h3 style="font-size:1rem;font-weight:600;margin-bottom:6px;line-height:1.5;">
        <a href="${p.url}" target="_blank" rel="noopener" style="color:#1d1d1f;text-decoration:none;">${p.title}</a>
      </h3>
      <div style="font-size:0.85rem;color:#6e6e73;margin-bottom:4px;">
        <span style="font-weight:600;color:#2563eb;">CEPR</span>
        <span> · </span>
        <span>${p.date || ''}</span>
        ${p.authors ? `<span> · ${p.authors}</span>` : ''}
      </div>
      ${topics.length > 0 ? `<div style="margin-top:8px;display:flex;flex-wrap:wrap;gap:6px;">${topics.map(t => `<span style="background:#eff6ff;color:#2563eb;font-size:0.78rem;padding:2px 10px;border-radius:20px;">${t}</span>`).join('')}</div>` : ''}
    </div>`;
  }).join('');

  const moreBtn = document.getElementById('cepr-load-more-container');
  if (visibleCount >= filtered.length) {
    moreBtn.style.display = 'none';
  } else {
    moreBtn.style.display = 'block';
  }
}

document.getElementById('cepr-search').addEventListener('input', () => {
  visibleCount = 20;
  renderPapers();
});

document.getElementById('cepr-load-more').addEventListener('click', () => {
  visibleCount += loadMoreCount;
  renderPapers();
});

renderPapers();
</script>
