#--------------------------------------------------------------------

#初始配置：读取config文件中的api_key model等信息，选择合适的大模型服务商创建client对象
import os
config_path=os.path.join(os.path.dirname(__file__),'config.ini')
import configparser
config=configparser.ConfigParser()
config.read(config_path,encoding='utf-8')

#uri用于连接ES，ES作为长期记忆的存储库和搜索引擎


#bocha api支持
#api_key=""
#base_url="https://api.bochaai.com/v1/"
api_key=config['Bocha']['api_key']
base_url=config['Bocha']['base_url']

#------------------------------------------

#三个模块：

#Agent封装，覆写chat逻辑之后使用

#Long Memory，实现长期记忆的搜索、保存和清理

#Tool Call ，实现工具定义、工具调用、工具结果返回

#首先是Agent




class Agent:
     """
     __init__:初始化参数，use_summary,use_function,tools_schemas

     __call__:输入messages列表，返回流式文本和json格式的结果，包括input_text,function_calls,assistant_summary

     
     """
     def __init__(self,use_summary=True,use_function=True,tools_schemas=[]):
          """
          初始化参数：
          use_summary:是否使用长期记忆模块的summary功能,默认为True
          use_function:是否使用长期记忆模块的function功能,默认为True 
          tools_schemas:工具列表，每个元素为一个工具的json schema，用于生成function_prompt,默认为[]

          可选覆写的函数：self.chat

          使用方法：
          继承并初始化

          然后使用类__call__调用，输入messages列表
          输出：
          1、流式文本
          2、{'input_text':input_text,'function_calls':function_calls,'assistant_summary':summary_text},一同返回，输出形式为json

          该封装支持 智能体输出的摘要生成，以及函数调用function_calls内容的生成，全部以文本的形式返回

          """
          self.use_summary=use_summary
          self.use_function=use_function
          self.function_prompt=""" 
Now, the actions you can choose are:
 1. Execute any number of functions to better answer user questions 
 2. Have already called a function or are fully prepared, answer the user's question directly. 
 If you want to call a function, you need to explain it to the user in a humanized way and wait a moment, for example:It's so sorry. Wait a minute, I need to recall what we talked about before.(very important! just Think of yourself as an adult. Don't disclose that you are calling from  tools.)
 Then use <function>  </function>   to generate a function call record. 
 For example, if the user asks a question about the weather, you ask the user to provide the necessary information，such as the city and date, and then generate a function call record as follows:
 <function>{"function": {"arguments": "{\\"city\\": \\"北京\\"}", "date": "2025-02-18"}',
"name": "get_weather"},
"type": "function"}</function>.
 Generate one for each function call. 
 If you want to call information but need the user to provide information, you can politely ask the user for it. 
 However, if you can answer directly, please ignore the above process and follow the instructions in the following content.

there are functions available for you to use:
"""
          self.summary_prompt="""\nWhen answering user questions based on the above content, output the <summary> </summary> section after each answer to excerpt the key points of your current answer to ensure that the information of each entity object in the excerpt is as complete as possible. Until the end of your answer, all <extract> </extract> are generated. Answer in the same language as the user's question. If you choose a tool call instead of answering directly, please ignore the impact of <extract> </extract>."""
          #初始化function_prompt
          self.function_prompt=self.function_add_prompt(self.function_prompt,tools_schemas)
          
     
     def function_add_prompt(self,function_prompt,tools_schemas):
          function_prompt+="\n"
          for i,tool_schema in enumerate(tools_schemas):
               function_prompt+="{}. {}\n".format(i+1,tool_schema)
          return function_prompt
     def apply_llm_summary(self,messages):
          #查找最近的一次user_message,并添加prompt
          index=None
          length=len(messages)
          for i in range(length-1,-1,-1):
               if messages[i]['role']=='user':
                    index=i
                    break
          if index is not None and self.summary_prompt  not in messages[index]['content']:
                    messages[index]['content']+=self.summary_prompt
          else:
               print("error: no user message found, please make sure the last message is user's message")
               raise ValueError
          return messages
     def apply_current_time(self,messages):
          #在system中告知当前时间
          import datetime
          current_time=datetime.datetime.now()
          formatted_time=current_time.strftime('%Y-%m-%d %H:%M:%S')
          time_prompt="\ncurrent time:{current_time}".format(current_time=formatted_time)
          for i in range(len(messages)):
               if messages[i]['role']=='system':
                    messages[i]['content']+=time_prompt
                    break
     def apply_function_calls(self,messages):
          #查找最近的一次system_message,并添加prompt
          #如果没有system_message,则创建一个
          index=None
          length=len(messages)
          for i in range(length):
               if messages[i]['role']=='system':
                    index=i
                    break
          if index is not None:
               messages[index]['content']+=self.function_prompt
          else:
               messages.append({
                    'role':'system',
                    'content':self.function_prompt
               })
        
     def chat(self,messages,client=None,model=None,stream=True,**kwargs):
        """
        参数：
        text:输入文本
        model：模型型号，默认为doubaoAI的ep_point
        stream：是否流式返回，默认为True
        其他参数参考ark的API文档
        返回：
        文本字符串
        """
        #messages重写
        messages=self.rewrite_messages(messages)
        completion=client.chat.completions.create(
            model=model,
            messages=[
                 *messages
            ],
            stream=stream,
            **kwargs
        )
        if not stream:
            return completion.choices[0].message.content
        else:
             return self.yield_output(completion)
     def yield_output(self,response):
        for chunk in response:
            yield chunk.choices[0].delta.content
     
     def rewrite_messages(self,messages):
          """ 
          根据设置，补充必要的prompt添加至messages
          
          """
          if self.use_summary:
               messages=self.apply_llm_summary(messages)
          if self.use_function:
               messages=self.apply_function_calls(messages)
          messages=self.apply_current_time(messages)
          return messages
     def label_response(self,response):
          """
          接受一个流式文本返回器，根据配置提取标签。
          当前标签有：<summary> </summary> <function> </function> 
          """
          label_streaming=False #检测模型是否正在输出标签内容
          input_text="" #智能体回答
          function_list=[] #function内容记录
          summary_list=[] #summary内容记录
          for text in response:
               input_text+=text
               if '</summary>' in input_text and label_streaming:
                          #对</summary>进行拆分
                          right=input_text.split('</extract>')[1] #右边部分输出
                          yield right
                          #正则化提取内容
                          import re
                          if '<summary>' in input_text:
                              summary_text=re.findall('<extract>(.*)</extract>',input_text)[0]
                              summary_list.append(summary_text)
                          input_text=input_text.replace('</summary>','').replace('<summary>','').replace(summary_text,'')
                          label_streaming=False 
               elif  '</function>' in input_text and label_streaming:
                          #对</function>进行拆分
                          right=input_text.split('</function>')[1] #右边部分输出
                          yield right
                          #正则化提取内容
                          import re
                          if '<function>' in input_text:
                              function_text=re.findall('<function>(.*)</function>',input_text)[0]
                              function_list.append(function_text)
                          input_text=input_text.replace('</function>','').replace('<function>','').replace(function_text,'')
                          label_streaming=False 
               elif '<' in text :
                    label_streaming=True
                    if text.split('<'):
                         yield  text.split('<')[0]                           

               else :
                    yield text
          #最终输出，获得三个数据,它们的键分别为input_text,function_calls,summary_text
          """
          返回参数类型：
          input_text:str
          function_calls:list[dict]
          assistant_summary:str
     
          """
          import json
          import random
          #如果有function_calls，对最终的function_calls增加一个id标识
          for i,function_call in enumerate(function_list):
               function_list[i]=json.loads(function_call)
               number=random.randint(100000,999999)
               call_id="call_{}".format(number)
               function_list[i]['id']=call_id
          yield  {'generate_text':input_text,'tool_calls':function_list,'assistant_summary':summary_list}
     def __call__(self,messages,client=None,model=None,stream=True,**kwargs):
          '''
          输入参数:
           - messages:输入消息列表，标准格式为{'role':str,'content':str,'function_calls':list[dict],'tool_calls':list[dict]},也支持{'role':str,'content':str}格式
           - client:大模型客户端，必填
           - model:模型型号，必填
           - stream:是否流式返回，默认为True
           - 其他参数参考openai的API文档
          return:
            流式传输文本
            以及{'input_text':input_text,'tool_calls':function_calls,'assistant_summary':summary_text},格式为json，其中function_calls为函数调用列表，每个元素为{'id':str,'name':str,'arguments':dict}json格式，summary_text为智能体摘要列表,list[str]。 
          
          
          '''
          response=self.chat(messages,client=client,model=model,stream=stream,**kwargs)
          return self.label_response(response)
