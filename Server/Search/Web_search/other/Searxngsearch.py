"""
同样是由服务器端进行引擎搜索并后处理，然后转发结果到客户端

"""
import asyncio
import aiohttp
import time
import logging
import configparser
import nest_asyncio
import os
from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers import Html2TextTransformer
nest_asyncio.apply()
file_path = os.path.dirname(os.path.abspath(__file__))  
config = configparser.ConfigParser()
config.read(os.path.join(file_path, 'config.ini'))
# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

base_url = config.get('searxng', 'url')
html2text = Html2TextTransformer()
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
    results=[result for result in results if result is not None]
    return results

def process_results(results):
    urls = [ item['url']    for result in results  for item in result['results']  ]
    print(urls)
    loader = AsyncHtmlLoader(urls)
    docs =loader.load()
    # 获取搜索结果
    try:
        # 处理文档内容
        for doc in docs:
            if doc.page_content == '':
                doc.page_content = doc.metadata.get('description', '')
        # 转换为文本格式
        docs_transformed = html2text.transform_documents(docs)
        # 构建搜索内容
        metadata = []
        result=[]
        for i, doc in enumerate(docs_transformed):
            try:
                title_content,source= results[i]["title"].split("-")
            except:
                title_content=results[i]["title"]
                source='未知'
            try:
                snippet=results[i]["snippet"]
                search_content=clear_process(doc.page_content,snippet)
            except:
                snippet=''
                search_content=clear_process(doc.page_content,snippet)
            metadata.append({
            "title": title_content,
            "url": results[i]["link"],
            "snippet": snippet,  
            "score": source
        })
            #循环拆分搜索内容，最大不超过512个字符
            for index in range(0, len(search_content), 512):
            # 收集元数据
                    result.append(
            {    #将meta数据融入搜索结果中，并添加<llmlingua, compress=False></llmlingua>标签，防止被压缩。
                'content': search_content[index:index+512]+'\n<llmlingua, compress=False>标题：{}\t链接：{}\t简介：{}\t来源：{}</llmlingua>'.format(title_content,results[i]["link"],snippet,source),
                'metadata': metadata[i]
            }
                    )
        return result
    except Exception as e:
        print(e)
        return str(e)
import re
import asyncio

def clear_process(content, snippet):
    # 文档清洗
    content = re.sub(r'<.*?>', '', content)  # 去除 HTML 标签
    content = content.strip()  # 去除多余空格
    content = re.sub(r'\s+', ' ', content)  # 去除多余空格

    # 针对特定网站进行规则过滤
    content = re.sub(r'热门推荐.*|__返回搜狐.*|END.*|下一篇.*|相关阅读.*|相关资讯.*|相关文档.*', '', content)  # 进行合并的正则替换

    if len(content) > 500:
        flag = True
    else:
        flag = False

    # 采用切片的方式处理内容并提高判断效率
    last_part = content[-500:] if flag else content
    if any(word in last_part for word in ['推荐', '更多', '其他']):
        content = content[:-500] +  Frequency_filtering(last_part)

    if len(content) < len(snippet):  # 校验长度
        content = snippet

    return content

def Frequency_filtering(content):
    segments = re.split(r'推荐|更多|其他', content)  # 使用更简洁的表达
    text, content_ = segments[0], ' '.join(segments[1:])  # 合并后部分

    # 使用正则做句子拆分
    content_ = re.split(r'[，。！？；：、“”‘’（）《》* # | |]', content_)

    # 统计短句、标点符号、数字的比例
    count_num = sum(1 for i in content_ if i.isdigit())
    count_short = sum(1 for i in content_ if len(i) < 8)

    total_count = len(content_)
    if total_count == 0:  # 防止除以零
        return content  # 或返回其他适当值

    if count_num / total_count > 0.5 or count_short / total_count > 0.5:
        return text  # 用有效文本替代
    else:
        return content  # 返回正常内容



    
if __name__ == '__main__':
     result=asyncio.run(asyncsearch('字节跳动薪资待遇', 1))
     output=process_results(result)
     print(output)
   


    