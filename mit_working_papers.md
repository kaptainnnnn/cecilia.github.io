---
layout: page
title: "MIT 工作论文"
permalink: /mit-working-papers/
---

<div id="mit-papers-container">
  <p class="page-subtitle">来自 MIT Economics Department 的 Faculty Working Papers，每日自动更新。</p>

  <div style="margin-bottom: 20px;">
    <input type="text" id="mit-search" placeholder="搜索论文标题、作者或教授姓名…" style="width:100%;padding:10px 16px;border:1px solid #ddd;border-radius:8px;font-size:0.95rem;">
  </div>

  <div id="mit-papers-list"></div>
  <div id="mit-load-more-container" style="text-align:center;margin-top:20px;display:none;">
    <button id="mit-load-more" style="padding:10px 30px;border:1px solid #ddd;border-radius:8px;background:#fff;cursor:pointer;font-size:0.95rem;">显示更多</button>
  </div>
</div>

<script>
const allMitPapers = {{ site.data.mit_papers | jsonify }};

let visibleCount = 20;
const loadMoreCount = 30;

function renderMitPapers() {
  const container = document.getElementById('mit-papers-list');
  const query = (document.getElementById('mit-search').value || '').toLowerCase().trim();

  let filtered = allMitPapers;
  if (query) {
    filtered = allMitPapers.filter(p =>
      (p.title || '').toLowerCase().includes(query) ||
      (p.authors || '').toLowerCase().includes(query) ||
      (p.faculty || '').toLowerCase().includes(query)
    );
  }

  const toShow = filtered.slice(0, visibleCount);

  if (toShow.length === 0) {
    container.innerHTML = '<p style="color:#888;text-align:center;padding:40px 0;">没有找到匹配的论文。</p>';
    document.getElementById('mit-load-more-container').style.display = 'none';
    return;
  }

  container.innerHTML = toShow.map(p => {
    const linkUrl = p.pdf_url || '#';
    const linkTarget = p.pdf_url ? 'target="_blank" rel="noopener"' : '';

    return `
    <div style="border:2px solid #e0e0e0;border-radius:10px;padding:20px 24px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,0.06);">
      <h3 style="font-size:1rem;font-weight:600;margin-bottom:6px;line-height:1.5;">
        <a href="${linkUrl}" ${linkTarget} style="color:#1d1d1f;text-decoration:none;">${p.title}</a>
      </h3>
      <div style="font-size:0.85rem;color:#6e6e73;margin-bottom:4px;display:flex;flex-wrap:wrap;gap:4px 8px;align-items:center;">
        <span style="font-weight:600;color:#7c3aed;">MIT</span>
        <span style="color:#ccc;">·</span>
        <span>${p.date || ''}</span>
        ${p.faculty ? `<span style="color:#ccc;">·</span><span>${p.faculty}</span>` : ''}
        ${p.authors ? `<span style="color:#ccc;">·</span><span>${p.authors}</span>` : ''}
      </div>
      <div style="margin-top:8px;display:flex;flex-wrap:wrap;gap:6px;">
        <span style="background:#f5f3ff;color:#7c3aed;font-size:0.78rem;padding:2px 10px;border-radius:20px;">MIT Economics</span>
      </div>
    </div>`;
  }).join('');

  const moreBtn = document.getElementById('mit-load-more-container');
  if (visibleCount >= filtered.length) {
    moreBtn.style.display = 'none';
  } else {
    moreBtn.style.display = 'block';
  }
}

document.getElementById('mit-search').addEventListener('input', () => {
  visibleCount = 20;
  renderMitPapers();
});

document.getElementById('mit-load-more').addEventListener('click', () => {
  visibleCount += loadMoreCount;
  renderMitPapers();
});

renderMitPapers();
</script>
