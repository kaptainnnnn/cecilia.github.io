
My name is Yuxin Wen. I'm currently a PhD candidate in economics from Zhejiang University.

### 项目结构

| 文件 | 说明 |
|---|---|
| `_data/adb_papers.json` | ADB 工作论文数据（每日自动更新） |
| `_data/ox_papers.json` | Oxford 工作论文数据（每日自动更新） |
| `_data/oecd_papers.json` | OECD 工作论文数据（每日自动更新） |
| `_data/nber_papers.json` | NBER 工作论文数据（每日自动更新） |
| `adb_working_papers.md` | ADB 论文展示页面 `/adb-working-papers/` |
| `ox_working_papers.md` | Oxford 论文展示页面 `/oxford-working-papers/` |
| `oecd_working_papers.md` | OECD 论文展示页面 `/oecd-working-papers/` |
| `nber_working_papers.md` | NBER 论文展示页面 `/nber-working-papers/` |
| `scripts/adb_crawler.py` | ADB 爬虫（DrissionPage，需 headed 模式绕过 Cloudflare） |
| `scripts/ox_crawler.py` | Oxford 爬虫（DrissionPage，纯文本解析） |
| `scripts/oecd_crawler.py` | OECD 爬虫（HTTP API，无需浏览器） |
| `scripts/nber_crawler.py` | NBER 爬虫（DrissionPage，页面速度快） |
| `.github/workflows/update_papers.yml` | 每日自动运行所有爬虫并提交数据 |

### 本地运行爬虫

```bash
pip install DrissionPage requests

# ADB 爬虫（Cloudflare 需要 headed 浏览器）
python scripts/adb_crawler.py --pages 2

# Oxford 爬虫
python scripts/ox_crawler.py --pages 2    # 抓取2页（约50篇）
python scripts/ox_crawler.py --pages all  # 抓取全部（约84页）

# OECD 爬虫（API 直连，不需要浏览器）
python scripts/oecd_crawler.py            # 抓取全部（约1845篇）
python scripts/oecd_crawler.py --pages 5  # 抓取前5页

# NBER 爬虫
python scripts/nber_crawler.py --pages 2   # 抓取2页（100篇）
python scripts/nber_crawler.py --all       # 抓取全部（35873篇）
```
