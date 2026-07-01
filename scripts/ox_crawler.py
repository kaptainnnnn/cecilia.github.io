#!/usr/bin/env python3
"""ox_crawler.py — 抓取 Oxford Economics Working Papers（纯文本解析，高速）"""
import os, sys, json, time, hashlib, argparse, re
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_URL = "https://www.economics.ox.ac.uk/research/working-papers?filter_types-2448601[]=c-report&filter_series-2448601[]=1343026,1346531,1356606,1357171,1429171"


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


def parse_date(text):
    text = text.strip()
    for fmt in ["%d %b %Y", "%d %B %Y", "%B %Y", "%b %Y"]:
        try:
            dt = datetime.strptime(text, fmt)
            return dt.strftime("%Y-%m-%d") if "%d" in fmt else dt.strftime("%Y-%m")
        except ValueError:
            continue
    return text


def scrape_one_page(page_num, existing_titles):
    url = BASE_URL if page_num == 0 else f"{BASE_URL}&page-2448601={page_num}"
    print(f"  第{page_num+1}页: {url[:70]}...")

    browser = make_browser()
    tab = browser.latest_tab
    tab.get(url)
    time.sleep(5)

    # Cookie
    for btn in tab.eles("css:button"):
        if "accept optional" in (btn.text or "").lower():
            btn.click()
            time.sleep(1)
            break

    # 一次性获取所有 ORA 链接（按页面出现顺序）
    ora_urls = []
    for a in tab.eles("css:a[href*='ora.ox.ac.uk']"):
        href = (a.attr("href") or "").strip()
        if href:
            ora_urls.append(href)
    print(f"    {len(ora_urls)} 个 ORA 链接")

    # 获取所有 article 的文本（一次性提取，避免子元素查询）
    articles = tab.eles("css:article")
    texts = [a.text.strip() for a in articles]
    n = len(texts)
    print(f"    {n} 个 article")

    papers = []
    ora_idx = 0
    for i in range(0, n, 2):
        card_text = texts[i]
        detail_text = texts[i + 1] if i + 1 < n else ""

        if not card_text:
            continue

        card_lines = [l.strip() for l in card_text.split("\n") if l.strip()]

        # 标题 = 卡片第2行
        title = card_lines[1] if len(card_lines) > 1 else (card_lines[0] if card_lines else "")
        if not title or len(title) < 5:
            continue
        # 排除非标题行
        if title in ("|", "Working paper", "ORA record") or "Working Papers" in title:
            if len(card_lines) > 2:
                title = card_lines[2]
            else:
                continue

        if title in existing_titles:
            continue

        all_text = card_text + "\n" + detail_text

        # 日期
        date = ""
        for line in all_text.split("\n"):
            l = line.strip()
            if re.match(r'^\d{1,2}\s+\w+\s+202\d', l):
                date = parse_date(l)
                break
        if not date:
            for line in all_text.split("\n"):
                if "202" in line:
                    date = parse_date(line)
                    if date:
                        break

        # ORA 链接（按顺序匹配，每篇论文有2个相同链接，取第一个即可）
        url_link = ora_urls[ora_idx] if ora_idx < len(ora_urls) else ""
        ora_idx += 2  # 跳过 duplicate（card 和 detail 各一个）

        # 摘要
        abstract = ""
        for line in detail_text.split("\n"):
            l = line.strip()
            if len(l) > 80 and not l.startswith("http") and "Keywords" not in l and "Journal:" not in l:
                abstract = l
                break

        author = card_lines[2] if len(card_lines) > 2 else ""
        series = card_lines[0] if card_lines else ""

        pid = hashlib.md5((url_link or title).encode()).hexdigest()[:8]
        papers.append({
            "id": f"ox-{pid}",
            "title": title,
            "url": url_link,
            "description": abstract,
            "date": date or "",
            "authors": author,
            "series": series,
            "source": "Oxford",
            "tags": ["economics"],
        })

    browser.quit()
    return papers


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=int, default=2)
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    output_path = args.output or os.path.join(PROJECT_ROOT, "_data", "ox_papers.json")
    existing = load_existing(output_path)
    existing_titles = {p.get("title", "") for p in existing}
    print(f"已有 {len(existing)} 篇论文")

    all_papers = existing.copy()
    for page in range(args.pages):
        print(f"\n--- 第{page+1}页 ---")
        papers = scrape_one_page(page, existing_titles)
        for p in papers:
            existing_titles.add(p["title"])
        all_papers.extend(papers)
        print(f"  新增 {len(papers)} 篇")
        if not papers:
            print("  无数据，停止")
            break
        time.sleep(1)

    print(f"\n共新增 {len(all_papers) - len(existing)} 篇，总计 {len(all_papers)} 篇")
    save_papers(all_papers, output_path)


if __name__ == "__main__":
    main()
