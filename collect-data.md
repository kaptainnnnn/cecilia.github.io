---
layout: page
title: "爬虫数据"
---

# 一、常见操作
## 1. Macbook运行Python代码步骤
```bash
# Step1:激活虚拟环境
source /Users/wenyuxin/浙江大学/博二秋冬学期/论文/Intelligent-Computing/.venv/bin/activate
# Step2:查看python路径
which python
>>> /Users/wenyuxin/浙江大学/博二秋冬学期/论文/Intelligent-Computing/.venv/bin/python
# Step3:运行代码
/Users/wenyuxin/浙江大学/博二秋冬学期/论文/Intelligent-Computing/.venv/bin/python 代码.py
```

# 二、专利数据爬取
## Google patent
现成的python包：python-stil，网址：https://pypi.org/project/patent-stil/#description

# 2026年5月13日 调用API爬取网站数据
今天在爬{某投资。项目。在线申报平台}的时候，解锁了调用API爬取数据的方法，并成功获取数据。
我在实践的过程中发现，相比于用drissionpage唤起浏览器，这种方法的优势是不占用浏览器内存。
该平台有个很明显的bug，就是只能查询近半个月的数据。全部的数据可以获得，但必须一页一页地翻，一旦程序断开，又要从第一页开始。而且当浏览器请求过多次，会产生大量缓存，导致电脑卡顿。
下面我将说明如何从网页获取代码中关键变量的值。首先展示模板代码(代码由deepseek生成)：
```python
import requests
import time

# 1. 配置区
url = "https://tzxm.zjzwfw.gov.cn/publicannouncement.do?method=itemList"
target_cookies = """cna=WJ+KI...(省略)...682%22%7D"""

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Referer": "https://tzxm.zjzwfw.gov.cn/tzxmweb/zwtpages/resultsPublicity/notice_of_publicity_new.html?page=1",
    "X-Requested-With": "XMLHttpRequest",
    "Cookie": target_cookies
}

# 3. 数据采集
all_items = []
total_count = 0

for page_no in range(0, 38287): 
    payload = {
        "pageFlag": "1",
        "pageNo": str(page_no),
        "area_code": "",
        "area_flag": "1",
        "deal_code": "",
        "item_name": ""
    }
    
    try:
        response = requests.post(url, data=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # 提取数据
        if data and len(data) > 0:
            item_list = data[0].get('itemList', [])
            counts = data[0].get('counts', '0')
            
            for item in item_list:
                row_data = {
                    "项目代码": item.get('deal_code', ''),
                    "项目名称": item.get('apply_project_name', ''),
                    "审批事项": item.get('ITEM_NAME', ''),
                    "办理状态": item.get('DEAL_NAME', ''),
                    "办理时间": item.get('DEAL_TIME', ''),
                    "管理部门": item.get('DEPT_NAME', ''),
                }

                all_items.append(item)
            
        else:
            print(f"第 {page_no} 页返回数据为空或格式异常")
            
    except requests.exceptions.RequestException as e:
        print(f"第 {page_no} 页请求发生错误: {e}")
    except json.JSONDecodeError as e:
        print(f"第 {page_no} 页JSON解析失败: {e}")
    except Exception as e:
        print(f"第 {page_no} 页发生未知错误: {e}")
    
    # 增加到3秒延迟，更加礼貌
    time.sleep(3)
```
## 详细步骤
步骤一：在网页空白处点击右键，选择“检查”
<img width="1204" height="837" alt="image" src="https://github.com/user-attachments/assets/927ca7f4-904e-4bc0-8d95-d7ef07ca6d68" />
步骤二：在右侧出现的面板中，点击“网络”。先点击清空符号，选择筛选“Fetch/XHR”，再点击网站页面的“下一页”，会出现新的请求。
<img width="900" height="374" alt="image" src="https://github.com/user-attachments/assets/74a9d715-3bec-4f4f-8c63-b1556b7b5a3b" />
<img width="902" height="316" alt="image" src="https://github.com/user-attachments/assets/7c2c1edb-ecc8-4e28-8d4f-10fa506449e8" />

步骤三：点击新出现的请求，点击“标头”。代码中的url对应的“请求网址”，cookie=target_cookie对应的Cookie，User-Agent、Content-Type、Referer、X-Requested-With直接复制粘贴

<img width="1076" height="835" alt="image" src="https://github.com/user-attachments/assets/f610ff20-16a2-4cff-a6a6-81ed86157f29" />
<img width="1090" height="362" alt="image" src="https://github.com/user-attachments/assets/06b56149-2625-4933-9a13-352cad2bd74c" />
步骤四：点击“载荷”（payload，将对应的参数输入进payload。
<img width="1080" height="1039" alt="image" src="https://github.com/user-attachments/assets/a43b5134-ce69-49b6-b59a-ef44e593afa2" />

# 2026年5月16日 
## 政府数据开放API接口
免网站爬虫，效率太低，直接调用政府数据开放API接口

## 爬取文献数据
### OpenALex
OpenALex API网址：[https://developers.openalex.org](https://developers.openalex.org/guides/recipes#explore-citation-links)
例：这是调用OpenALex API的网址https://api.openalex.org/works?filter=primary_location.source.issn:0002-8282，0002-8282是American Economic Review的代码。
ps：使用JSONVue（谷歌浏览器插件），json数据易读
```Python
# 批量获取期刊文献的信息
https://api.openalex.org/works?filter=primary_location.source.issn:{issn} # issn为期刊的issn号
```

### Crossref REST API
网址：[https://api.crossref.org/swagger-ui/index.html?utm_source=chatgpt.com#/](https://api.crossref.org/swagger-ui/index.html?utm_source=chatgpt.com#/Works/get_works__doi__agency)
例：利用crossref调用doi为10.3982/ecta16484的文献的网址，https://api.crossref.org/works/10.3982/ecta16484