#------------------------------------


#初始化agent
#tools_schemas=[]
#agent=Agent(use_summary=True,use_function=True,tools_schemas=tools_schemas)

#生成流式输出

messages=[
     {'role':'user','content':'你好，请问今天天气怎么样？'}
]

#response=agent(messages=messages,client=client,model=model,stream=True)


#流式输出结果

#result_dict=None

#for text in response:
     #if isinstance(text,str):
          #填写文本输出逻辑
          #pass
     #else:
          #result_dict=text
          

#Long Memory模块

#uri=None
class Long_Memory:
     def __init__(self,uri):
          #连接数据库
          from elasticsearch import Elasticsearch
          self.es=Elasticsearch(uri=uri)
          if not self.es.ping():
               raise Exception("连接es失败")
          else:
               print("连接es成功")
          #如果没有chat_memory表，则创建,chat_memory固定的数据组织形式为：
          """
          {
              "user_id": text,
              "upload_time": date,
              "content": text,
              "role": text,
          } 
          
          
          """
          fields={ 
               "user_id": {"type": "text"},
               "upload_time": {"type": "date"},
               "content": {"type": "text"},
               "role": {"type": "text"}
          }
          settings={
               'settings':{
                    'number_of_shards':1,
                    'number_of_replicas':0
                },
               'mappings':{
                    'properties':fields
               }
          }
          if not self.es.indices.exists(index='chat_memory'):
               self.es.indices.create(index='chat_memory', body=settings)
               print("创建chat_memory表成功")
     def data_upload(self,data):
          #上传数据
          """
          上传数据统一为固定格式：
          {
              "user_id": text,
              "upload_time": date,
              "content": text,
              "role": text,
          }
          """
          actions=[]
          for item in data:
               actions.append({
                    "_index": "chat_memory",
                    "_source": item
               })
          from elasticsearch import helpers
          helpers.bulk(self.es,actions)
          print("上传数据成功")
     async def data_query(self,user_id,time_range=None,keywords=None,limit=None):
          """ 
          查询数据，支持：
          
          1、查询指定时间范围内的数据
          2、查询指定关键字的数据
          3、查询数量不超过limit的数据
          
          参数：
          - user_id: 用户id
          - time_range: 时间范围，格式为[开始时间，结束时间]，如["2021-01-01","2021-01-31"]
          - keywords: 关键字列表，如["你好","早上好"]
          - limit: 限制返回的数据条数
          
          """
          #查询数据
          import asyncio
          from elasticsearch import ConnectionError,NotFoundError
          import logging
          if not self.es.ping():
               try:
                    self.es=Elasticsearch(uri=uri)
               except ConnectionError:
                    raise ConnectionError("连接es失败，重新连接")
          search_query=None
          if time_range!="":
               #查询条件
               search_query={
               "query":{
                    "bool":{
                         "must":[
                              {
                                   "match":{
                                        "user_id":user_id
                                   }
                              },
                              {
                                   "range":{
                                        "upload_time":{
                                             "gte":time_range[0],
                                             "lte":time_range[1]
                                        }
                                   }
                              }
                         ]
                    }
               }
          }
          if keywords!=[]:
               if search_query==None:
                    search_query={
                         "query":{
                              "bool":{
                                   "must":[
                                        {
                                             "match":{
                                                  "user_id":user_id
                                             }
                                        }
                                   ]
                              }
                         }
                    }
               #添加关键字查询
               for keyword in keywords:
                    search_query['query']['bool']['must'].append(
                         {
                              "match":{
                                   "content":keyword
                              }
                         }
                    )
          if limit!=None:
               search_query['size']=limit
          try:
               max_retries=3 #最大重试次数
               for attempt in range(max_retries):
                    try:
                         response=self.es.search(index='chat_memory',body=search_query)
                         result=[]
                         for hit in response['hits']['hits']:
                              result.append(hit['_source'])
                         return result 
                    except (ConnectionError,NotFoundError) as e:
                         logging.error("查询数据失败，原因：{},重试次数：{}".format(e,attempt+1))
                         await asyncio.sleep(0.5) #等待0.5秒后重试
               return []
                 
          except Exception as e:
               logging.error("查询数据失败，原因：{}".format(e))
               return []
     async def save(self,messages,user_id=None):
         """
          messages存储为long memory方法的高级封装

          输入messages列表，自动将messages转化为可上传的数据格式，并保存到数据库
          """
         import      datetime

         if user_id==None:
              print("please provide the user'user_id.")
              raise Exception("parameter lost")
         if not isinstance(messages,list):
              print("please provide the messages as a list.")
              raise TypeError("messages must be a list")
         upload_time=datetime.datetime.now()
         #构建data
         data=[ {'user_id':user_id,'upload_time':upload_time,'content':message['content'],'role':message['role']}  for message in messages if 'content' in message and 'role' in message]
         #上传数据
         await self.data_upload(data)
     async def recall(self,user_id=None,time_range=None,keywords=None,limit=None):
          """
          回忆功能的高级封装

          输入参数：
          - user_id: 用户id
          - time_range: 时间范围，格式为[开始时间，结束时间]，如["2021-01-01","2021-01-31"]
          - keywords: 关键字列表，如["你好","早上好"]
          - limit: 限制返回的数据条数
          
          返回：
          回忆内容的文本格式
          """
          import asyncio
          if user_id==None:
               print("please provide the user'user_id.")
               raise Exception("parameter lost")
          result=await self.data_query(user_id=user_id,time_range=time_range,keywords=keywords,limit=limit)
          #组合成纯文本格式
          result_text=""
          if result==[]:
               return "没有找到相关记忆。"
          for item in result:
               role=item['role']
               content=item['content']
               result_text+="{}:{}\n".format(role,content)
          return result_text
     async def preload(self,user_id=None,time_range=None):
          """
          预加载，用于初始化一个对话后，加载部分先前的历史对话内容。
          参数：
          - user_id: 用户id
          - time_range: 时间范围，可选：['past_week','yesterday','past_month','three_days'],如果未设置，则默认加载前三天的对话内容
          """
          import datetime 
          now=datetime.datetime.now()
          if user_id==None:
               print("please provide the user'user_id.")
               raise Exception("parameter lost")
          if time_range=='past_week':
               #加载最近一周的对话内容
               time_range=[(now-datetime.timedelta(days=7)).strftime("%Y-%m-%d"),now.strftime("%Y-%m-%d")]
          elif time_range=='yesterday':
               #加载昨天的对话内容
               time_range=[(now-datetime.timedelta(days=1)).strftime("%Y-%m-%d"),now.strftime("%Y-%m-%d")]
          elif time_range=='past_month':
               #加载最近一个月的对话内容
               time_range=[(now-datetime.timedelta(days=30)).strftime("%Y-%m-%d"),now.strftime("%Y-%m-%d")]
          elif time_range=='three_days':
               #加载最近3天的对话内容
               time_range=[(now-datetime.timedelta(days=3)).strftime("%Y-%m-%d"),now.strftime("%Y-%m-%d")]
          else:
               #默认加载最近3天的对话内容
               time_range=[(now-datetime.timedelta(days=3)).strftime("%Y-%m-%d"),now.strftime("%Y-%m-%d")]
          #加载数据
          result=await self.data_query(user_id=user_id,time_range=time_range)
          #组合成messages的格式，其中role的tool消息与它之前的assistant调用消息将会被丢弃
          messages=[]
          for item in result:
               role=item['role']
               content=item['content']
               if role=='tool':
                    messages.append({'role':role,'content':content})
                    if messages[-1]['role']=='assistant':
                         messages.pop()
               else: 
                     messages.append({'role':role,'content':content})
          return messages
               
          #默认加载最近3天的对话内容，
     async def clean(self):
          #清理逻辑：
          #获取当前时间,删除12个月前的数据
          import datetime
          import logging
          now=datetime.datetime.now()
          #one_month_ago=now-datetime.timedelta(days=30)
          one_year_ago=now-datetime.timedelta(days=365)
          #构建删除查询
          delete_query={
               "query":{
                    "range":{
                         "upload_time":{
                              "lt": one_year_ago.strftime("%Y-%m-%d")
                         }
                    }
               }
          }
          try:
               response=self.es.delete_by_query(index='chat_memory',body=delete_query)
               print(f"清理数据成功,删除了{response['deleted']}条记录")
          except Exception as e:
               logging.error("删除数据失败，原因：{}".format(e))
               raise Exception("删除数据失败")


