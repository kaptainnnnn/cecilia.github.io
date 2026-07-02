#!/usr/bin/env python3
"""
oecd_crawler.py — 抓取 OECD Economics Department Working Papers

通过 OECD WebCMS API 获取数据，无需浏览器。
API: GET https://api.oecd.org/webcms/search/faceted-search
  facets=oecd-serials:g17270e4 → OECD Economics Department Working Papers
  共约 1845 篇论文，每页 100 条，约 19 页。

使用方法:
    python scripts/oecd_crawler.py                          # 默认抓取全部
    python scripts/oecd_crawler.py --pages 5                # 只抓前5页
"""

import os, sys, json, time, hashlib, argparse, requests
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_URL = "https://api.oecd.org/webcms/search/faceted-search"


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


def parse_date(dt_str):
    """解析 ISO 日期"""
    if not dt_str:
        return ""
    for fmt in ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"]:
        try:
            return datetime.strptime(dt_str[:19] + ("Z" if "Z" in dt_str else ""),
                                     "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")
        except ValueError:
            continue
    return dt_str[:10]


def api_params(page=0, page_size=100):
    """构建 API 参数"""
    return [
        ("siteName", "oecd"),
        ("interfaceLanguage", "en"),
        ("orderBy", "mostRecent"),
        ("pageSize", str(page_size)),
        ("page", str(page)),
        ("hiddenFacets", "oecd-search-config-pillars:publications"),
        ("facets", "oecd-serials:g17270e4"),
        ("facets", "oecd-languages:en"),
    ]


def fetch_page(page=0, page_size=100, max_retries=3):
    """调用 API 抓取一页"""
    for attempt in range(max_retries):
        try:
            r = requests.get(API_URL, params=api_params(page, page_size),
                             headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
            if r.status_code == 200:
                return r.json()
            print(f"  API {r.status_code}，重试 {attempt+1}")
            time.sleep(2)
        except Exception as e:
            print(f"  请求失败: {e}，重试 {attempt+1}")
            time.sleep(2)
    return None


def scrape_papers(max_pages=None, output_path=None):
    if output_path is None:
        output_path = os.path.join(PROJECT_ROOT, "_data", "oecd_papers.json")

    existing = load_existing(output_path)
    existing_urls = {p.get("url", "") for p in existing if p.get("url")}
    print(f"已有 {len(existing)} 篇论文")

    # 先获取第一页得到总数
    data = fetch_page(page=0, page_size=1)
    if not data:
        print("API 请求失败")
        return

    total = data.get("total", 0)
    page_size = 100
    total_pages = (total + page_size - 1) // page_size
    if max_pages:
        total_pages = min(total_pages, max_pages)
    print(f"共 {total} 篇论文，{total_pages} 页")

    all_papers = existing.copy()
    total_new = 0

    for page in range(total_pages):
        print(f"\n--- 第 {page+1}/{total_pages} 页 ---")
        if page == 0:
            data = fetch_page(page=0, page_size=page_size)
        else:
            time.sleep(0.5)
            data = fetch_page(page=page, page_size=page_size)

        if not data:
            print("  请求失败，停止")
            break

        results = data.get("results", [])
        for item in results:
            url = (item.get("url") or "").strip()
            if not url:
                continue
            if url in existing_urls:
                continue

            title = item.get("title", "").strip()
            description = item.get("description", "").strip()
            pub_date = parse_date(item.get("publicationDateTime", ""))
            authors = item.get("authors", [])
            # 过滤非 economics 内容
            tags = [t.get("id", "") for t in item.get("tags", [])]
            if "oecd-policy-areas:pa5" not in tags:
                # 允许没有 policy area tag 的（有些工作论文没有）
                pass

            all_papers.append({
                "id": f"oecd-{hashlib.md5(url.encode()).hexdigest()[:8]}",
                "title": title,
                "url": url,
                "description": description,
                "date": pub_date or "",
                "authors": "; ".join(authors) if authors else "",
                "series": "OECD Economics Department Working Papers",
                "source": "OECD",
                "tags": ["economics"],
            })
            existing_urls.add(url)
            total_new += 1

        print(f"  本页 {len(results)} 条，新增 {len(results)} 篇")

    print(f"\n共新增 {total_new} 篇，总计 {len(all_papers)} 篇")
    save_papers(all_papers, output_path)


def main():
    parser = argparse.ArgumentParser(description="OECD Working Papers 爬虫")
    parser.add_argument("--pages", type=int, default=None,
                        help="抓取页数（默认全部，每页100条）")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    output_path = args.output or os.path.join(PROJECT_ROOT, "_data", "oecd_papers.json")
    scrape_papers(max_pages=args.pages, output_path=output_path)


if __name__ == "__main__":
    main()
