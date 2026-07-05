---
layout: page
title: 最新经济学工作论文
description: 自动聚合 NBER、CEPR、OECD、Oxford、ADB 最新经济学工作论文，每日更新。
image: /assets/images/og-preview.svg
---

<div id="papers-container">
  <p class="page-subtitle">来自 NBER、CEPR、OECD、Oxford、ADB 的最新工作论文。</p>

  <div style="margin-bottom:20px;">
    <input type="text" id="papers-search" placeholder="搜索论文标题、作者、来源…" style="width:100%;padding:10px 16px;border:1px solid #ddd;border-radius:8px;font-size:0.95rem;box-sizing:border-box;">
  </div>

  <div id="papers-stats" style="font-size:0.85rem;color:#6e6e73;margin-bottom:12px;"></div>
  <div id="papers-list"></div>
  <div id="papers-load-more" style="text-align:center;margin-top:20px;display:none;">
    <button id="papers-load-more-btn" style="padding:10px 30px;border:1px solid #ddd;border-radius:8px;background:#fff;cursor:pointer;font-size:0.95rem;transition:background 0.2s;" onmouseover="this.style.background='#f5f5f7'" onmouseout="this.style.background='#fff'">显示更多</button>
  </div>
</div>

<script>
(function() {
  // 聚合所有论文源
  var allPapers = [];

  function addSource(name, data) {
    if (!data || !data.length) return;
    for (var i = 0; i < data.length; i++) {
      var p = data[i];
      allPapers.push({
        title: p.title || '',
        url: p.url || '',
        authors: p.authors || '',
        date: p.date || '',
        source: p.source || name,
        description: p.description || '',
        series: p.series || '',
      });
    }
  }

  // 从 Jekyll 的 site.data 注入
  addSource('NBER', {{ site.data.nber_papers | jsonify }});
  addSource('CEPR', {{ site.data.cepr_papers | jsonify }});
  addSource('OECD', {{ site.data.oecd_papers | jsonify }});
  addSource('Oxford', {{ site.data.ox_papers | jsonify }});
  addSource('ADB', {{ site.data.adb_papers | jsonify }});

  // 按日期排序（最新的在前）
  allPapers.sort(function(a, b) { return b.date.localeCompare(a.date); });

  // ---- 状态 ----
  var visibleCount = 20;
  var loadMoreCount = 30;
  var currentQuery = '';

  // 颜色映射
  var sourceColors = {
    'NBER':   { bg: '#ecfdf5', text: '#059669' },
    'CEPR':   { bg: '#eff6ff', text: '#2563eb' },
    'OECD':   { bg: '#fef3c7', text: '#d97706' },
    'Oxford': { bg: '#f0fdf4', text: '#16a34a' },
    'ADB':    { bg: '#fef2f2', text: '#dc2626' },
  };
  function getSourceColor(s) {
    return sourceColors[s] || { bg: '#f5f5f7', text: '#515154' };
  }

  function filterPapers() {
    var q = currentQuery.toLowerCase().trim();
    if (!q) return allPapers;
    return allPapers.filter(function(p) {
      return (p.title || '').toLowerCase().includes(q) ||
             (p.authors || '').toLowerCase().includes(q) ||
             (p.source || '').toLowerCase().includes(q) ||
             (p.series || '').toLowerCase().includes(q) ||
             (p.description || '').toLowerCase().includes(q);
    });
  }

  function render() {
    var container = document.getElementById('papers-list');
    var stats = document.getElementById('papers-stats');
    var moreDiv = document.getElementById('papers-load-more');

    var filtered = filterPapers();
    var toShow = filtered.slice(0, visibleCount);

    // 统计
    if (currentQuery) {
      stats.textContent = '搜索 "' + currentQuery + '" 找到 ' + filtered.length + ' 篇论文';
    } else {
      stats.textContent = '共 ' + allPapers.length + ' 篇论文';
    }

    if (toShow.length === 0) {
      container.innerHTML = '<p style="color:#888;text-align:center;padding:40px 0;">没有找到匹配的论文。</p>';
      moreDiv.style.display = 'none';
      return;
    }

    container.innerHTML = toShow.map(function(p) {
      var c = getSourceColor(p.source);
      return '<div class="paper-card" style="border:2px solid #e0e0e0;border-radius:10px;padding:20px 24px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,0.06);">' +
        '<h3 style="font-size:1rem;font-weight:600;margin-bottom:6px;line-height:1.5;">' +
          '<a href="' + p.url + '" target="_blank" rel="noopener" style="color:#1d1d1f;text-decoration:none;">' + escHtml(p.title) + '</a>' +
        '</h3>' +
        '<div style="font-size:0.85rem;color:#6e6e73;margin-bottom:4px;display:flex;flex-wrap:wrap;gap:4px 8px;align-items:center;">' +
          '<span style="font-weight:600;color:' + c.text + ';">' + p.source + '</span>' +
          '<span style="color:#ccc;">·</span>' +
          '<span>' + (p.date || '') + '</span>' +
          (p.authors ? '<span style="color:#ccc;">·</span><span>' + escHtml(p.authors) + '</span>' : '') +
        '</div>' +
        (p.series ? '<div style="font-size:0.78rem;color:#9e9ea0;margin-bottom:4px;">' + escHtml(p.series) + '</div>' : '') +
        (p.description ? '<p style="font-size:0.88rem;color:#6e6e73;line-height:1.6;margin-top:8px;">' + escHtml(p.description) + '</p>' : '') +
        '<div style="margin-top:8px;display:flex;flex-wrap:wrap;gap:6px;">' +
          '<span style="background:' + c.bg + ';color:' + c.text + ';font-size:0.78rem;padding:2px 10px;border-radius:20px;">economics</span>' +
        '</div>' +
      '</div>';
    }).join('');

    if (visibleCount >= filtered.length) {
      moreDiv.style.display = 'none';
    } else {
      moreDiv.style.display = 'block';
    }
  }

  function escHtml(s) {
    if (!s) return '';
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  // 搜索
  document.getElementById('papers-search').addEventListener('input', function() {
    currentQuery = this.value;
    visibleCount = 20;
    render();
  });

  // 加载更多
  document.getElementById('papers-load-more-btn').addEventListener('click', function() {
    visibleCount += loadMoreCount;
    render();
  });

  render();
})();
</script>
