#------------------图文api演示---------------------


#api应实现的逻辑如下：

#1、客户端发送query请求，立即搜索图片作为候选列，支持分片搜索和全部搜索
#2、模型输入知识库，返回流式输出，维护一个缓存处理器，存储生成文本，并延迟发送消息
#3、对流式输出token进行段落标志检测，段落标志检测规则由prompt和模型输出格式决定
#4、如果检测到段落结束，则进行图片匹配，如果匹配成功则插入图片引用语句，例如<img src='xxx' alt='xxx'/>
#5、如果没有找到图片，则直接输出文本片段
#6、成功匹配的图片应该从图片候选列中删除
#7、每一次query前重置处理器存储的文本
#8、存储的文本仅保留最新的一个段落
#图片候选地址默认为图片绝对地址，例如:os.path.join(root_path,image_path)，图片下载接口应使引用语句可用
#图片配置好公网访问链接

#------------------图文api实现示例----------------

"""
test_api用于测试图文展示的功能
组成模块如下：

open_api: 用于向客户端提供图片下载链接

image_search: 用于图片的二阶段搜索，第一阶段根据用户的问题获取图片候选列，第二阶段根据模型的输出插入图片

fastapi与LLM用于输出内容
"""
from RAG.Engine.LLM.LLM import zhipuAI,deepseekAI
from fastapi import FastAPI, Query, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import threading
app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware
from RAG.Engine.LLM.image_prompt import load_prompt
from script.ImageRAG.Engine.image_search import ImageSearch
import asyncio
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 或者指定你允许的来源
    allow_credentials=True,
    allow_methods=["*"],  # 或者指定允许的方法，如 ["GET", "POST"]
    allow_headers=["*"],  # 或者指定允许的头部
)

#-----参数，图片根目录或云端存储链接前缀---------

#root_path=r"/root/autodl-tmp/images"
root_path="http://localhost/images"

#------------初始化大模型API------------#
zhipullm=zhipuAI()
deepseekllm=deepseekAI()
class Query(BaseModel):
    q: str

""" 
这里实现的逻辑是：

1、客户端发送一个query请求，立即向端口发送

2、返回流式输出，尽可能在短时间内对生成的文本进行堆积，重新组织速度输出给客户端

3、此时服务端接收到的文本和输出到客户端的文本有时间差，大约控制在一秒，用来图片检索和插入图片

4、为图片插入成功，可能需要阻塞。



"""



""" 
延迟响应。维护一个缓冲队列，当达到的输入的时候输出，形成时间差

"""
async def delayed_response(generator,time_step=1,image_tracker=None):
     """
     generator: 大模型流式生成器
     time_step: 时间间隔，默认一秒，视图片处理速度而定 
     
     """
     import time
     buffer=[]
     start_time=time.time()
     time_step=time_step
     for item in generator:
          #创建缓冲区，在存入之前判定是否要插入图片
          #限定模型只能使用<p></p>来生成段落
          #一个是从前端提取，另一个是从末尾添加，理论上可以异步进行
          buffer=await image_tracker.add(buffer,item)
          #buffer.append(item)
          if time.time()-start_time>time_step:
               #输出缓冲区
               for _ in buffer:
                    yield buffer.pop(0)
               
               #time_diff=time.time()-start_time
               #start_time=time.time()
               #print(f"time_diff:{time_diff}")
