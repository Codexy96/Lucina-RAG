import asyncio
import aiohttp
import logging
import configparser
import nest_asyncio
import os
from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers import Html2TextTransformer
import re
import bs4


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



import asyncio
import aiohttp
def classification_urls(urls):
    files_urls = []
    web_urls = []
    # 定义常见文件扩展名的正则表达式
    file_extensions = re.compile(r'\.(pdf|docx|zip|jpg|jpeg|png|xlsx|pptx|rar|txt|mp3|mp4|avi)$', re.IGNORECASE)
    web_extensions=re.compile(r'\.(com|cn|org|net|edu|gov)', re.IGNORECASE)
    for url in urls:
        if file_extensions.search(url):  # 检查URL是否包含文件扩展名
            files_urls.append(url)
        elif web_extensions.search(url):
            web_urls.append(url)
        else:
            #不符合设定的扩展名，直接丢弃
            pass
    
    return files_urls, web_urls

async def check_url(url, timeout=0.5):
    async with aiohttp.ClientSession() as session:
        try:
            # 正确地使用 wait_for 来等待 session.head(url)
            response = await asyncio.wait_for(session.head(url), timeout)
            # 只有当返回的状态码是 200 时，说明链接是有效的
            return url if response.status == 200 else None
        except asyncio.TimeoutError:
            print(f"Timeout checking {url}")
            return None
        except Exception as e:
            print(f"Error checking {url}: {e}")
            return None

async def process_results(results):
    urls = [item['url'] for result in results for item in result['results']]
    # 检查每个 URL 的有效性
    _, web_urls =classification_urls(urls)
    url_check_tasks = [check_url(url) for url in web_urls]
    valid_urls = await asyncio.gather(*url_check_tasks)
    valid_urls = [url for url in valid_urls if url is not None]
    loader = AsyncHtmlLoader(valid_urls[:5])
    docs = loader.load()
    try: 
        results=doc_process(docs)
        return results

    except Exception as e:
        print(e)
        return []
def  doc_process(docs):        
        for doc in docs:
            if doc.page_content == '':
                doc.page_content = doc.metadata.get('description', '')
        docs_transformed = html2text.transform_documents(docs)
        metadata = []
        result = []
        for i, doc in enumerate(docs_transformed):
            if 'title' in docs[i].metadata.keys():
                try:
                    title_content, source = docs[i].metadata["title"].split(' -')
                except:
                    title_content = docs[i].metadata["title"]
                    source = '未知'
            else:
                title_content = '未知'
                source = '未知'
            try:
                snippet = docs[i].metadata["description"]
                search_content = clear_process(doc.page_content, snippet)
            except:
                snippet = ''
                search_content = clear_process(doc.page_content, snippet)
            metadata.append({
                "title": title_content,
                "url": docs[i].metadata["source"],
            })
            #为元数据预留空间
            for index in range(0, len(search_content), 512):
                result.append(
                    {
                        'content': search_content[index:index+512],
                        'snippet': snippet,
                        'status': 'success',
                        'metadata': metadata[i]
                    }
                )
        return result
def clear_process(content, snippet):
    import re
    content = re.sub(r'<.*?>', '', content)
    content = content.strip()
    content = re.sub(r'\s+', ' ', content)
    content = re.sub(r'热门推荐.*|__返回搜狐.*|END.*|下一篇.*|相关阅读.*|相关资讯.*|相关文档.*', '', content)

    if len(content) > 500:
        flag = True
    else:
        flag = False

    last_part = content[-500:] if flag else content
    if any(word in last_part for word in ['推荐', '更多', '其他']):
        content = content[:-500] + Frequency_filtering(last_part)

    if len(content) < len(snippet):
        content = snippet

    return content

def Frequency_filtering(content):
    segments = re.split(r'推荐|更多|其他', content)
    text, content_ = segments[0], ' '.join(segments[1:])
    content_ = re.split(r'[，。！？；：、“”‘’（）《》* # | |]', content_)
    count_num = sum(1 for i in content_ if i.isdigit())
    count_short = sum(1 for i in content_ if len(i) < 8)
    total_count = len(content_)
    if total_count == 0:
        return content
    if count_num / total_count > 0.5 or count_short / total_count > 0.5:
        return text
    else:
        return content

if __name__ == '__main__':
    pass
