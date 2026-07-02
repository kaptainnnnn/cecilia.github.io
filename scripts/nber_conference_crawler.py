#!/usr/bin/env python3
"""nber_conference_crawler.py — 抓取 NBER Conferences"""
import os, sys, json, time, hashlib, argparse

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_URL = "https://www.nber.org/conferences?page={}&perPage=50&eventType=upcoming"


def load_existing(output_path):
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return []
    return []


def save_papers(papers, output_path):
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(papers, f, indent=2, ensure_ascii=False)
    print(f"[OK] 已保存 {len(papers)} 篇到 {output_path}")


def make_browser():
    from DrissionPage import Chromium, ChromiumOptions
    co = ChromiumOptions().auto_port()
    co.set_argument("--no-sandbox")
    co.set_argument("--disable-blink-features=AutomationControlled")
    co.set_argument("--window-position=-3000,0")
    co.set_argument("--window-size=1920,1080")
    return Chromium(addr_or_opts=co)


def try_get_page(page_num, existing_urls):
    url = BASE_URL.format(page_num)
    print(f"  第{page_num}页: {url}")

    for _ in range(2):
        browser = make_browser()
        tab = browser.latest_tab
        tab.get(url)
        time.sleep(4)

        cards = tab.eles("css:.event-card")
        if not cards:
            browser.quit()
            continue

        conferences = []
        for card in cards:
            title_el = card.eles("css:.event-card__title a")
            if not title_el:
                continue
            title = title_el[0].text.strip()
            href = (title_el[0].attr("href") or "").strip()
            url_link = "https://www.nber.org" + href if href.startswith("/") else href

            if url_link in existing_urls:
                continue

            date_els = card.eles("css:.event-card__label")
            date = date_els[0].text.strip() if len(date_els) > 0 else ""
            etype = date_els[1].text.strip() if len(date_els) > 1 else ""

            # 检查是否有 "Program"（绿色圆点）
            has_program = "Program" in card.text

            pid = hashlib.md5(url_link.encode()).hexdigest()[:8]
            conferences.append({
                "id": f"nber-conf-{pid}",
                "title": title,
                "url": url_link,
                "date": date,
                "type": etype,
                "has_program": has_program,
            })
            existing_urls.add(url_link)

        browser.quit()
        return conferences
    return []


def scrape(max_pages=2, output_path=None):
    if output_path is None:
        output_path = os.path.join(PROJECT_ROOT, "_data", "nber_conferences.json")

    existing = load_existing(output_path)
    existing_urls = {p.get("url", "") for p in existing if p.get("url")}
    print(f"已有 {len(existing)} 个会议")

    all_items = existing.copy()
    for page in range(1, max_pages + 1):
        print(f"\n--- 第{page}页 ---")
        items = try_get_page(page, existing_urls)
        if not items:
            print("  无数据")
            break
        all_items.extend(items)
        print(f"  新增 {len(items)} 个")
        time.sleep(1)

    print(f"\n共新增 {len(all_items) - len(existing)} 个，总计 {len(all_items)} 个")
    save_papers(all_items, output_path)


def main():
    parser = argparse.ArgumentParser(description="NBER Conferences 爬虫")
    parser.add_argument("--pages", type=int, default=2)
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()
    output_path = args.output or os.path.join(PROJECT_ROOT, "_data", "nber_conferences.json")
    scrape(max_pages=args.pages, output_path=output_path)


if __name__ == "__main__":
    main()
