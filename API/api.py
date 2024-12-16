import sys
import threading
sys.path.append('e:\RAG框架\FIRST')
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import asyncio
import json
import pandas as pd
from Search.Ducksearch import duckduckgo_search as asyncduckduckgo_search
from Search.ElasticSearch import search as elasticSearch
from Search.MilvusSearch import search as milvusSearch
from LLM.LLM import zhipuAI,doubaoAI
from pydantic import BaseModel
import time
def load_modules():
    global compress_content, rerank
    from Instantcompression.Lingua2 import  compress_content_list as compress_content
    from Rerank.Rerank import rerank
modules_loaded_event = threading.Event()
app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 或者指定你允许的来源
    allow_credentials=True,
    allow_methods=["*"],  # 或者指定允许的方法，如 ["GET", "POST"]
    allow_headers=["*"],  # 或者指定允许的头部
)
class Query(BaseModel):
    q: str

""" 
基于线程的并行检索

"""


@app.post("/ask")
async def ask_query(query: Query):
    #意图识别
    result=zhipuAI(
        [
            {'role':'system','content':"""
        你现在有一个知识完备的外接知识库
       判断用户输入的问题能否使用你现有的知识进行回答。如果可以，请直接返回"可以"。
       你可以回答的问题有：
             1、闲聊
             2、简单法律概念的咨询
             3、法律考题的答疑
        你尽量不要去回答的有：
             1、复杂法律问题的咨询
             2、真实案例的剖析
             3、需要明确法律条文进行论述的推理
             4、用户透露了个人信息寻求法律咨询的行为 
       如果不能，请直接返回"抱歉，我无法生成，需要外部知识库协助"
    请不要向用户透露你判断的过程。
      """},
            {'role': 'user', 'content': query.q}
        ]
    )
    content=""
    for chunk in result:
        content+=chunk.decode('utf-8')
    if '可以' in content:
        return zhipuAI(
            [
            {'role': 'system', 'content':"""你是法亦有道，为了合理用法、以法制恶而生。你的开发者是wave。你可以为用户做的事：
             1、提供法律咨询服务
             2、为用户撰写法律文书
             3、为用户分析法律案例
             其他等等
             """},
             {'role': 'user', 'content': query.q}]
        )
        
    try:
        # 并行执行搜索任务
        #duck_search_result = await asyncduckduckgo_search(query.q, top_k=20)
        elastic_search_result = await elasticSearch('patent_law',query.q, top_k=20, threshold=0.5)
        milvus_search_result = milvusSearch(query.q, doc_limit=10, slice_limit=100, threshold=0.5, final_return=20)[0]
        # 进行结果合并和处理
        #print(elastic_search_result[0])
        #print(milvus_search_result[0])
        if isinstance(milvus_search_result, list):
            compare_hash_ids = [i['hash'] for i in milvus_search_result]
            if isinstance(elastic_search_result, list):
                for i in elastic_search_result:
                    if i['hash'] not in compare_hash_ids:
                        milvus_search_result.append(i)
              
        #if isinstance(duck_search_result, list):   
            #milvus_search_result.extend(duck_search_result)
        if len(milvus_search_result)>0:
            reranked_result = rerank(query.q, milvus_search_result, top_k=3)
            compressed_content = await compress_content(reranked_result)
        else:
            compressed_content=""
        print(compressed_content)
        message = [
            {'role': 'system', 'content': """首先理解用户问题的意图，然后按照提供的上下文信息详略得当、且能抓住关键信息回答用户问题，如果无法依据上下文信息对用户问题回答，请回复抱歉语句。请不要透露你是从参考信息中得到的内容。这是你可以参考的上下文：
             {}""".format(compressed_content)},
            {'role': 'user', 'content': query.q}
        ]
        response=zhipuAI(message)
        return StreamingResponse(response, media_type='application/json')
        

    except Exception as e:
        print(e)


if __name__ == "__main__":
    threading.Thread(target=load_modules).start()
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=7000)



