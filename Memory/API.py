#------------memory 模块共有三部分组成----------------------

# 1、Agent: 封装任意client,并重写了function逻辑，添加对智能体回复的summary功能

# 2、Long_Memory: 对长期记忆进行管理，基于ES进行记忆上传、加载和搜索等功能，适用于开发环境

# 3、Tool_Call  : 对工具定义进行统一管理，并提供从工具调用消息到工具结果消息的直接转换，减少工作流复杂程度，并支持多次并行调用函数

from memory import Agent,Long_Memory,Tool_Call,my_tool_call

#----------填写好config.ini文件内容后，可以直接使用我们预填充好的my_tool_call子类---------------

tools=my_tool_call()

#-------创建client-------------
import os
config_path=os.path.join(os.path.dirname(__file__),'config.ini')
import configparser
config=configparser.ConfigParser()
config.read(config_path,encoding='utf-8')
api_key=config['Model']['api_key']
model=config['Model']['model']

from volcenginesdkarkruntime  import Ark
#client=Ark(api_key="")
#model="ep-20241217224812-blnsj"
client=Ark(api_key=api_key)
model=model
client=Ark(api_key=api_key)
model=model
#选择，是否启用assistant的summary功能（能有效缩短模型的回复记录），是否启用function功能，以及function的schemas
agent=Agent(use_summary=True,use_function=True,tools_schemas=tools.tool_schemas)



#===========创建long_memory，默认chat_history作为存储的index_name=================

uri=config['ES']['uri']
long_memory=Long_Memory(uri)




#=======================一个具有user_id标识符的fast_api接口上下文===========================

from fastapi import FastAPI, Request

app = FastAPI()

session_messages={}
#接受用户 text:str的消息
#维护一个session
#维护一个dict,每个用户ID对应一个messages


#-------------------recoder_process函数用于处理标签<summary></summary> 和function信息，并更新session_messages-
def recoder_process(recoder,messages):
    assistant_message={'role':'assistant','content':'','function_calls':None,'tool_calls':None}
    if recoder:
     #generate_text用于记录assistant生成的回复，如果启用了summary，则直接记录assistant的summary即可
     if 'assistant_summary' in recoder.keys():
          assistant_message['content']="\n".join(recoder['assistant_summary'])
     else:
          assistant_message['content']=recoder['generate_text']
     #插入到messages中
     messages.append(assistant_message)
     #接下来，检查是否有tool_calls
     if 'tool_calls' in recoder.keys():
          tool_calls=recoder['tool_calls']
          #目前主流的api都支持多工具同步调用
          #插入assistant_message
          assistant_message['tool_calls']=tool_calls
          #调用工具的高级封装__function__，直接获得messages形式返回的结果
          function_result_messages=tools.__function__(assistant_message)    
          #将结果插入到messages中
          messages.extend(function_result_messages)
          return True,messages
    else:
         return False,messages


#----api--------
#一个用户ID建议最大保持10个会话的messags记录，在前端交互时进行限制
#每个会话ID应和user_id一起传入，以user_id+session_id来锁定当前chat的messags记录
#每个session_id共享同一个预加载的long_memory。
#不再活跃的session_id应及时存储到long_memory并清除，以节约内存。清除逻辑：每24小时清理24小时之前的session_id，并将其从session_messages中删除，同时将messages保存至long_memory中。
#24小时过后session_id失效，客户端应该为用户创建新的session_id，有long_memory的预加载，用户与模型的对话记录不会丢失。
#同时，long_memory在每月1号使用clean函数进行清除
#只有在user_id首次链接时，才需要使用long_memory preload函数预加载一次

from fastapi import FastAPI, Request
from datetime import datetime, timedelta
import asyncio

app = FastAPI()

session_messages = {} #用于存储每个用户的会话消息
session_last_activity = {}  # 用于记录每个用户的会话最后活动时间

#之前创建的agent、long_memory、tools将在这里直接使用

#================会话消息的保存与清理逻辑示例=======================
"""
每24小时检查一次现在内存中的消息列表，如果有超过24小时没有活动的session_id，则将其保存到long_memory中，并从session_messages中删除。

如果一个user_id下的会话数清空，则将其从session_messages中删除。

每月1号，清理long_memory中一年前的会话记录

"""


