""" 
Qanything 项目的 DuckDuckGo 搜索模块

使用 DuckDuckGo 搜索 API 进行搜索，并使用加载器和文档转换器进行文档处理。

需要连接外网vpn

搜索速度不与搜索数据量线性增长，适合大规模数据搜索。


langchain支持html网页，如果涉及文件下载url，可能会报错。
"""
import asyncio
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers import Html2TextTransformer
from pydantic import BaseModel, Field
import re


html2text = Html2TextTransformer()

class WebSearchInput(BaseModel):
    query: str = Field(..., description="Search query")

async def duckduckgo_search(query: str, top_k: int):
    # 获取搜索结果
    try:
        # 配置 DuckDuckGo 的 API 包装器
        api_wrapper = DuckDuckGoSearchAPIWrapper(max_results=top_k, backend="lite")
        results = await asyncio.to_thread(api_wrapper.results, query, max_results=top_k)
        # 提取链接
        urls = [res["link"] for res in results]
        # 使用异步加载器加载 HTML 内容
        loader = AsyncHtmlLoader(urls)
        docs = loader.load()
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
                search_content= await clear_process(doc.page_content,snippet)
            except:
                snippet=''
                search_content= await clear_process(doc.page_content,snippet)
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

async def clear_process(content, snippet):
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
        content = content[:-500] + await Frequency_filtering(last_part)

    if len(content) < len(snippet):  # 校验长度
        content = snippet

    return content

async def Frequency_filtering(content):
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



        

if __name__ == "__main__":
    import time
    import logging
    logging.basicConfig(level=logging.INFO)
    query = "字节跳动薪资待遇"
    top_k = 20  # 设置返回结果的数量
    start_time = time.time()
    result = asyncio.run(duckduckgo_search(query, top_k))
    end_time = time.time()
    print(result)
    logging.info(f"Search query: {query}, top_k: {top_k}, time: {end_time - start_time:.2f}s")
    #50条结果大概需要2.67s左右,比我的seaxng服务器要快，可能是网络速度较快。
    #100条结果只需要2.71左右,大规模数据搜索极具优势。
    #数据包括了大量博客，但是比较脏，需要进一步清洗。
    """ 
    改进：
    1、改写输出格式，增加元数据。
    2、异步调用API，提高搜索速度。
    3、采用规则的方法进行文档清洗
    """
   