"""
无时差记录器，用于跟踪文本输出，并检测当前文本片段是否要插入图片
add:添加文本片段

"""
class Image_tracker:
     def __init__(self,root_path=root_path,partition_name=None):
        """
        指定root_path，图片存储的根目录
        指定partition_name,如果不指定，则默认与dataset同名的分片中搜索图片
        如果要搜索全部分片，请指定partition_name='all'
        image_tracker应该在向大模型发送请求之前创建 
        """
        self.content=""
        self.image_search=ImageSearch(root_path=root_path)
        self.partition_name=partition_name
     async def add(self,buffer,item):
          """
          判断逻辑：如果当前文本片段包含</p>标签，则说明当前段落结束，可以进行图片检索，其他格式同理。如果包含进入检测逻辑，否则直接添加到缓冲区返回
          流式输出GLM没有把</p>作为一个token，视LLM的token输出对判断语句进行调整
          """
          if '>' in item:
               #如果包含</p>标签，说明当前段落结束，可以进行图片检索
               content=self.content+item
               if '</p>' in content:
                    #如果包含</p>标签，说明当前段落结束，可以进行图片检索
                    #流式输出可能有多个token，也有可能不连续，或者只有一个
                    add_text,reserve_text=item.split('>')
                    add_text=add_text+'>'
                    self.content+=add_text
                    buffer.append(add_text)
                    return await self.check_insert(buffer,reserve_text)
               else:
                    self.content+=item
                    buffer.append(item)
                    return buffer
          else:
               self.content+=item
               buffer.append(item)
               return buffer
     async def update_images(self,query):
          """
          输入query,更新图片候选地址
          """
          await self.image_search.search(text=query,partition_name=self.partition_name,top_k=10,output_fields=["vector","path"])
     async def check_insert(self,buffer,reserve_text):
          """
          只允许模型使用<p>标签来生成段落，因此只需要匹配<p>标签提取文本。
          """
          import re
          #提取<p></p>之间的内容
          re_result=re.findall(r'<p>.*?</p>',self.content)
          print(f"当前段落提取:{re_result}")
          #获取最新的一个段落
          if re_result:
               sub_content=re_result.pop()
               #这里将段落清空，始终保持content记录的是最新的段落
               self.content=self.content.replace(sub_content,'')
          else:
               print("no match p tag")
               buffer.append(reserve_text)
               return buffer
          if sub_content:
              #检查是否要插入图片,删除标签干扰项
              result= await self.image_search.match(sub_content.replace('<p>','').replace('</p>',''),top_k=1,threshold=0.3)
              if result==[]:
                   #没有找到图片,返回原来的值
                   buffer.append(reserve_text)
                   return buffer
              else:
                   #插入图片引用语句
                   for path in result:
                         #插入图片引用语句
                         buffer.append(f"<img src='{path}' alt='{path}'/>")
                         #删除图片候选地址的逻辑在image_search中实现
                   #返回更新后的缓冲区
                   buffer.append(reserve_text)
                   return buffer
          else:
               #没有找到子内容的结束，返回原来的值
               buffer.append(reserve_text)
               return buffer
     def reset(self):
               self.content=""
               self.image_search.reset()
               print("reset image_tracker successfully")
               return self
image_tracker=Image_tracker(root_path=root_path,partition_name="images")          
@app.get("/ask")
async def ask_query(query: str):
     image_tracker.reset()
     await image_tracker.update_images(query)
     result = zhipullm.response(
        messages=[
            *load_prompt(reference_prompt=reference),  #这里添加从知识库中搜索的上下文信息，这里以新能源汽车的部分资料作为示例
            {'role': 'user', 'content': query+'answer:\n<!DOCTYPE html>\n'} #trigger:answer:\n<!DOCTYPE html>\n
        ], 
        stream=True,
    )
     return StreamingResponse(delayed_response(result,image_tracker=image_tracker,time_step=0.2),  media_type='text/html')

if __name__ == "__main__":
    with open("./LLM.txt", "r", encoding="utf-8") as f:
        reference = f.read()
    # 启动服务
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6200)

#测试
#http://127.0.0.1:6200/ask?query=How is the employment environment in China's new energy vehicle market?

#curl
#curl -N -H "Accept: text/event-stream" "http://127.0.0.1:6200/ask?query=How%20is%20the%20employment%20environment%20in%20China's%20new%20energy%20vehicle%20market%3F"

#-N : 禁用数据缓冲，使得数据在接收到时立即输出。这对于处理流媒体数据特别有用。
#-H 指定客户端希望接受的数据格式为text/event-stream,这是服务器发送事件(SSE)的标准MIME类型