#---------------------------------------------

#首先，确保你已经安装了elasticsearch，并启动了es服务。

#uri="http://localhost:9200" #es服务地址
#long_memory=Long_Memory(uri=uri) #创建long_memory对象

#接下来，你可以使用long_memory对象进行数据存储、查询等操作。

#数据存储

#假设你有以下messages列表：
messages=[
    {'role':'user','content':'今天天气如何？'},
    {'content': '\n当前提供了 1 个工具，分别是["get_weather"]，需要查询北京市 2025 年 2 月 18 日的天气情况，调用 get_weather。',
 'role': 'assistant',
 'function_call': None,
 'tool_calls': [{'id': 'call_hkzmx1nmzesl06j7fvpso3jq',
   'function': {'arguments': '{"city": "北京", "date": "2025-02-18"}',
    'name': 'get_weather'},
   'type': 'function'}]},
    {'role':'tool','content':'今天天气多雨转阴，气温13度，湿度89%，白天多云，晚间有大风。',"tool_call_id":"call_hkzmx1nmzesl06j7fvpso3jq","name":"get_weather"}
]
################将短期对话转化为长期记忆#####################

#每一次短期会话结束后，使用long_memory.save()方法将messages存储到long_memory中，long_meomry不和任何user_id绑定，因此可以长期存在

