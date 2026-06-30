#!/usr/bin/env python3
"""
adb_crawler.py — 抓取 ADB Economics Working Papers 列表及详情

策略：
  ADB 全站有 Cloudflare 保护，必须用 headed 浏览器模式。
  每页用独立的浏览器实例，窗口移出屏幕避免打扰。
  失败时自动重试（刷新/新实例）。

使用方法:
    python scripts/adb_crawler.py                        # 抓取列表+摘要（默认2页）
    python scripts/adb_crawler.py --pages 3              # 抓取3页
    python scripts/adb_crawler.py --list-only            # 只抓列表
    python scripts/adb_crawler.py --no-description       # 跳过摘要
"""

import os, sys, json, time, hashlib, argparse
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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
    """创建新的浏览器实例（窗口移出屏幕，不 headless）"""
    from DrissionPage import Chromium, ChromiumOptions
    co = ChromiumOptions().auto_port()
    co.set_argument("--no-sandbox")
    co.set_argument("--disable-gpu")
    co.set_argument("--disable-blink-features=AutomationControlled")
    co.set_argument("--window-position=-3000,0")
    co.set_argument("--window-size=1920,1080")
    co.set_argument("--disable-extensions")
    co.set_argument("--no-first-run")
    co.set_argument("--disable-popup-blocking")
    return Chromium(addr_or_opts=co)


