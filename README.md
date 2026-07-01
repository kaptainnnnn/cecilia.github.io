
My name is Yuxin Wen. I'm currently a PhD candidate in economics from Zhejiang University.

### 项目结构

| 文件 | 说明 |
|---|---|
| `_data/adb_papers.json` | ADB 工作论文数据（每日自动更新） |
| `_data/ox_papers.json` | Oxford 工作论文数据（每日自动更新） |
| `adb_working_papers.md` | ADB 论文展示页面 `/adb-working-papers/` |
| `ox_working_papers.md` | Oxford 论文展示页面 `/oxford-working-papers/` |
| `scripts/adb_crawler.py` | ADB 爬虫（DrissionPage，需 headed 模式绕过 Cloudflare） |
| `scripts/ox_crawler.py` | Oxford 爬虫（DrissionPage，纯文本解析） |
| `.github/workflows/update_papers.yml` | 每日自动运行两个爬虫并提交数据 |

### 本地运行爬虫

```bash
pip install DrissionPage

# ADB 爬虫（Cloudflare 需要 headed 浏览器）
python scripts/adb_crawler.py --pages 2

# Oxford 爬虫
python scripts/ox_crawler.py --pages 2    # 抓取2页（约50篇）
python scripts/ox_crawler.py --pages all  # 抓取全部（约84页）
```