#假设当前上下文下：

user_id=123456

import asyncio

#保存
#asyncio.run(long_memory.save(messages,user_id=user_id))



################从长期记忆中预加载#########################


#假设下一次用户登录，需要加载之前的对话内容，可以使用long_memory.recall()方法，对话内容以文本的形式返回
#具体来说为以下组织形式：user:content \n assistant:content \n user:content \n tool:content

import asyncio

#预加载有四个尺度的加载方式：
#1、加载最近一周的对话内容
#2、加载昨天的对话内容
#3、加载最近一个月的对话内容
#4、加载最近3天的对话内容
#long_memory_messages=asyncio.run(long_memory.preload(user_id=user_id,time_range='past_week'))

#将历史对话记录插入到messages中，考虑到历史的工具调用消息对现在的对话没有帮助，因此将会丢弃tool调用和返回结果的部分。

#初始化一个新对话的messages，历史对话的插入位置应该在system_message之后

new_messages=[
     
     {'role':'system','content':'you are a helpful assistant, called Lucina.'}
]

#new_messages.append(long_memory_messages)



#同时，long_memory.recall()方法将作为可调用工具向大模型提供，大模型将根据对话内容要加载对应的长期记忆。

#这个函数的使用将在Tool_Call的使用中介绍







#-----------------------------Tool_Call模块------------------------------


#基础类Tool_Call

#实现：
#1、获取该类自定义的所有方法,自动生成json schema
#传入function_calls列表，运行对应的函数，并按顺序返回结果
#工具的结果均以文本返回，最终组合成一个list返回

