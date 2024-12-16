""" 
API能力包括：

fastapi异步处理

联网搜索（2.3秒）

混合搜索（1秒以内） 

混合搜索结果去重

如果混合搜索和联网搜索先后进入重排序，应该能更快。

搜索结果重排序

搜索结果按索引顺序排序

内容压缩

llm生成带chart的流式回复

"""
import sys 
sys.path.append('/root/4.0/')
from Engine.database.KnowledgeBase_for_search import KnowledgeBase
import concurrent.futures
from Server.Search.Web_search.Forwarduckgosearch import fetch_search_results
from Engine.model.LLM.LLM import deepseekAI,zhipuAI
import re
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import threading
from typing import List
from fastapi import FastAPI, Query, Body, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import matplotlib.pyplot as plt
import numpy as np
import threading
import asyncio
plt.rcParams['font.family'] ='SimHei' #中文显示
plt.rcParams['axes.unicode_minus'] = False #负号显示
kb=KnowledgeBase()
zhipullm=zhipuAI()
deepseekllm=deepseekAI()
app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware
def load_modules():
    global compress_content_list, rerank
    from Server.Compress.Lingua2 import compress_content_list
    from Tensorrt.BCE_rerank import rerank
    
modules_loaded_event = threading.Event()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 或者指定你允许的来源
    allow_credentials=True,
    allow_methods=["*"],  # 或者指定允许的方法，如 ["GET", "POST"]
    allow_headers=["*"],  # 或者指定允许的头部
)
class Query(BaseModel):
    q: str
system_prompt="""
 You are an expert in the field of employment planning, skilled at providing answers to users' questions with charts and text based on reference information. 
 Next, you will have a reference piece of information to answer user questions based on your own knowledge and reasoning using html language.
 ***Here are some rules you need to follow when you generate your answer with html language*** 
 use headings and subheadings to organize the structure of your article, and when you are about to start the next heading and content, you should start a new line. 
 The content under each title should be as detailed as possible until the full text is over 1500 words long.

 what's more.
 In the process of answering, you not only need to output text, but also need to output charts. 
 When you use more drawing techniques, such as comparing different levels of the same concept using different colored(It is best not to have more than three colors, representing the most prominent level, the ordinary level, and the lowest level) bar charts or graphs, distinguish high and low values using different colors. 
 also,When you use more than one or two or three or four charts  and graphs  in your text generate process to present vivid and visual data to users, you will receive more and bigger rewards.
 ***your goal***
 Your goal is not only to answer user questions with better ability to interweave text and images and professional guidance skills, the ability to cite data, but also to receive higher rewards in limited answers.
 The charts are presented in the form of code, and we will automatically convert them into corresponding charts. The code format for the chart should be as follows:
 We can use charts to explain this concept more intuitively or Next, I will present an image's title chart to provide a more intuitive representation to .... or This is an image's title to help understand to how ......:(the line  use as same as user's question to describe the chart)
 ```python
import pandas as pd
import matplotlib.pyplot as plt
plt.rcParams['font.family'] ='SimHei' #如果是中文图表，需要设置字体用来正常显示中文标签
.....
data=.....
```
<img src="http://127.0.0.1:6300/image_name which use English language.png" alt="image title using language as same as user's question">
It can be seen from the chart that(you can use the language as same as user's question to describe the chart)
or 
Next, I will present an image's title chart to provide a more intuitive representation.(the line use the language as same as user's question to describe the chart)
```python
import pands as pd
df=.....

```
<img src="chart/image_name.png" alt="image title using language as same as user's question">
It can be seen from the chart that(you can use the language as same as user's question to describe the chart)
or 
This is an image's title to help understand to how ......:(the line use the language as same as user's question to describe the chart)
```python
import seaborn as sns
.....
```
<img src="chart/image_name.png" alt="image title using language as same as user's question">
It can be seen from the chart that(you can use the language as same as user's question to describe the chart)
you can generate code in your answer text generate process to prove your viewpoint, make sure every code can Run independently.
every chart code generated should be saved in same file_dir named '/root/chart', don't plt.show() or show image just save it with english language name. please write save logic in your code with image name  and file_dir called /root/chart using English language.
your code should be interspersed after your corresponding analysis or related text.
your code should be leave it as it.

***tips***
1、your goal is to use as many charts as possible to illustrate the connections between different groups of data through my suggested method, while using reasonable headings and subheadings, and each small paragraph of 150-300 to organize your context
2、you can also consider showing the chart to the user together with the text process. 
3、Again, when you need to make a comparison, you can draw a corresponding chart according to the reward rules I gave and insert it behind your text.and when there are different objects with different numerical representations.
4、make sure that the  text and graphics  in chart generated by your code have sufficient space and layout to display, and that the data selection matches the titles and fields you have set.
5、your analysis after the image depends on the trend and performance of the data
6、if there is data loss, please do not generate incorrect charts and ignore them
7、Use line charts related to time periods, data with significant increases or decreases and indicate peak and minimum values. 
8、Use bar charts or bar charts to represent the differences in numerical values between entities within the same market or attribute.
10、Proportion, proportion, or share can be represented using pie charts or sector charts to show their proportional relationships.
11、when you output numerical data, you can start considering using charts to supplement the explanation, instead of displaying it in a separate title at the end
12、use the language as same as user's question to organize your language and chart content.
**output format**
The format of your text output should be an HTML webpage begin with <!DOCTYPE html>. Please use tags flexibly to layout your text For example, summarizing the content of a topic into a main heading and dividing it into several subheadings, with each subheading being between 100 or 300 words in length.
but your code should be leave it as it , with the format of the example I gave you from the code format.
***this is the reference information you can use for answering user questions, and answer with the language as same as user's question***
{text}
"""


