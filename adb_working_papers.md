---
layout: page
title: "ADB 经济学工作论文"
permalink: /adb-working-papers/
---

<div id="adb-papers-container">
  <p class="page-subtitle">来自 Asian Development Bank 的经济学工作论文，每日自动更新。</p>

  <div style="margin-bottom: 20px;">
    <input type="text" id="adb-search" class="search-input" placeholder="搜索论文标题或摘要…">
  </div>

  <div id="adb-papers-list"></div>
  <div class="load-more-container" id="adb-load-more-container" style="display:none;">
    <button id="adb-load-more" class="load-more-btn">显示更多</button>
  </div>
</div>

<script>
const allAdbPapers = {{ site.data.adb_papers | jsonify }};

let visibleCount = 20;
const loadMoreCount = 30;

function renderAdbPapers() {
  const container = document.getElementById('adb-papers-list');
  const query = (document.getElementById('adb-search').value || '').toLowerCase().trim();

  let filtered = allAdbPapers;
  if (query) {
    filtered = allAdbPapers.filter(p =>
      (p.title || '').toLowerCase().includes(query) ||
      (p.description || '').toLowerCase().includes(query)
    );
  }

  const toShow = filtered.slice(0, visibleCount);

  if (toShow.length === 0) {
    container.innerHTML = '<p class="empty-result">没有找到匹配的论文。</p>';
    document.getElementById('adb-load-more-container').style.display = 'none';
    return;
  }

  container.innerHTML = toShow.map(p => `
    <div class="paper-card">
      <h3 class="paper-title">
        <a href="${p.url}" target="_blank" rel="noopener">${p.title}</a>
      </h3>
      <div class="paper-meta">
        <span class="paper-source adb">ADB</span>
        <span> · </span>
        <span>${p.date || ''}</span>
      </div>
      ${p.description ? `<p class="paper-abstract">${p.description}</p>` : ''}
      <div class="paper-tags">
        ${(p.tags || []).map(t => `<span class="paper-tag economics">${t}</span>`).join('')}
      </div>
    </div>
  `).join('');

  const moreBtn = document.getElementById('adb-load-more-container');
  if (visibleCount >= filtered.length) {
    moreBtn.style.display = 'none';
  } else {
    moreBtn.style.display = 'block';
  }
}

document.getElementById('adb-search').addEventListener('input', () => {
  visibleCount = 20;
  renderAdbPapers();
});

document.getElementById('adb-load-more').addEventListener('click', () => {
  visibleCount += loadMoreCount;
  renderAdbPapers();
});

renderAdbPapers();
</script>