class Tool_Call:
     def __init__(self):
          """
          函数的返回建议都设置为纯文本，简化拼接逻辑。
          """
          #初始化实例时进行如下操作
          #获取该类自定义的所有方法
          self.functions=self.__getfunc__()
          self.tool_schemas=[]
          #获取该类自定义的所有方法的json schema
          from transformers.utils import get_json_schema
          #获取函数json schema
          for function in self.functions:
               try:
                    tool_schema=get_json_schema(function)
                    self.tool_schemas.append(tool_schema)
               except:
                    print("error: {} has no json schema,if it is not your function, please ignore it.".format(function))
     def __getfunc__(self):
          #获取该类自定义的所有方法
          return [getattr(self, func) for func in dir(self) if callable(getattr(self, func)) and not func.startswith("__")]
     #函数运行逻辑
     def __run__(self,function_name,arguments):
          #运行函数
          try:
               function=getattr(self,function_name)
               return function(**arguments)
          except Exception as e:
               print("error: function call failed, reason: {}".format(e))
               return "error: function {name} call failed, reason: {error}".format(name=function_name,error=e)
     #支持将所有函数结果转化为text格式
     def __result2text__(self,result):
          if isinstance(result,list):
               for i,item in enumerate(result):
                    result[i]="{}.{}\n".format(i+1,self.__result2text__(item))
          return str(result)
     async def __call__(self,tool_calls):
          #解析函数调用，函数调用默认都可以异步执行
          """
          所有函数都默认有返回值，因此不在此处过滤
          函数返回值全部以纯文本格式返回，list会添加序号
          """
          import json
          import asyncio
          task_list=[]
          result_list=[]
          for function in tool_calls:
               function_name=function['name']
               arguments=json.loads(function['arguments'])
               task1=asyncio.create_task(self.__run__(function_name,arguments))
               task_list.append(task1)
          #等待所有任务完成
          try:
               result_list=await asyncio.gather(*task_list,return_exceptions=True)
               #将结果转化为text格式
               result_list=[self.__result2text__(result) for result in result_list]
          except Exception as e:
               print("error: function call failed, reason: {}".format(e))
               raise Exception("function call failed, reason: {}".format(e))
          return result_list
     async def __function__(self,tool_calls):
          """
          __call__方法的高级封装
          输入tool_calls列表
          返回function_result_messages列表
          """
          import asyncio
          result=await self.__call__(tool_calls)
          #设置function result message模板
          function_result_messages=[]
          template={'role':'tool','content':'','tool_call_id':'','name':''}
          for index,tool_call in enumerate(tool_calls):
               function_result_message=template.copy()
               function_result_message['tool_call_id']=tool_call['id']
               function_result_message['name']=tool_call['name']
               function_result_message['content']+=result[index]
               function_result_messages.append(function_result_message)
          return function_result_messages

               
               
               
               
               

#要定义自己的工具箱，请先继承Tool_Call类,然后编写self函数，__ 开头的函数为保留函数，它们将不会被视为tools。
# 
# 这里提供一个常用的工具的集合

#实现
#继承Tool_Call类
#工具列表：
#1、获取当前时间
#2、获取指定地区和日期的天气信息
#3、获取每日早报新闻
#4、百度百科查询
#5、联网搜索: 使用bocha_api
#6、获取Epic今日免费游戏
#7、获取政治新闻
#8、获取科技新闻
#9、获取正在热映的电影信息


#可以继续将RAG的逻辑添加到tools中，这里暂时不展示，后续会补上

#long_memory的recall()方法一般调用逻辑如下：
#long_memory=Long_Memory(uri=uri)
async def remember_memory(time:list,keywords:list,user_id=None,long_memory=None):
     """
     If the thing the user mentioned to you may have happened a long time ago,  calling this function will help you find the answer from previous memories.

     Args:
         time: If you want to recall something that happened at a specific time, please enter a list of date ranges in YYY-MM-DD format, such as ['2001-12-3','2002-01-12']. Make sure that the thing you want to recall must have happened within this time range. Pay special attention to the fact that the date should not exceed the number of days in each month.
         keywords: If you want to search for memories related to certain keywords, please enter this parameter format as a list of strings. For example, ['food','restaurant'] will search for memories related to food and restaurant.
         user_id: not used in this function, ignore it.
     """
     import asyncio
     if user_id==None:
          print("please provide the user'user_id.")
          raise Exception("parameter lost") 
     if long_memory==None:
          print("please provide the long_memory object.")
          raise Exception("parameter lost")
     task_list=[]
     if isinstance(time,str):
          #如果time是字符串，则认为是单个时间范围
          time_range_list=[time]
     else:
          #如果time是列表，则认为是多个时间范围
          time_range_list=time
     for time_range in time_range_list:
          #这里可以引入一个时间检查逻辑，确保日期没有超过月份对应的最大日期
          #异步添加任务
          task_list.append(
                 long_memory.data_query(
                      user_id=user_id,
                      time_range=time_range,
                      keywords=keywords,
                    
          ))
     #同时启动
     asyncio.gather(*task_list)
     result_list=[]
     for task in task_list:
          result_list.extend(await task)
     #组合成纯文本格式
     result_text=""
     for item in result_list:
          role=item['role']
          content=item['content']
          result_text+="{}:{}\n".format(role,content)
     return result_text