@app.get("/ask")
async def ask_query(query: str):
    # 意图识别
    result = zhipullm.response(
        messages=[
            {'role': 'system', 'content': """
        你现在有一个知识完备的外接知识库
       判断用户输入的问题能否使用你现有的知识进行回答。如果可以，请直接返回"可以"。
       你可以回答的问题有：
             1、闲聊
             2、简单名词的定义描述
        你尽量不要去回答的有：
             1、职业规划的咨询
             2、真实案例的剖析
             3、现实场景中的考公、考研、考证、工作等问题
             4、有关公司、国家、组织的相关问题
       如果不能，请直接返回"抱歉，我无法生成，需要外部知识库协助"
    请不要向用户透露你判断的过程。
      """},
            {'role': 'user', 'content': query}
        ],
        stream=True,
    )
    content = ""
    for chunk in result:
        content += chunk
    if '可以' in content:
        response = zhipullm.response(
            messages=[
                {'role': 'system', 'content': """你是lucina, 擅长16岁到30岁的人们的职业规划，提供行业情形一手资讯和就业、考公、考研建议，和定制化职业规划、个人发展指导服务。
             """},
                {'role': 'user', 'content': query}],
            stream=True,
        )

        return StreamingResponse(response, media_type='text/plain')
    try:
        # 执行混合搜索任务
        mix_search_result = await kb.search(name='job', query=query, keyword_threshold=5, top_k=20, top_e=20)
        rerank_result = await rerank(query, mix_search_result, top_k=20)
        compress_content_mix= await compress_content_list(rerank_result)
         # 使用线程池执行联网搜索，并设置超时
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(fetch_search_results, query=query+"数据公开", top_k=20)
            try:
                web_search_result = future.result(timeout=15)
            except concurrent.futures.TimeoutError:
                print("联网搜索超时，已退出")
                web_search_result = []
        #web_search_result =fetch_search_results(query, top_k=30)
        compress_content_web=await compress_content_list(web_search_result)
        total_result=compress_content_mix+compress_content_web
        messages = [
            {'role': 'system', 'content': system_prompt.format(text="\n".join(total_result))[:65536]},
            {'role': 'user', 'content': query}
        ]
        return StreamingResponse(deepseekllm.response_code(messages, stream=True), media_type='text/html')
    except Exception as e:
        print(e)






if __name__ == "__main__":
    threading.Thread(target=load_modules).start()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6200)

        


        


