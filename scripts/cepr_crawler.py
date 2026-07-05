#!/usr/bin/env python3
"""
cepr_crawler.py — 抓取 CEPR Discussion Papers

CEPR 网站基于 Drupal 10，使用 AJAX 分页加载论文列表。
需要用浏览器获取初始页面，然后通过点击分页链接触发 AJAX 加载更多。

使用方法:
    python scripts/cepr_crawler.py                          # 默认抓取前2页
    python scripts/cepr_crawler.py --pages 5                # 抓取前5页
    python scripts/cepr_crawler.py --all                    # 抓取全部（约1800页，慎用）
"""

import os, sys, json, time, hashlib, argparse, re
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_URL = "https://cepr.org/publications/discussion-papers"


def load_existing(output_path):
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return []
    return []


def save_papers(papers, output_path):
    papers.sort(key=lambda p: p.get("date", ""), reverse=True)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(papers, f, indent=2, ensure_ascii=False)
    print(f"[OK] 已保存 {len(papers)} 篇论文到 {output_path}")


def make_browser():
    from DrissionPage import Chromium, ChromiumOptions
    co = ChromiumOptions().auto_port()
    co.set_argument("--no-sandbox")
    co.set_argument("--disable-blink-features=AutomationControlled")
    co.set_argument("--window-position=-3000,0")
    co.set_argument("--window-size=1920,1080")
    return Chromium(addr_or_opts=co)


def parse_date(date_str):
    if not date_str:
        return ""
    date_str = date_str.strip()
    for fmt in ["%d %b %Y", "%d %B %Y", "%b %Y", "%B %Y"]:
        try:
            dt = datetime.strptime(date_str, fmt)
            if "%d" in fmt:
                return dt.strftime("%Y-%m-%d")
            return dt.strftime("%Y-%m")
        except ValueError:
            continue
    return date_str


def parse_papers_from_html(html, existing_urls=None):
    """从浏览器渲染的 HTML 中提取论文信息

    支持两种卡片格式：
    - c-compact-card: 初始页面（只有姓）
    - c-card: AJAX 加载的页面（完整信息含全名和JEL分类）
    """
    papers = []
    if existing_urls is None:
        existing_urls = set()

    article_pattern = re.compile(
        r'<article[^>]+data-history-node-id="(\d+)"[^>]+about="(/publications/dp\d+)"[^>]*>'
        r'(.*?)</article>',
        re.DOTALL
    )

    for match in article_pattern.finditer(html):
        about_path = match.group(2)
        inner = match.group(3)
        url = f"https://cepr.org{about_path}"

        if url in existing_urls:
            continue
        existing_urls.add(url)  # 防止同一次调用中出现重复

        # 标题 — 两种格式
        title_match = re.search(r'(?:c-compact-card__title-link|c-card__title-link)[^>]*>(.*?)</a>', inner, re.DOTALL)
        title_raw = title_match.group(1).strip() if title_match else ""
        # 去除 HTML 标签
        title = re.sub(r'<[^>]+>', '', title_raw).strip()
        if not title:
            continue

        # 作者 — 两种格式
        authors = [a.group(1) for a in re.finditer(r'(?:c-compact-card__meta-text--link|c-card__meta-text--link)[^>]*>([^<]+)</a>', inner)]

        # 日期
        date_match = re.search(r'<time[^>]+datetime="([^"]+)"', inner)
        date = parse_date(date_match.group(1)) if date_match else ""

        # 论文类型 — 两种格式
        type_match = re.search(r'(?:c-compact-card__footer-meta|c-card__sub-type)[^>]*>\s*([^<\s][^<]*?)\s*</(?:small|span)>', inner, re.DOTALL)
        ptype = type_match.group(1).strip() if type_match else "Discussion paper"

        # 主题/JEL分类（仅在 c-card 格式中有）
        topics = [t.group(1) for t in re.finditer(r'c-card__taxonomy-list-link[^>]*>([^<]+)</a>', inner)]

        pid = hashlib.md5(url.encode()).hexdigest()[:8]
        papers.append({
            "id": f"cepr-{pid}",
            "title": title,
            "url": url,
            "description": "",
            "date": date,
            "authors": "; ".join(authors) if authors else "",
            "series": "CEPR Discussion Papers",
            "source": "CEPR",
            "type": ptype,
            "topics": topics,
            "tags": ["economics"],
        })

    return papers


