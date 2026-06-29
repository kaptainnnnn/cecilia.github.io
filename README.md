
My name is Yuxin Wen. I'm currently a phD candidate in economics from Zhejiang University.

### 项目结构

| 文件 | 说明 |
|---|---|
| `_data/adb_papers.json` | ADB 工作论文数据（每日自动更新） |
| `adb_working_papers.md` | ADB 论文展示页面 `https://kaptainnnnn.github.io/adb-working-papers/` |
| `scripts/adb_crawler.py` | ADB 爬虫脚本（DrissionPage 绕过 Cloudflare） |
| `.github/workflows/update_papers.yml` | 每日自动运行爬虫并提交数据 |

### 本地运行 ADB 爬虫

```bash
pip install DrissionPage
python scripts/adb_crawler.py --pages 2
```