def wait_cloudflare(tab, timeout=50, refresh_at=20):
    """等待 Cloudflare 验证通过，超时后刷新一次"""
    for i in range(timeout // 2):
        time.sleep(2)
        title = tab.title.lower()
        if "economics" in title or "papers" in title:
            return True
        if refresh_at and (i * 2) == refresh_at:
            tab.refresh()
    return False


def try_get_page(page_num, max_retries=3):
    """尝试抓取一页列表，失败则重试"""
    if page_num == 0:
        url = "https://www.adb.org/publications/series/economics-working-papers"
    else:
        url = f"https://www.adb.org/publications/series/economics-working-papers?page={page_num}"

    for attempt in range(max_retries):
        browser = make_browser()
        tab = browser.latest_tab
        tab.get(url)

        ok = wait_cloudflare(tab)
        if not ok:
            browser.quit()
            continue

        time.sleep(3)

        papers = []
        for el in tab.eles("tag:a"):
            txt = el.text
            if not txt or not isinstance(txt, str):
                continue
            txt = txt.strip()
            if "Papers and Briefs |" not in txt:
                continue
            href = (el.attr("href") or "").strip()
            if not href:
                continue
            if href.startswith("/"):
                href = "https://www.adb.org" + href
            parts = txt.split("\n", 1)
            title = parts[1].strip() if len(parts) > 1 else ""
            if not title:
                continue

            header = parts[0]
            date_part = header.split("|", 1)[1].strip() if "|" in header else ""
            pub_date = ""
            for fmt in ["%d %b %Y", "%d %B %Y"]:
                try:
                    pub_date = datetime.strptime(date_part, fmt).strftime("%Y-%m-%d")
                    break
                except ValueError:
                    continue

            papers.append((title, pub_date, href))

        browser.quit()
        if papers:
            return papers

    return []


def fetch_descriptions(papers):
    """抓取每篇论文的摘要（一个浏览器实例）"""
    todo = [p for p in papers if not p.get("description")]
    if not todo:
        print("所有论文已有摘要，跳过")
        return papers

    print(f"需要抓取 {len(todo)} 篇论文的摘要")
    browser = make_browser()
    tab = browser.latest_tab

    # 先通过首页验证
    tab.get("https://www.adb.org/publications/series/economics-working-papers")
    wait_cloudflare(tab)

    success = 0
    try:
        for i, paper in enumerate(todo):
            url = paper["url"]
            print(f"  [{i+1}/{len(todo)}] {paper['title'][:55]}...", end=" ", flush=True)

            tab.get(url)
            time.sleep(5)

            desc = ""
            # meta description
            meta = tab.eles("css:meta[name='description']")
            if meta:
                c = (meta[0].attr("content") or "").strip()
                if len(c) > 30:
                    desc = c

            # og:description
            if not desc:
                og = tab.eles("css:meta[property='og:description']")
                if og:
                    c = (og[0].attr("content") or "").strip()
                    if len(c) > 30:
                        desc = c

            # CSS selectors for abstract
            if not desc:
                for sel in [".abstract", ".field-abstract",
                            ".field--name-field-abstract",
                            ".node__content p"]:
                    els = tab.eles(f"css:{sel}")
                    for el in els:
                        t = el.text
                        if t and isinstance(t, str) and len(t.strip()) > 30:
                            desc = t.strip()
                            break
                    if desc:
                        break

            # 找 Abstract 标题后的段落
            if not desc:
                for tag in tab.eles("css:h2, h3, strong"):
                    t = tag.text
                    if t and isinstance(t, str) and "abstract" in t.lower():
                        parent = tag.parent()
                        if parent:
                            for p_el in parent.eles("css:p"):
                                ct = p_el.text
                                if ct and isinstance(ct, str) and len(ct) > 40:
                                    desc = ct.strip()
                                    break
                        if desc:
                            break

            if desc:
                paper["description"] = desc
                success += 1
                print(f"[OK] {len(desc)} 字符")
            else:
                print("[无摘要]")

            if (i + 1) % 5 == 0 and i + 1 < len(todo):
                time.sleep(2)
    finally:
        browser.quit()

    print(f"摘要完成: {success}/{len(todo)} 篇")
    return papers


def make_paper_dict(title, date, url):
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    return {
        "id": f"adb-{url_hash}",
        "title": title,
        "url": url,
        "description": "",
        "date": date or "",
        "source": "ADB",
        "tags": ["economics", "development"],
        "featured": False,
    }


def scrape_adb_papers(max_pages=2, output_path=None, skip_details=False):
    if output_path is None:
        output_path = os.path.join(PROJECT_ROOT, "_data", "adb_papers.json")

    existing = load_existing(output_path)
    existing_urls = {p.get("url", "") for p in existing}
    print(f"已有 {len(existing)} 篇论文在数据文件中")
    print(f"其中 {sum(1 for p in existing if p.get('description'))} 篇有摘要")

    # 1. 抓取列表
    print("\n=== 抓取列表 ===")
    entries = []
    for page in range(max_pages):
        print(f"\n第{page+1}页:")
        papers = try_get_page(page)
        print(f"  获取到 {len(papers)} 篇")
        entries.extend(papers)

    # 去重
    seen_urls = set()
    unique_entries = []
    for t, d, u in entries:
        if u not in seen_urls:
            seen_urls.add(u)
            unique_entries.append((t, d, u))
    print(f"\n列表共 {len(unique_entries)} 篇唯一论文")

    # 合并已有数据（保留 description）
    merged = []
    for t, d, u in unique_entries:
        existing_desc = ""
        for ep in existing:
            if ep.get("url") == u and ep.get("description"):
                existing_desc = ep["description"]
                break
        paper = make_paper_dict(t, d, u)
        if existing_desc:
            paper["description"] = existing_desc
        merged.append(paper)

    # 2. 抓取摘要
    if not skip_details:
        print("\n=== 抓取摘要 ===")
        merged = fetch_descriptions(merged)

    save_papers(merged, output_path)
    return merged


def main():
    parser = argparse.ArgumentParser(description="ADB Economics Working Papers 爬虫")
    parser.add_argument("--pages", type=int, default=2)
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--list-only", action="store_true", help="只抓列表")
    parser.add_argument("--no-description", action="store_true", help="跳过摘要")
    args = parser.parse_args()

    scrape_adb_papers(
        max_pages=args.pages,
        output_path=args.output,
        skip_details=args.list_only or args.no_description,
    )


if __name__ == "__main__":
    main()
