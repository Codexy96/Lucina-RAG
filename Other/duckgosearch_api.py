import asyncio
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers import Html2TextTransformer
""" 
先搜索，然后使用htmlload去加载url中的内容，最后再进行清洗和分段，统一数据格式

"""
app = FastAPI()

html2text = Html2TextTransformer()

class WebSearchInput(BaseModel):
    query: str = Field(..., description="Search query")
    top_k: int = Field(..., description="Number of top results to return")

async def asyncsearch(query: str, top_k: int):
    try:
        api_wrapper = DuckDuckGoSearchAPIWrapper(max_results=top_k, backend="lite")
        results = await asyncio.to_thread(api_wrapper.results, query, max_results=top_k)
        urls = [res["link"] for res in results]
        loader =  AsyncHtmlLoader(urls)
        docs =loader.load()
        
        for doc in docs:
            if doc.page_content == '':
                doc.page_content = doc.metadata.get('description', '')
        
        docs_transformed = html2text.transform_documents(docs)
        metadata = []
        result = []
        
        for i, doc in enumerate(docs_transformed):
            title_content, source = results[i]["title"].split("-", 1) if "-" in results[i]["title"] else (results[i]["title"], '未知')
            snippet = results[i].get("snippet", "")
            search_content = await clear_process(doc.page_content, snippet)

            metadata.append({
                "title": title_content,
                "url": results[i]["link"],
                "snippet": snippet,  
                "score": source
            })

            # 循环拆分搜索内容，最大不超过512个字符
            for index in range(0, len(search_content), 512):
                result.append({
                    'content': search_content[index:index + 512] + f'\n<llmlingua, compress=False>标题：{title_content}\t链接：{results[i]["link"]}\t简介：{snippet}\t来源：{source}</llmlingua>',
                    'metadata': metadata[i]
                })
        return result
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

async def clear_process(content, snippet):
    content = re.sub(r'<.*?>', '', content)
    content = content.strip()
    content = re.sub(r'\s+', ' ', content)

    content = re.sub(r'热门推荐.*|__返回搜狐.*|END.*|下一篇.*|相关阅读.*|相关资讯.*|相关文档.*', '', content)

    flag = len(content) > 500
    last_part = content[-500:] if flag else content
    
    if any(word in last_part for word in ['推荐', '更多', '其他']):
        content = content[:-500] + await Frequency_filtering(last_part)

    if len(content) < len(snippet):
        content = snippet

    return content

async def Frequency_filtering(content):
    segments = re.split(r'推荐|更多|其他', content)
    text = segments[0]
    content_ = ' '.join(segments[1:])
    
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

@app.post("/search")
async def search(input: WebSearchInput):
    results = await asyncsearch(input.query, input.top_k)
    return {"results": results}

# 启动服务器的命令: uvicorn your_filename:app --reload

""" 
curl -X POST http://localhost:8000/search -H "Content-Type: application/json" -d '{"query": "字节跳动薪资待遇", "top_k": 5}'

"""