def scrape_papers(max_pages=2, output_path=None):
    if output_path is None:
        output_path = os.path.join(PROJECT_ROOT, "_data", "cepr_papers.json")

    existing = load_existing(output_path)
    existing_urls = {p.get("url", "") for p in existing if p.get("url")}
    print(f"已有 {len(existing)} 篇论文")

    browser = make_browser()
    tab = browser.latest_tab

    tab.get(BASE_URL)
    time.sleep(5)

    # 接受 Cookie
    try:
        for btn in tab.eles("css:button"):
            txt = (btn.text or "").lower()
            if "accept" in txt:
                btn.click()
                time.sleep(1)
                break
    except Exception:
        pass

    # 等待卡片加载
    for i in range(15):
        time.sleep(1)
        cards = tab.eles("css:article[about*='/publications/dp']")
        if len(cards) > 0:
            print(f"  页面加载完成，{len(cards)} 个卡片")
            break

    all_papers = existing.copy()
    total_new = 0
    scraped_urls = set(existing_urls)

    # 第1页：从初始 HTML 中解析
    html = tab.html
    papers = parse_papers_from_html(html, scraped_urls)

    for p in papers:
        scraped_urls.add(p["url"])
        for ep in existing:
            if ep.get("url") == p["url"] and ep.get("description"):
                p["description"] = ep["description"]
                break

    all_papers.extend(papers)
    total_new += len(papers)
    print(f"\n--- 第 1 页 ---  获取 {len(papers)} 篇（累计 {len(all_papers)} 篇）")

    # 后续页：通过 AJAX 点击翻页
    for page in range(1, max_pages):
        print(f"\n--- 第 {page+1} 页 ---")

        clicked = False
        for link in tab.eles("css:.c-pagination__button a"):
            href = link.attr("href") or ""
            m = re.search(r'page=(\d+)', href)
            if m and int(m.group(1)) == page:
                try:
                    tab.run_js("arguments[0].click();", link)
                    clicked = True
                except Exception as e:
                    print(f"  点击失败: {e}")
                break

        if not clicked:
            print("  找不到分页链接，停止翻页")
            break

        # 等待 AJAX 响应并更新 DOM
        time.sleep(8)

        # 从当前页面解析新文章
        html = tab.html
        new_papers = parse_papers_from_html(html, scraped_urls)

        for p in new_papers:
            scraped_urls.add(p["url"])
            for ep in existing:
                if ep.get("url") == p["url"] and ep.get("description"):
                    p["description"] = ep["description"]
                    break

        all_papers.extend(new_papers)
        total_new += len(new_papers)
        print(f"  获取 {len(new_papers)} 篇（累计 {len(all_papers)} 篇）")

        if not new_papers:
            print("  没有新文章，停止翻页")
            break

    browser.quit()
    print(f"\n共新增 {total_new} 篇，总计 {len(all_papers)} 篇")
    save_papers(all_papers, output_path)


def main():
    parser = argparse.ArgumentParser(description="CEPR Discussion Papers 爬虫")
    parser.add_argument("--pages", type=int, default=2,
                        help="抓取页数（默认2页）")
    parser.add_argument("--all", action="store_true",
                        help="抓取全部页（约1800页，慎用）")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    pages = 9999 if args.all else args.pages
    scrape_papers(max_pages=pages, output_path=args.output)


if __name__ == "__main__":
    main()