class my_tool_call(Tool_Call):
    def __init__(self):
        super().__init__()
    #获取当前时间
    async def get_time(self):
        import datetime
        """
        Gets the current time.
        Returns:
            The current time in the format of "YYYY-MM-DD HH:MM:SS".
        """
        now = datetime.datetime.now()
        result= now.strftime("%Y-%m-%d %H:%M:%S")
        return result

    # 获取指定地区和日期的天气信息
    async def get_weather(self, area: str, date: str):
        """
        Gets the weather information for a given area and date.

        Args:
            area: The name of the area for which to query the weather. This can be any city, region name, or latitude|longitude, e.g., "Beijing Changping District", "116.40741|39.90421". If the returned result is rejected by the user, more specific location details should be provided, down to the city, district, or county.
            date: The date for which to query the weather. This supports any time-related description, e.g., "February 11th", "this afternoon", "tomorrow", "this week", "this month", etc.

        Returns:
            A dictionary with the following keys:
            - status: The status of the request, either "success" or "error".
            - query: The query statement.
            - content: The content of the weather information.
            - from_url: The URL of the weather information source.
            - request_time: The time the request was made.
        """
        # 组织查询语句
        query = "Query weather: {area} area {date} weather".format(area=area, date=date)
        # 调用搜索函数
        result = await self.__search__(query, 'oneDay', True, 3)
        # 组织返回内容
        return_message = {
            "query": query,
            "content": "\n".join([item['summary'] for item in result['data']['webPages']['value']]),
            "from_url": [item['url'] for item in result['data']['webPages']['value']],
            'request_time': await self.get_time(),
            "status": "success"
        }
        return return_message

    # 获取每日早报新闻
    async def get_dailynews(self):
        """
        Retrieves the daily briefing news.

        Returns:
            A dictionary with the following keys:
            - query: The query statement.
            - content: The content of the daily news.
            - from_url: The URL of the news source.
            - request_time: The time the request was made.
            - status: The status of the request, either "success" or "error".
        """
        import httpx
        base_url = "https://60s.viki.moe?v2=1"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(base_url)
            if response.status_code == 200:
                result = response.json()
                return_message = {
                    "query": "Daily briefing news",
                    "content": "\n".join(result['data']['news']),
                    "from_url": result['data']['url'],
                    "request_time": await self.get_time(),
                    "status": "success"
                }
            else:
                return_message = {
                    "query": "Daily briefing news",
                    "content": "",
                    "from_url": "",
                    "request_time": await self.get_time(),
                    "status": "error:{status_code}".format(status_code=response.status_code)
                }
        except Exception as e:
            return_message = {
                "query": "Daily briefing news",
                "content": "Failed to retrieve",
                "from_url": "",
                "request_time": await self.get_time(),
                "status": "error:{error}".format(error=e)
            }
            
        return return_message

    # 百度百科查询
    async def get_encyclopedia(self, word: str, snippet: bool = True):
        """
        Retrieves the Baidu Encyclopedia entry for a given word.

        Args:
            word: The word to query the encyclopedia entry for.
            snippet: Whether to return only the summary. Default is True. If the full content of the entry is needed, set this to False.

        Returns:
            A list of content items, where each item has a maximum of 512 characters.
            Each item in the list is a dictionary with the following keys:
            - content: The content.
            - metadata:
                - title: The title.
                - url: The URL.
            - snippet: The summary. For a single URL search result, the snippet for each item is the same.
            - status: The status of the request, either "success" or "error".
        """
        #import threading
        from url_tools import doc_process
        from langchain_community.document_loaders import AsyncHtmlLoader

        base_url = "https://baike.baidu.com/item/{word}"
        loader = AsyncHtmlLoader([base_url.format(word=word)])
        try:
            docs = loader.load()
            result = doc_process(docs)
        except Exception as e:
            result = [{
                "content": "Failed to retrieve Baidu Encyclopedia entry, reason: {error}".format(error=e),
                "metadata": {"title": "", "url": "", "snippet": ""},
                "status": "error:{error}".format(error=e),
                'snippet': ''
            }]
        if snippet:
            return_message = {
                'content': result[0]['snippet'],
                'metadata': result[0]['metadata'],
                'status': result[0]['status']
            }
            return return_message
        else:
            return result

    # 获取 Epic Games 免费游戏推荐
    async def get_epic_games(self):
        """
        Retrieves the daily free games from Epic Games.

        Returns:
            A list of dictionaries, each containing the following keys:
            - title: The title of the game.
            - cover: The cover image URL of the game.
            - description: The description of the game.
            - original_price: The original price of the game.
            - is_free: Boolean indicating whether the game is free now.
            - free_start: The start time of the free offer.
            - free_end: The end time of the free offer.
            - link: The URL to the game's page.
            - status: The status of the request, either "success" or "error".
        """
        base_url = "http://60s-api.viki.moe/v2/epic"
        import httpx
        try:
            response = httpx.get(base_url)
            if response.status_code == 200:
                result = response.json()
                game_list = result['data']
                return_message = [{
                    "title": item['title'],
                    "cover": item['cover'],
                    "description": item['description'],
                    "original_price": item['original_price'],
                    "is_free": item['is_free_now'],
                    "free_start": item['free_start'],
                    "free_end": item['free_end'],
                    "link": item['link'],
                    "status": "success"
                } for item in game_list]
            else:
                return_message = [{
                    "title": "",
                    "cover": "",
                    "description": "",
                    "original_price": "",
                    "is_free": "",
                    "free_start": "",
                    "free_end": "",
                    "link": "",
                    "status": "error:{status_code}".format(status_code=response.status_code)
                }]
        except Exception as e:
            return_message = [{
                "title": "",
                "cover": "",
                "description": "",
                "original_price": "",
                "is_free": "",
                "free_start": "",
                "free_end": "",
                "link": "",
                "status": "error:{error}".format(error=e)
            }]
        return return_message

    # 联网搜索
    async def web_search(self, query: str, freshness: str, summary: bool, count: int):
        """
        Performs a web search for the given query.

        Args:
            query: The search query.
            freshness: The freshness of the search results. It specifies the time range for the search.
            summary: Whether to display summaries of the search results. The default is False.
            count: The number of search results to return. The default is 10.

        Returns:
            The search result as a JSON object if the request is successful.
            None if the request fails.
        """
        import httpx
        global api_key
        global base_url
        url = f"{base_url}/web-search"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        # 构建请求体
        body = {"query": query, "freshness": freshness, "summary": summary, "count": count}
        # 过滤掉值为None的参数
        body = {k: v for k, v in body.items() if v is not None}
        try:
            # 发送异步 POST 请求
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=body)
                # 检查请求是否成功
                if response.status_code == 200:
                    # 将结果转化为 JSON
                    result = response.json()
                    return_message = {
                    "query": "Daily briefing news",
                    "content": "\n".join(result['data']['news']),
                    "from_url": result['data']['url'],
                    "request_time": await self.get_time(),
                    "status": "success"}
                    return return_message
                else:
                    print(f"Request failed: {response.status_code}")
                    return f"Request failed: {response.status_code}"
        except httpx.RequestError as e:
            print(f"Request failed: {e}")
            return "Request failed: {e}"

    # 获取正在上映的电影信息
    async def get_now_movies(self):
        """
        Retrieves information about movies currently showing.

        Returns:
            A dictionary containing the following keys:
            - id: The ID of the movie.
            - haspromotionTag: Boolean indicating whether the movie has a promotion tag.
            - img: The image URL of the movie poster.
            - version: The version information of the movie.
            - nm: The name of the movie.
            - preShow: Boolean indicating whether the movie is a pre-show.
            - sc: The score of the movie.
            - globalReleased: Boolean indicating whether the movie has been released globally.
            - wish: The number of people wishing to see the movie.
            - star: The main actors of the movie.
            - rt: The release date of the movie.
            - showInfo: Information about the movie's showings on the day, such as the number of cinemas and showtimes.
            - showst: The show status.
            - wishst: The wish status.
            - comingTitle: The release date and day of the week of the movie.
            - showStateButton: A dictionary containing button color, content, and whether it is only for pre-show.
        """
        import aiohttp
        url = "https://apis.netstart.cn/maoyan/index/movieOnInfoList"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    data = await response.json()
                    return data
        except Exception as e:
            print(f"Failed to retrieve movie information: {e}")
            return "Failed to retrieve movie information: {e}"

    # 获取时政新闻
    async def get_politics_news(self):
        """
        Retrieves political news.

        Returns:
            A dictionary with the following keys:
            - query: The query statement.
            - content: The content of the political news.
            - from_url: The URL of the news source.
            - request_time: The time the request was made.
            - status: The status of the request, either "success" or "error".
        """
        # 组织查询语句
        query = "Political hotspots, national policy releases"
        # 调用搜索函数
        result = await self.__search__(query, 'oneWeek', True, 10)
        # 组织返回内容
        if result:
            return_message = {
            "query": query,
            "content": "\n".join([item['summary'] for item in result['data']['webPages']['value']]),
            "from_url": [item['url'] for item in result['data']['webPages']['value']],
            'request_time': await self.get_time(),
            "status": "success"
        }
        else:
            return_message = {
            "query": query,
            "content": "",
            "from_url": "",
            'request_time': await self.get_time(),
            "status": "error:no result, please try again now or later"
        }
        return return_message

    # 获取科技热点新闻
    async def get_tech_news(self):
        """
        Retrieves technology news.

        Returns:
            A dictionary with the following keys:
            - query: The query statement.
            - content: The content of the technology news.
            - from_url: The URL of the news source.
            - request_time: The time the request was made.
            - status: The status of the request, either "success" or "error".
        """
        query = "Leading edge technology, technological breakthroughs, future technology fields"
        # 调用搜索函数
        result = await self.__search__(query, 'oneWeek', True, 10)
        # 组织返回内容
        return_message = {
            "query": query,
            "content": "\n".join([item['summary'] for item in result['data']['webPages']['value']]),
            "from_url": [item['url'] for item in result['data']['webPages']['value']],
            'request_time': await self.get_time(),
            "status": "success"
        }
        return return_message
    async def __search__(query, freshness, summary, count):
        """
        query: 用户的搜索词
        freshness: 搜索指定时间范围内的网页
        summary: 是否显示摘要，默认不显示
        count: 返回结果的数量，默认10条
        """
        import requests
        import httpx
        global api_key
        global base_url
        url = f"{base_url}/web-search"
        headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"}
        # 构建请求体
        body = {
        "query": query,
        "freshness": freshness,
        "summary": summary,
        "count": count}
        # 过滤掉值为None的参数
        body = {k: v for k, v in body.items() if v is not None}
        try:
            # 发送异步 POST 请求
            async with httpx.AsyncClient() as client:
                 response = await client.post(url, headers=headers, json=body)
            # 检查请求是否成功
            if response.status_code == 200:
                 # 将结果转化为 JSON
                 result = response.json()
                 return result
            else:
                 print(f"请求出错: {response.status_code}")
                 return None
        except requests.exceptions.RequestException as e:
            print(f"请求出错: {e}")
            return None
    #长期记忆搜索
    async def remember_memory(self,time:list,keywords:list,user_id=None,long_memory=None):
         """
         If the thing the user mentioned to you may have happened a long time ago,  calling this function will help you find the answer from previous memories.
         
         Args:
           time: If you want to recall something that happened at a specific time, please enter a list of date ranges in YYY-MM-DD format, such as ['2001-12-3','2002-01-12']. Make sure that the thing you want to recall must have happened within this time range. Pay special attention to the fact that the date should not exceed the number of days in each month.
           keywords: If you want to search for memories related to certain keywords, please enter this parameter format as a list of strings. For example, ['food','restaurant'] will search for memories related to food and restaurant.
           user_id: not used in this function, ignore it.
           long_memory:not used in this function, ignore it.
         """
         import asyncio
         if user_id==None:
              print("please provide the user'user_id.")
              raise Exception("parameter lost") 
         if long_memory==None:
              print("please provide the long_memory object.")
              raise Exception("parameter lost")
         task_list=[]
         if isinstance(time,str):
            #如果time是字符串，则认为是单个时间范围
            time_range_list=[time]
         else:
          #如果time是列表，则认为是多个时间范围
          time_range_list=time
         for time_range in time_range_list:
          #这里可以引入一个时间检查逻辑，确保日期没有超过月份对应的最大日期
          #异步添加任务
          task_list.append(
                 long_memory.data_query(
                      user_id=user_id,
                      time_range=time_range,
                      keywords=keywords,
                    
          ))
          #同时启动
          asyncio.gather(*task_list)
          result_list=[]
          for task in task_list:
               result_list.extend(await task)
          #组合成纯文本格式
          result_text=""
          for item in result_list:
               role=item['role']
               content=item['content']
               result_text+="{}:{}\n".format(role,content)
          return result_text

         

