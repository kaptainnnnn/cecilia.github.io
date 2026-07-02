#!/usr/bin/env python3
"""
nber_crawler.py — 抓取 NBER Working Papers

NBER 无 Cloudflare，页面渲染快。
每页用独立浏览器实例翻页。每页最多50篇。

API 端点（在浏览器中可用）:
  /api/v1/working_page_listing/contentType/working_paper/_/_/search

使用方法:
    python scripts/nber_crawler.py                          # 默认抓取2页（100篇）
    python scripts/nber_crawler.py --pages 5                # 抓取5页
    python scripts/nber_crawler.py --all                    # 抓取全部
"""

import os, sys, json, time, hashlib, argparse, re
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_URL = "https://www.nber.org/papers?page={}&perPage=50&sortBy=public_date"


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


def parse_nber_date(text):
    """解析 "June 2026" 格式日期"""
    text = text.strip()
    for fmt in ["%B %Y", "%b %Y", "%d %B %Y", "%d %b %Y"]:
        try:
            dt = datetime.strptime(text, fmt)
            if "%d" in fmt:
                return dt.strftime("%Y-%m-%d")
            return dt.strftime("%Y-%m")
        except ValueError:
            continue
    return text


def try_get_page(page_num, existing_urls, max_retries=2):
    """抓取一页"""
    url = BASE_URL.format(page_num)
    print(f"  第{page_num}页: {url}")

    for attempt in range(max_retries):
        browser = make_browser()
        tab = browser.latest_tab
        tab.get(url)
        time.sleep(4)

        # 等待 digest-card 渲染
        for i in range(10):
            time.sleep(1)
            cards = tab.eles("css:.digest-card")
            if len(cards) > 0:
                break

        html = tab.html

        # 提取所有 digest-card 的文本
        papers = []
        cards = tab.eles("css:.digest-card")
        print(f"    找到 {len(cards)} 个卡片")

        for card in cards:
            text = card.text.strip()
            if not text:
                continue

            lines = [l.strip() for l in text.split("\n") if l.strip()]
            if not lines:
                continue

            title = lines[0] if lines else ""
            if not title or len(title) < 10:
                continue
            if title in existing_urls:  # 用 title 去重
                continue

            # 找 NBER URL
            url_link = ""
            for a in card.eles("tag:a"):
                href = (a.attr("href") or "").strip()
                if "/papers/w" in href:
                    url_link = "https://www.nber.org" + href if href.startswith("/") else href
                    break

            if url_link in existing_urls:
                continue

            # 日期：第2行通常是 "June 2026 - Working Paper"
            date = ""
            if len(lines) > 1:
                date_part = lines[1].split(" - ")[0].strip()
                date = parse_nber_date(date_part)

            # 作者：找含 "Author(s)" 的行
            author = ""
            for line in lines:
                if line.startswith("Author(s)") or line.startswith("Author"):
                    author = line.replace("Author(s)", "").replace("Author", "").strip(" - ")
                    break

            # 摘要：找最长的行
            abstract = ""
            for line in lines:
                if len(line) > 80 and "Author" not in line:
                    abstract = line
                    break

            pid = hashlib.md5((url_link or title).encode()).hexdigest()[:8]
            papers.append({
                "id": f"nber-{pid}",
                "title": title,
                "url": url_link,
                "description": abstract,
                "date": date or "",
                "authors": author,
                "series": "NBER Working Papers",
                "source": "NBER",
                "tags": ["economics"],
            })
            if url_link:
                existing_urls.add(url_link)

        browser.quit()
        if papers:
            return papers

    return []


def get_total_pages():
    """获取总页数"""
    browser = make_browser()
    tab = browser.latest_tab
    tab.get(BASE_URL.format(1))
    time.sleep(4)
    html = tab.html
    m = re.search(r'(\d[\d,]*)\s+results?\s+found', html, re.I)
    browser.quit()
    if m:
        total = int(m.group(1).replace(",", ""))
        pages = (total + 49) // 50
        print(f"共 {total} 篇论文，{pages} 页")
        return pages
    return 1


def scrape_papers(max_pages=2, output_path=None):
    if output_path is None:
        output_path = os.path.join(PROJECT_ROOT, "_data", "nber_papers.json")

    existing = load_existing(output_path)
    existing_urls = {p.get("url", "") for p in existing if p.get("url")}
    print(f"已有 {len(existing)} 篇论文")

    all_papers = existing.copy()
    for page in range(1, max_pages + 1):
        print(f"\n--- 第{page}页 ---")
        papers = try_get_page(page, existing_urls)
        if not papers:
            print("  无数据，停止")
            break
        all_papers.extend(papers)
        print(f"  新增 {len(papers)} 篇")
        time.sleep(1)

    print(f"\n共新增 {len(all_papers) - len(existing)} 篇，总计 {len(all_papers)} 篇")
    save_papers(all_papers, output_path)


def main():
    parser = argparse.ArgumentParser(description="NBER Working Papers 爬虫")
    parser.add_argument("--pages", type=int, default=2)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    output_path = args.output or os.path.join(PROJECT_ROOT, "_data", "nber_papers.json")
    pages = args.pages
    if args.all:
        pages = get_total_pages()
    scrape_papers(max_pages=pages, output_path=output_path)


if __name__ == "__main__":
    main()
