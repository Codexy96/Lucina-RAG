""" 
API能力包括:

duckgo+searxng 网页搜索

milvus+ES混合搜索

单问题首token响应时长（在模拟通信环境中测试，服务器地址：内蒙，客户端地址：北京）：10秒-13秒

平均回复时长：30s-60s

"""
import sys 
sys.path.append('/root/4.0/')
import re
import threading
from fastapi import FastAPI, Query, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import threading
from ..Engine.LLM.prompt import get_add_prompt,get_intent_prompt,get_system_prompt
from ..Engine.LLM.LLM import zhipuAI,deepseekAI
app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware
modules_loaded_event = threading.Event()

#------异步加载search模块------#
def load_modules():
    global search
    from ..Server.Search import search_with_web as search
    modules_loaded_event.set()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 或者指定你允许的来源
    allow_credentials=True,
    allow_methods=["*"],  # 或者指定允许的方法，如 ["GET", "POST"]
    allow_headers=["*"],  # 或者指定允许的头部
)
#------------初始化大模型API------------#
zhipullm=zhipuAI()
deepseekllm=deepseekAI()



class Query(BaseModel):
    q: str





@app.get("/ask")
async def ask_query(query: str):
    # 意图识别
    result = zhipullm.response(
        messages=[
            {'role': 'system', 'content': get_intent_prompt()},
            {'role': 'user', 'content': query}
        ],
        stream=True,
    )
    content = ""
    initial_chunks = []  # 用于保存初始的chunk
    flag=True
    for chunk in result:
        initial_chunks.append(chunk)
        content += chunk
        if len(content)<4:
            if "不" in content:    
                flag=False
        elif len(content)>4 and flag==True:
            break
    if flag:
        return StreamingResponse(result, media_type='text/html')
    else:
        querys=re.findall(r'```query(.*?)```',content,re.S)
        if len(querys)==0:
            querys=[query]
        #print(querys)
        if len(querys)>=2:
            querys_searxng=querys[2:]
            querys_duckgo=querys[:2]

    try:
        total_result=await search(query,querys,querys_searxng,querys_duckgo)
        #print(web_search_result_searxng,"web_search_result_searxng")
        #print(web_search_result_duckgo,"web_search_result_duckgo")
        messages = [
            {'role': 'system', 'content':get_system_prompt()},
            {'role': 'user', 'content': """***the data you can use:{data}.
             {add_prompt} 
             ***the query you need to answer***\n{query}\n***remmber***3、When numbers appear in the description, it is possible to trigger a description of a chart and generate code. The more data there is, the higher the probability of triggering. You need to determine when to use charts instead of text explanations for more persuasive presentation.the format with code is  before your <iframe> reference.such as ```python  #your chart generate code in it  #if  the data contains time data such as year and month, they need to be converted into str format first, for example, years=[str(year) for year in years] and then you can generate the chart with code ``` <iframe src="http://localhost:6300/charts/your_chart_name.html" style="width: 100%; height: 100%; border: none; border-radius: 10px;"></iframe>\n
             Try to minimize the repetition of viewpoints in discussions and generate content by combining more reference information.
             ***your response as assistant with***:<!DOCTYPE html> <html lang="cn"> <head> <meta charset="UTF-8">.....
             please return html format response.""".format(query=query, data=total_result[:55000], add_prompt=get_add_prompt)},
        ] 
        return StreamingResponse(deepseekllm.response_code(messages, stream=True), media_type='text/html')

    except Exception as e:
        print(e)





if __name__ == "__main__":
    threading.Thread(target=load_modules).start()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6200)

