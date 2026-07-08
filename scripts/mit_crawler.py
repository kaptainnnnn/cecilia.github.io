"""
MIT Economics Faculty Working Papers Crawler
抓取所有MIT经济系教师的Working Papers，按日期排序显示最新50篇
"""
import requests
from bs4 import BeautifulSoup
import re
import json
import sys
import io
import time
import os

# 解决 Windows 终端编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_URL = "https://economics.mit.edu"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}
MONTH_MAP = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12,
}
OUTPUT_FILE = '_data/mit_papers.json'
PAPER_URL_PATHS = ['working-papers', 'publications', 'papers', 'research']


def fetch_soup(url, timeout=30):
    """请求 URL 并返回 BeautifulSoup 对象，失败返回 None"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        return BeautifulSoup(r.text, 'html.parser')
    except Exception as e:
        print(f"   请求失败: {url} — {e}")
        return None


def extract_faculty_info(a_tag):
    """从 <a> 标签中提取单个教授的基本信息"""
    href = a_tag.get('href', '')
    slug_match = re.match(r'/people/faculty/([^/]+)$', href)

    info = {
        'name': '',
        'title': '',
        'research_fields': [],
        'slug': slug_match.group(1) if slug_match else '',
        'url': f"{BASE_URL}{href}" if slug_match else '',
    }

    # 提取姓名
    name_el = a_tag.find('h3', class_='profile-teaser__name')
    if name_el:
        name = ''.join(name_el.find_all(string=True, recursive=False)).strip()
        info['name'] = name or name_el.get_text(strip=True)

    # 提取职称
    title_el = a_tag.find('h4', class_='profile-teaser__title')
    if title_el:
        info['title'] = title_el.get_text(strip=True)

    # 提取研究领域（以 <br> 分隔）
    cat_el = a_tag.find('div', class_='profile-teaser__categories')
    if cat_el:
        items_el = cat_el.find('p', class_='profile-teaser__categories-items')
        if items_el:
            fields = []
            current = []
            for child in items_el.children:
                if child.name == 'br':
                    if current:
                        fields.append(''.join(current).strip())
                        current = []
                elif isinstance(child, str):
                    current.append(child.strip())
            if current:
                fields.append(''.join(current).strip())
            info['research_fields'] = [f for f in fields if f]

    return info


def get_faculty_list():
    """从教师列表页爬取所有教授信息"""
    soup = fetch_soup(f"{BASE_URL}/people/faculty")
    if not soup:
        print("无法获取教授列表页面")
        return []

    container = soup.find('div', class_='faculty-landing__content')
    if not container:
        print("未找到 faculty-landing__content 容器")
        return []

    faculty = []
    seen_slugs = set()
    for a_tag in container.find_all('a', href=True):
        slug_match = re.match(r'/people/faculty/([^/]+)$', a_tag['href'])
        if slug_match and slug_match.group(1) not in seen_slugs:
            seen_slugs.add(slug_match.group(1))
            info = extract_faculty_info(a_tag)
            if info['name'] and len(info['name']) > 2:
                faculty.append(info)
    return faculty


def parse_date(date_text):
    """将日期字符串解析为 (year, month) 元组，用于排序"""
    if not date_text:
        return (0, 0)
    dm = re.match(r'(\w+)\s+(\d{4})', date_text.strip())
    if dm:
        month = MONTH_MAP.get(dm.group(1).lower(), 1)
        return (int(dm.group(2)), month)
    return (0, 0)


def extract_paper(teaser, faculty_name, slug):
    """从单个 publication-teaser 中提取论文信息"""
    title_el = teaser.find('h3', class_='publication-teaser__title')
    authors_el = teaser.find('div', class_='publication-teaser__authors')
    date_el = teaser.find('div', class_='publication-teaser__date')

    title = title_el.get_text(strip=True) if title_el else ''
    if not title:
        return None

    # PDF 链接
    title_a = teaser.find('a', href=True)
    pdf_url = ''
    if title_a and title_a['href'].endswith('.pdf'):
        href = title_a['href']
        pdf_url = href if href.startswith('http') else f"{BASE_URL}{href}"

    date_text = date_el.get_text(strip=True) if date_el else ''
    year, month = parse_date(date_text)

    return {
        'title': title,
        'authors': authors_el.get_text(strip=True) if authors_el else '',
        'date': date_text,
        'year': year,
        'month': month,
        'pdf_url': pdf_url,
        'faculty': faculty_name,
        'faculty_slug': slug,
    }


def get_professor_papers(slug, faculty_name):
    """获取单个教授的所有 working papers（尝试多个 URL 路径）"""
    for path in PAPER_URL_PATHS:
        url = f"{BASE_URL}/people/faculty/{slug}/{path}"
        soup = fetch_soup(url)
        if soup is None:
            continue

        publication_teasers = soup.find_all('div', class_='publication-teaser')
        if not publication_teasers:
            continue

        papers = []
        for teaser in publication_teasers:
            paper = extract_paper(teaser, faculty_name, slug)
            if paper:
                papers.append(paper)

        label = 'WP' if 'working' in path else 'Pub'
        print(f"  {label} {faculty_name}: {len(papers)} papers")
        return papers

    print(f"  - {faculty_name}: 无working papers页面")
    return []


def save_papers(papers):
    """保存论文数据到 JSON 文件"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, '..', OUTPUT_FILE)
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(papers, f, ensure_ascii=False, indent=2)
        print(f"\n数据已保存到 {output_path}")
        return True
    except Exception as e:
        print(f"\n保存文件失败: {e}")
        return False


def display_papers(papers, count=50):
    """打印最新 N 篇论文"""
    total = len(papers)
    print("\n" + "=" * 60)
    print(f"共收集 {total} 篇Working Papers")
    print(f"最新 {count} 篇如下：")
    print("=" * 60)

    for i, paper in enumerate(papers[:count], 1):
        print(f"\n{i}. {paper['title']}")
        print(f"   作者: {paper['authors']}")
        print(f"   日期: {paper['date']} | 教授: {paper['faculty']}")
        if paper['pdf_url']:
            print(f"   链接: {paper['pdf_url']}")


def main():
    print("=" * 60)
    print("MIT Economics Faculty Working Papers Crawler")
    print("=" * 60)

    # Step 1: 获取教授列表
    print("\n[1/2] 获取教授列表...")
    faculty = get_faculty_list()
    print(f"找到 {len(faculty)} 位教授\n")

    if not faculty:
        print("未找到任何教授，退出")
        return

    # Step 2: 遍历爬取论文
    print("[2/2] 爬取各教授Working Papers...")
    all_papers = []
    for i, prof in enumerate(faculty, 1):
        print(f"({i}/{len(faculty)}) {prof['name']}")
        papers = get_professor_papers(prof['slug'], prof['name'])
        all_papers.extend(papers)
        time.sleep(1)

    # 排序并展示
    all_papers.sort(key=lambda p: (p['year'], p['month']), reverse=True)
    display_papers(all_papers)
    save_papers(all_papers)
    print("\n完成！")


if __name__ == '__main__':
    print('程序开始')
    main()
