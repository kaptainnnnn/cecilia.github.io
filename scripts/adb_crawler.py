#!/usr/bin/env python3
"""
adb_crawler.py — 抓取 ADB Economics Working Papers 列表

使用方法:
    python scripts/adb_crawler.py                          # 抓取最新论文
    python scripts/adb_crawler.py --pages 3                # 抓取前3页
    python scripts/adb_crawler.py --output _data/adb_papers.json  # 指定输出路径

依赖:
    pip install DrissionPage
"""

import os
import sys
import json
import time
import re
import argparse
from datetime import datetime

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_existing(output_path):
    """加载已有的论文数据，用于去重"""
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return []
    return []


def save_papers(papers, output_path):
    """保存论文数据（按日期降序）"""
    def sort_key(p):
        d = p.get("date", "")
        if not d:
            return "0000-00-00"
        return d
    papers.sort(key=sort_key, reverse=True)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(papers, f, indent=2, ensure_ascii=False)
    print(f"[OK] 已保存 {len(papers)} 篇论文到 {output_path}")


def parse_adb_date(text):
    """从 '29 Jun 2026' 格式文本中解析日期"""
    text = text.strip()
    for fmt in ["%d %b %Y", "%d %B %Y", "%B %d, %Y", "%Y-%m-%d"]:
        try:
            dt = datetime.strptime(text, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return ""


def extract_papers_from_page(driver, url):
    """用 DrissionPage 访问 ADB 页面，提取论文列表"""
    print(f"正在访问: {url}")
    driver.get(url)
    time.sleep(6)

    papers = []

    # 获取页面中所有指向 /publications/ 的链接
    all_links = driver.eles("css:a[href*='/publications/']")

    for link_el in all_links:
        full_text = link_el.text.strip()
        href = link_el.attr("href") or ""
        if not full_text or not href:
            continue

        # 跳过导航型链接（无 "Papers and Briefs |" 前缀）
        if "Papers and Briefs |" not in full_text:
            continue

        # 解析格式: "Papers and Briefs | 29 Jun 2026\nTitle More..."
        parts = full_text.split("\n", 1)
        header = parts[0]  # "Papers and Briefs | 29 Jun 2026"
        title = parts[1].strip() if len(parts) > 1 else ""

        # 从 header 中提取日期
        date_part = ""
        if "|" in header:
            date_part = header.split("|", 1)[1].strip()

        pub_date = parse_adb_date(date_part)

        # 补全链接
        if href.startswith("/"):
            href = "https://www.adb.org" + href

        if not title:
            continue

        papers.append({
            "id": f"adb-{hash(href) % 10000000:08d}",
            "title": title,
            "url": href,
            "description": "",
            "date": pub_date or datetime.now().strftime("%Y-%m-%d"),
            "source": "ADB",
            "tags": ["economics", "development"],
            "featured": False,
        })

    print(f"  本页提取到 {len(papers)} 篇论文")
    return papers


def scrape_adb_papers(max_pages=2, output_path=None, headless=False):
    """主函数：抓取 ADB 经济学工作论文，去重合并后保存"""
    from DrissionPage import Chromium, ChromiumOptions

    if output_path is None:
        output_path = os.path.join(PROJECT_ROOT, "_data", "adb_papers.json")

    existing = load_existing(output_path)
    existing_ids = {p.get("id", "") for p in existing}
    existing_urls = {p.get("url", "") for p in existing}
    print(f"已有 {len(existing)} 篇论文在数据文件中")

    # 启动浏览器（可选无头模式，CI 环境需要）
    print("启动浏览器...")
    co = ChromiumOptions().auto_port()
    if headless:
        co.set_argument("--headless=new")
        co.set_argument("--no-sandbox")
        co.set_argument("--disable-gpu")
        co.set_argument("--disable-dev-shm-usage")
    browser = Chromium(addr_or_opts=co)
    tab = browser.latest_tab

    new_count = 0
    all_papers = existing.copy()

    try:
        for page_num in range(max_pages):
            if page_num == 0:
                url = "https://www.adb.org/publications/series/economics-working-papers"
            else:
                url = f"https://www.adb.org/publications/series/economics-working-papers?page={page_num}"

            page_papers = extract_papers_from_page(tab, url)

            for p in page_papers:
                if p["url"] not in existing_urls:
                    all_papers.append(p)
                    existing_urls.add(p["url"])
                    existing_ids.add(p["id"])
                    new_count += 1

            if len(page_papers) == 0:
                print("  本页无数据，停止翻页")
                break

    finally:
        browser.quit()

    print(f"\n新增 {new_count} 篇，共 {len(all_papers)} 篇")
    save_papers(all_papers, output_path)
    return all_papers


def main():
    parser = argparse.ArgumentParser(description="抓取 ADB Economics Working Papers")
    parser.add_argument("--pages", type=int, default=2, help="抓取页数（每页约10篇，默认2）")
    parser.add_argument("--output", type=str, default=None, help="输出 JSON 路径")
    parser.add_argument("--headless", action="store_true", help="无头模式（CI 环境使用）")
    args = parser.parse_args()

    scrape_adb_papers(max_pages=args.pages, output_path=args.output, headless=args.headless)


if __name__ == "__main__":
    main()
