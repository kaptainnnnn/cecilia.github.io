---
layout: page
title: "ADB 经济学工作论文"
permalink: /adb-working-papers/
---

<div id="adb-papers-container">
  <p class="page-subtitle">来自 Asian Development Bank 的经济学工作论文，每日自动更新。</p>

  <div style="margin-bottom: 20px;">
    <input type="text" id="adb-search" placeholder="搜索论文标题或摘要…" style="width:100%;padding:10px 16px;border:1px solid #ddd;border-radius:8px;font-size:0.95rem;">
  </div>

  <div id="adb-papers-list"></div>
  <div id="adb-load-more-container" style="text-align:center;margin-top:20px;display:none;">
    <button id="adb-load-more" style="padding:10px 30px;border:1px solid #ddd;border-radius:8px;background:#fff;cursor:pointer;font-size:0.95rem;">显示更多</button>
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
    container.innerHTML = '<p style="color:#888;text-align:center;padding:40px 0;">没有找到匹配的论文。</p>';
    document.getElementById('adb-load-more-container').style.display = 'none';
    return;
  }

  container.innerHTML = toShow.map(p => `
    <div style="border:2px solid #e0e0e0;border-radius:10px;padding:20px 24px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,0.06);">
      <h3 style="font-size:1rem;font-weight:600;margin-bottom:6px;line-height:1.5;">
        <a href="${p.url}" target="_blank" rel="noopener" style="color:#1d1d1f;text-decoration:none;">${p.title}</a>
      </h3>
      <div style="font-size:0.85rem;color:#6e6e73;margin-bottom:6px;">
        <span style="font-weight:600;color:#2563eb;">ADB</span>
        <span> · </span>
        <span>${p.date || ''}</span>
      </div>
      ${p.description ? `<p style="font-size:0.88rem;color:#6e6e73;line-height:1.6;">${p.description}</p>` : ''}
      <div style="margin-top:8px;display:flex;flex-wrap:wrap;gap:6px;">
        ${(p.tags || []).map(t => `<span style="background:#eef2ff;color:#4338ca;font-size:0.78rem;padding:2px 10px;border-radius:20px;">${t}</span>`).join('')}
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
