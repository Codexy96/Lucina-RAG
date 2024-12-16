"""
在云服务器上部署searxng docker容器，并在该脚本中设置后处理逻辑

searxng:开源搜索引擎，支持私有化部署且国内可用
主要搜索来源：bing
"""
#langchain实现
"""
from langchain_community.utilities import SearxSearchWrapper
search = SearxSearchWrapper(searx_host="http://124.220.221.33:8080", k=10)
if __name__ == '__main__':
    query = "python"
    results = search.run(query, source="bing")
    print(results)

"""
#request实现
"""
#request实现
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import time

def create_session():
    session = requests.Session()
    retry = Retry(
        total=5,  # 最大重试次数
        backoff_factor=1,  # 等待时间指数增加
        status_forcelist=[500, 502, 503, 504]  # 针对这些状态码重试
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def search_searxng(query):
    start_time= time.time()
    searxng_url = 'http://124.220.221.33:8080/search'
    params = {'q': query, 'format': 'json'}
    
    session = create_session()
    response = session.get(searxng_url, params=params)
    end_time = time.time()
    print("request 搜索耗时：", end_time - start_time)

    if response.status_code == 200:
        return response.json()
    else:
        print("请求失败，状态码：", response)
        return None
    

if __name__ == '__main__':
    query = "python"
    results = search_searxng(query)

    if results:
        for result in results.get('results', []):
            print(result['title'], result)

    query = "python"
    start_time = time.time()
    results = search.run(query, source="bing")
    end_time = time.time()
    print("langchain 搜索耗时：", end_time - start_time)
    print(results)

    自定义request的搜索速度比langchain快个0.1秒（十个返回结果），差别不大，但是我希望result返回score，用于后续的重排序。
    
"""
    
#最终实现
""" 
对langchain实现的借鉴和改进

1、增加score字段，用于后续的重排序

2、并行处理分页请求，适合大规模搜索

3、增加meta元数据，方便溯源

"""
"""
该API实现有一个问题，返回的content只是省略部分，需要根据网易的做法，获取url连接使用网页加载器获取到全部内容。

searxng充当网页搜索工具

"""
import asyncio
import aiohttp
import time
import logging
import configparser
import nest_asyncio
import os
nest_asyncio.apply()
file_path = os.path.dirname(os.path.abspath(__file__))  
config = configparser.ConfigParser()
config.read(os.path.join(file_path, 'config.ini'))
# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

base_url = config.get('searxng', 'url')

async def fetch(session, url):
    try:
        async with session.get(url) as response:
            response.raise_for_status()  # 引发 HTTPError 错误
            return await response.json()
    except aiohttp.ClientError as e:
        logging.error(f"网络请求错误: {e} - URL: {url}")
        return None
    except ValueError as e:
        logging.error(f"解码 JSON 错误: {e} - URL: {url}")
        return None

async def search_searxng(query, page):
    if not isinstance(query, str) or not isinstance(page, int) or page < 1:
        logging.error("无效的查询或页码")
        return None

    searxng_url = base_url.format(query, page)
    async with aiohttp.ClientSession() as session:
        data = await fetch(session, searxng_url)
        if data is None:
            logging.warning(f"未能获取页面 {page} 的数据")
        return data

async def asyncsearch(query, total_pages):
    tasks = []
    for page in range(1, total_pages + 1):
        tasks.append(search_searxng(query, page))
    
    results = await asyncio.gather(*tasks)
    return results

def process_results(results):
    output = []
    for result in results:
        if result and 'results' in result:
            for item in result['results']:
                score = item.get('score', 0)  # 获取 score
                content = item.get('content', '无内容')  # 假设有这个字段
                try:
                    publish_time, text = content.split('·') 
                except ValueError:
                    publish_time = '未知'
                    text = content
                try:
                    title,source =item.get('title').split(' - ')
                except ValueError:
                    source = '未知'
                    title = item.get('title')

                output.append({
                    'content': text+"\n"+"\n<llmlingua,compress=False>信息来源:{}\t发布时间：{}\t标题：{}\t连接：{}\t使用引擎：{}</llmlingua>".format(source,publish_time,title,item.get('url'),item.get('engine')),
                    'score': score,
                    'meta_data': {
                        'url': item.get('url', '无链接'),
                        'title': title,
                        'source': source,
                        'engine': item.get('engine', '未知'),
                        'publish_time': publish_time,
                    }
                })
    return output
if __name__ == '__main__':
    start_time = time.time()
    query = "字节跳动薪资待遇"
    total_pages = 5  # 设置要检索的页面数量，返回总数为page*10条，

    results = asyncio.run(asyncsearch(query, total_pages))  # 异步运行用户请求
    processed_results = process_results(results)
    print(processed_results)
    end_time = time.time()
    print("总搜索耗时：",  end_time - start_time)
    #50条搜索结果耗时3.15左右，比langchain快了0.6秒左右
    #100条搜索结果6.118秒
    """ 
    使用了香港服务器之后，50条搜索结果在2.2秒左右。
    """
    
    
   


    