#-------------tool_call使用-------------------

#创建好了自己的tool_call类后，进行初始化，初始化将会根据注释自动生成schema
"""
tools=my_tool_call()
#获取tools的schema
tools_schemas=tools.tool_schemas

#传入Agent的初始化

agent=Agent(use_summary=True,use_memory=True,use_tool=True,tools_schemas=tools_schemas)

#现在，agent已经具有函数调用能力

#初始化一个client

#agent使用示例
from volcenginesdkarkruntime  import Ark
client=Ark(api_key="4a65a771-f695-4fe6-8c34-79508e9427c4")
model="ep-20241217224812-blnsj"

#假设我们有如下messages

messages=[
     {'role': 'user', 'text': '今天北京天气如何？'}
]

#调用agent
response=agent(messages,client,model,stream=True)

#这里的response代码保持不变
recorder=None
for item in response:
     if isinstance(item,str):
          print(item)
     else:
          recoder=item 

#recorder将会传回一个字典，包含了 {'generate_text':input_text,'tool_calls':function_list,'assistant_summary':summary_list}

#对于生成的recorder处理如下，先预先定义一个assistant_message的模板

assistant_message={'role':'assistant','content':'','function_calls':None,'tool_calls':None}

if recorder:
     #generate_text用于记录assistant生成的回复，如果启用了summary，则直接记录assistant的summary即可
     if 'assistant_summary' in recorder.keys():
          assistant_message['content']=recorder['assistant_summary']
     else:
          assistant_message['content']=recorder['generate_text']
     #插入到messages中
     messages.append(assistant_message)
     #接下来，检查是否有tool_calls
     if 'tool_calls' in recorder.keys():
          tool_calls=recorder['tool_calls']
          #目前主流的api都支持多工具同步调用
          #插入assistant_message
          assistant_message['tool_calls']=tool_calls
          #调用工具的高级封装__function__，直接获得messages形式返回的结果
          function_result_messages=tools.__function__(assistant_message)    
          #将结果插入到messages中
          messages.extend(function_result_messages)

#进入新一轮对话
#如果最后一个消息role:tool，即工具调用结果，则立即传入agent产生新的对话

if messages[-1]['role']=='tool':
     response=agent(messages[-1]['content'],client,model,stream=True)
     recorder=None    
     for item in response:
          if isinstance(item,str):
               print(item)
          else:
               recorder=item
"""
#.............................................


          
          
          
          






