import asyncio
import concurrent.futures
import re
import os
import json
import requests
from Engine.Searxng.searxngsearch import async_search_results as async_fetch_search_results_searxng
from Engine.Duckgo.Forwarduckgosearch  import async_search_results as async_fetch_search_results_duckgo
from Engine.Bocha.bochasearch import search  as fetch_search_results_bocha
from Engine.KB.KBsearch import SearchEngine
from Engine.Tensorrt.BCErerank import rerank
from Engine.Tensorrt.Lingua2compress import compress_content_list
kb=SearchEngine()


#--------------最终搜索逻辑------------

async def search_with_web(query,querys,querys_searxng,querys_duckgo,kb_name='job'):        
        web_search_result_searxng=[]
        web_search_result_duckgo=[]
        compress_content_mix=[]
        #print(compress_content_mix,"compress_content_mix")
        tasks=[
            mix_search(query,querys,kb_name=kb_name),
            web_search_searxng(query,querys_searxng,top_k=1,tok_rerank=20),
            web_search_duckgo(query,querys_duckgo,top_k_search=4,top_k_rerank=20)
        ]
        try:
            search_results=await asyncio.gather(*tasks,return_exceptions=True)
            compress_content_mix,web_search_result_searxng,web_search_result_duckgo=search_results
            if isinstance(compress_content_mix,Exception):
                print("混合搜索失败")
                print(compress_content_mix)
                compress_content_mix=[]
            if isinstance(web_search_result_searxng,Exception):
                print("searxng搜索失败")
                print(web_search_result_searxng)
                web_search_result_searxng=[]
            if isinstance(web_search_result_duckgo,Exception):
                print("duckgo搜索失败")
                print(web_search_result_duckgo)
                web_search_result_duckgo=[]
        except Exception as e:
            print("在执行任务时发生了异常。")

        compress_content_web=web_search_result_searxng+web_search_result_duckgo
        #web_search_result =fetch_search_results(query, top_k=30)
        #compress_content_web=await compress_content_list(web_search_result)
        total_result=compress_content_mix+compress_content_web
        
        return "\n".join(total_result)

async def search_with_bocha(query,querys,kb_name='job'):        
        compress_content_mix=[]
        compress_content_bocha=[]
        #print(compress_content_mix,"compress_content_mix")
        tasks=[
            mix_search(query,querys,kb_name),
            bocha_search(query,querys)

        ]
        try:
            search_results=await asyncio.gather(*tasks,return_exceptions=True)
            compress_content_mix,compress_content_bocha=search_results
            if isinstance(compress_content_mix,Exception):
                print("混合搜索失败")
                print(compress_content_mix)
                compress_content_mix=[]
            if isinstance(compress_content_bocha,Exception):
                print("bocha搜索失败")
                print(compress_content_bocha)
                compress_content_bocha=[]
        except Exception as e:
            print("在执行任务时发生了异常。")

        total_result=compress_content_mix+compress_content_bocha
        
        return "\n".join(total_result)





async def fetch_all_results(querys, top_k=5):
    tasks = [async_fetch_search_results_searxng(query, top_k) for query in querys]
    results = await asyncio.gather(*tasks)
    return results


#-----------------Searxng搜索---------------------------

async def web_search_searxng(query,querys,top_k=1,tok_rerank=20):
    results = await fetch_all_results(querys, top_k)
    search_results=[res for result in results for res in result if result is not []]
    rerank_results=await rerank(query,search_results,top_k=tok_rerank)
    compressed_results=await compress_content_list(data_reserve(rerank_results))
    return compressed_results

#-----------------Duckgo搜索---------------------------


async def web_search_duckgo(question,querys,top_k_search=5,top_k_rerank=10):
    tasks = [asyncio.ensure_future(async_fetch_search_results_duckgo(query, top_k_search)) for query in querys]
    results =await asyncio.gather(*tasks,return_exceptions=True)
    #合并结果并重排序
    search_results=[  res for result in results for res in result if result is not [] and not isinstance(result,Exception) and not isinstance(result,concurrent.futures.TimeoutError)]
    if len(search_results)<1:
        print("请求超时，duckgo搜索结果为空")
        return []
    rerank_results=await rerank(question,search_results,top_k_rerank)
    print(rerank_results,"rerank_results")
    compressed_results=await compress_content_list(data_reserve(rerank_results))
    return compressed_results




#---------------------Bocha搜索---------------------------

async def bocha_search(query,querys):
    search_results=fetch_search_results_bocha(querys)
    #重排序管道
    rerank_results=await rerank(query,search_results,30)
    #重新组织数据，保留数值
    #compress_results=await compress_content_list(data_reserve(rerank_results))
    compress_results=[res['content'] for res in rerank_results if len(res['content'])>100]
    return compress_results
#---------------------混合搜索：向量搜索与关键词搜索,更换知识库名即可实现不同知识库搜索--------------------

async def  mix_search(query,querys,kb_name):
          # 创建搜索任务
          search_tasks = [
        kb.search(name=kb_name, query=query, keyword_threshold=5, top_k=10, top_e=10) for query in querys
    ]
          search_results=await asyncio.gather(*search_tasks,return_exceptions=True)
          #对查询的搜索结果汇总去重并进行重排序
          unique_results=[]
          for result in search_results:
              if isinstance(result,Exception):
                  print("查询失败")
              elif result is not None and result is not []:
                  for res in result:
                      if  res not in unique_results:
                          unique_results.append(res)
                          
          #重排序
          rerank_results=await rerank(query,unique_results,20)
          compress_results=await compress_content_list(data_reserve(rerank_results))
          return compress_results
 
 
 
 #----------数据预处理----------

def data_reserve(result):
    for res in result:
        if len(res['content'])<100:
            continue
        structured_text,unstructured_text=data_classifier(res['content'])
        res['content']="<llmlingua,compress=False>{structured_text}</llmlingua>{unstructured_text}".format(structured_text=structured_text,unstructured_text=unstructured_text)
    return result



#----------结构化数据与非结构化数据分离----------

def data_classifier(text):
    pattern=r'(\d+(?:\.\d+)?)'
    matches=list(re.finditer(pattern,text))

    #提取数字并保留一定上下文窗口
    structured_text_list=[]
    index=0
    while index < len(matches):
        match=matches[index]
        #number=match.group()
        start_index=match.start()
        end_index=match.end()
        context_start=max(0,start_index-8)
        context_end=min(len(text),end_index+8)
        for i in range(index+1,len(matches)):
            if max(matches[i].start()-5,0)<=context_end:
                context_end=min(len(text),matches[i].end()+5)
                index=i
                
        index+=1
        structured_text_list.append(text[context_start:context_end])
    """
    for match in matches:
        number=match.group()
        start_index=match.start()
        end_index=match.end()
        context_start=max(0,start_index-10)
        context_end=min(len(text),end_index+10)
        context=text[context_start:context_end]
        structured_text.append((number,context))
    """

    #提取非数字文本，即删除数字及上下文窗口的文本之后的剩余文本
    unstructured_text=text 
    for context in structured_text_list:
         unstructured_text = unstructured_text.replace(context, '')
    unstructured_text=re.sub(r'\s+',' ',unstructured_text).strip()

    return "".join(structured_text_list),unstructured_text