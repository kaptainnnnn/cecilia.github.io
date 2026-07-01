---
layout: page
title: "Oxford 经济学工作论文"
permalink: /oxford-working-papers/
---

<div id="ox-papers-container">
  <p class="page-subtitle">来自 University of Oxford 的经济学工作论文（Department of Economics / CSAE / Oxford Economic and Social History 系列），每日自动更新。</p>

  <div style="margin-bottom: 20px;">
    <input type="text" id="ox-search" class="search-input" placeholder="搜索论文标题、摘要或作者…">
  </div>

  <div id="ox-papers-list"></div>
  <div class="load-more-container" id="ox-load-more-container" style="display:none;">
    <button id="ox-load-more" class="load-more-btn">显示更多</button>
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
    container.innerHTML = '<p class="empty-result">没有找到匹配的论文。</p>';
    document.getElementById('ox-load-more-container').style.display = 'none';
    return;
  }

  container.innerHTML = toShow.map(p => `
    <div class="paper-card">
      <h3 class="paper-title">
        ${p.url ? `<a href="${p.url}" target="_blank" rel="noopener">${p.title}</a>`
                : p.title}
      </h3>
      <div class="paper-meta">
        <span class="paper-source oxford">Oxford</span>
        <span> · </span>
        <span>${p.date || ''}</span>
        ${p.authors ? `<span> · ${p.authors}</span>` : ''}
      </div>
      <div class="paper-series">${p.series || ''}</div>
      ${p.description ? `<p class="paper-abstract">${p.description}</p>` : ''}
      <div class="paper-tags">
        <span class="paper-tag oxford">economics</span>
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
