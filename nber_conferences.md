---
layout: page
title: "NBER 学术会议"
permalink: /nber-conferences/
---

<div id="conf-container">
  <p class="page-subtitle">来自 National Bureau of Economic Research 的 upcoming 学术会议，每日自动更新。</p>

  <div style="margin-bottom: 20px;">
    <input type="text" id="conf-search" placeholder="搜索会议…" style="width:100%;padding:10px 16px;border:1px solid #ddd;border-radius:8px;font-size:0.95rem;">
  </div>

  <div id="conf-list"></div>
  <div id="conf-load-more-container" style="text-align:center;margin-top:20px;display:none;">
    <button id="conf-load-more" style="padding:10px 30px;border:1px solid #ddd;border-radius:8px;background:#fff;cursor:pointer;font-size:0.95rem;">显示更多</button>
  </div>
</div>

<script>
const allConfs = {{ site.data.nber_conferences | jsonify }};

let visibleCount = 20;
const loadMoreCount = 30;

function render() {
  const container = document.getElementById('conf-list');
  const query = (document.getElementById('conf-search').value || '').toLowerCase().trim();

  let filtered = allConfs;
  if (query) {
    filtered = allConfs.filter(p =>
      (p.title || '').toLowerCase().includes(query) ||
      (p.date || '').toLowerCase().includes(query)
    );
  }

  const toShow = filtered.slice(0, visibleCount);

  if (toShow.length === 0) {
    container.innerHTML = '<p style="color:#888;text-align:center;padding:40px 0;">没有找到匹配的会议。</p>';
    document.getElementById('conf-load-more-container').style.display = 'none';
    return;
  }

  container.innerHTML = toShow.map(p => `
    <div style="border:3px solid #e0e0e0;border-radius:10px;padding:20px 24px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,0.06);">
      <h3 style="font-size:1rem;font-weight:600;margin-bottom:6px;line-height:1.5;">
        <a href="${p.url}" target="_blank" rel="noopener" style="color:#1d1d1f;text-decoration:none;">${p.title}</a>
      </h3>
      <div style="font-size:0.85rem;color:#6e6e73;margin-bottom:4px;">
        <span style="font-weight:600;color:#059669;">NBER</span>
        <span> · </span>
        <span>${p.date || ''}</span>
        <span> · ${p.type || ''}</span>
        ${p.has_program ? '<span style="margin-left:8px;font-size:0.75rem;color:#059669;">● Program</span>' : ''}
      </div>
    </div>
  `).join('');

  const moreBtn = document.getElementById('conf-load-more-container');
  if (visibleCount >= filtered.length) {
    moreBtn.style.display = 'none';
  } else {
    moreBtn.style.display = 'block';
  }
}

document.getElementById('conf-search').addEventListener('input', () => { visibleCount = 20; render(); });
document.getElementById('conf-load-more').addEventListener('click', () => { visibleCount += loadMoreCount; render(); });
render();
</script>