async def save_and_clean_sessions():
    task_list = []
    while True:
        await asyncio.sleep(86400)  # 每24小时检查一次
        current_time = datetime.now()
        for user_id, sessions in session_last_activity.items():
            for session_id, last_activity in sessions.items():
                if current_time - last_activity > timedelta(hours=24):
                    # 保存到long_memory
                    task_list.append(asyncio.create_task(long_memory.save(messages=session_messages[user_id][session_id], user_id=user_id)))
                    # 清除对应的session_id下的session_messages
                    del session_messages[user_id][session_id]
                    del session_last_activity[user_id][session_id]
            if len(session_last_activity[user_id]) == 0:
                del session_last_activity[user_id]
        #这里异步循环，将长期存储的任务分批次提交处理
        for i in range(0,len(task_list),100):
            await asyncio.gather(*task_list[i:i+100])
        if len(task_list)>0:
              await asyncio.gather(*task_list)
        # 每月1号清理long_memory
        if current_time.day == 1:
            long_memory.clean()
        print("Session cleanup and long_memory cleaning completed.")
#===============================================================================


#============================预加载逻辑==========================

"""
以user_id作为标识符，默认从long_memory中加载前三天的消息 

由于设定首次user_id连接需要加载preloaded消息，因此，system_message也直接并到该函数中完成



"""


async def preload_long_memory(user_id):
    #从long_memory中预加载messages
    system_prompt={'role':'system','content':'you are a helpful assistant.'}

    preloaded_messages= await long_memory.preload(user_id=user_id)

    return [system_prompt]+preloaded_messages
    


#===============================================================

import logging
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 聊天接口
@app.post('/chat/{user_id}')
async def chat(request: Request, user_id: int):
    request_message = await request.json()
    text = request_message.get("text")
    session_id = request_message.get("session_id")

    # 请求格式校验
    if not text or not session_id:
        raise HTTPException(status_code=400, detail="Invalid request format")

    # 记录会话最后活动时间
    if user_id not in session_last_activity:
        session_last_activity[user_id] = {}
    session_last_activity[user_id][session_id] = datetime.now()

    # 初始化 session_messages
    if user_id not in session_messages:
        # 用户第一次开启会话，预加载消息
        messages = await preload_long_memory(user_id)
        session_messages[user_id] = {session_id: messages}
    elif session_id not in session_messages[user_id]:
        # 用户开启了一个新会话，复用最近一次会话记录
        last_session_id = list(session_messages[user_id].keys())[-1]
        messages = session_messages[user_id][last_session_id].copy()
        session_messages[user_id][session_id] = messages
    else:
        # 已存在的会话，直接处理用户消息
        messages = session_messages[user_id][session_id]

    # 将用户消息添加到会话中
    messages.append({'role': 'user', 'content': text})

    # 调用 agent.chat 获取响应
    #这里将recoder、text处理逻辑封装成异步生成器，以支持流式响应
    async def generate_response():
        async for item in agent.chat(messages=messages, client=client, model=model, stream=True):
            if isinstance(item, str):
                yield item.encode("utf-8")  # 确保返回的是 bytes
            else:
                # 处理非字符串类型的响应（如工具调用结果）
                recoder = item
                flag,messages= recoder_process(recoder, messages)
                logger.info("Processed recoder response.")
                #如果最后一个消息role为tool，则输入到chat当中，继续生成回复
                #这里因为使用了递归，所以有可能陷入死循环的情况，有两种办法解决
                #1、在prompt中告知模型函数调用限制次数或者让它强制生成答案
                #2、直接在generate_response写死函数调用最大次数
                #这里使用第二种方法
                #flag==True表示有tool_calls，则继续生成回复
                if flag and messages[-2]['role']!='tool':
                    yield generate_response()
    # 更新会话最后活动时间
    session_last_activity[user_id][session_id] = datetime.now()

    # 返回流式响应
    return StreamingResponse(generate_response(), media_type="text/plain")

# 启动定时任务
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(save_and_clean_sessions())
    logger.info("Startup event completed. Session cleanup task started.")