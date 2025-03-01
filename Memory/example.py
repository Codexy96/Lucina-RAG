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
          assistant_message['content']=recoder['assistant_summary']
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
    return None,messages


