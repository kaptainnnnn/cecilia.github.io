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


def extract_papers_from_page(driver, url):
    """用 DrissionPage 访问 ADB 页面，提取论文列表"""
    print(f"正在访问: {url}")
    driver.get(url)
    driver.wait.load_complete()

    # 等待论文列表加载（ADB 页面结构：class 含有 card 或 teaser 的条目）
    driver.wait.doc_loaded()

    papers = []

    # ADB 论文列表的选择器 —— 根据页面结构定位
    # 常见结构：每个条目是一个 <article> 或 <div> 带有 title 和 description
    items = driver.eles("css:.c-teaser__title a, .card__title a, h3 a, h2 a")
    descriptions = driver.eles("css:.c-teaser__description, .card__description, .field--name-field-description p, .teaser__description")
    dates = driver.eles("css:.c-teaser__date time, .card__date time, time")

    if not items:
        # 尝试更通用的选择器：页面中所有指向 /publications/ 的链接
        items = driver.eles("css:a[href*='/publications/']")

    # 如果还是找不到，打印页面快照帮助调试
    if not items:
        print("[!] 未找到论文条目，打印页面片段用于调试:")
        body_text = driver.eles("css:body")[0].text if driver.eles("css:body") else ""
        print(body_text[:1000] if body_text else "页面为空")
        return papers

    for i, item in enumerate(items):
        title = item.text.strip()
        link = item.attr("href") or ""
        if not title or not link:
            continue

        # 补全相对链接
        if link.startswith("/"):
            link = "https://www.adb.org" + link

        # 提取描述（如果有对应索引）
        desc = ""
        if i < len(descriptions):
            desc = descriptions[i].text.strip()

        # 提取日期
        pub_date = ""
        if i < len(dates):
            date_text = dates[i].attr("datetime") or dates[i].text.strip()
            if date_text:
                # 尝试解析多种日期格式
                for fmt in ["%Y-%m-%d", "%d %B %Y", "%B %d, %Y", "%Y/%m/%d"]:
                    try:
                        dt = datetime.strptime(date_text.strip(), fmt)
                        pub_date = dt.strftime("%Y-%m-%d")
                        break
                    except ValueError:
                        continue
                if not pub_date:
                    pub_date = date_text[:10]  # 取前10个字符

        papers.append({
            "id": f"adb-{hash(link) % 10000000:08d}",
            "title": title,
            "url": link,
            "description": desc,
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
