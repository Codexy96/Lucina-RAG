"""  
提示词工程分为两个部分。

第一个部分面向任务构建提示词模板函数，转化为message消息列表

第二部分在不同的大模型上应用消息列表，返回内容

"""
import os
flie_path=os.path.dirname(__file__)
config_path=os.path.join(flie_path,'config.yaml')
import yaml 
import json
with open(config_path  ,'r') as file:
    config=yaml.safe_load(file)

def zhipuAI(messages, model='glm-4-air', **kwargs):
    from zhipuai import ZhipuAI
    assert config['zhipuAI']['api_key'] != "", "请在config.yaml中配置zhipuai的api_key"
    client = ZhipuAI(api_key=config['zhipuAI']['api_key'])
    
    response = client.chat.completions.create(
        model=model,  # 填写需要调用的模型编码
        messages=messages,
        stream=True,  # 开启流式返回
        **kwargs
    )
    
    for chunk in response:
        yield chunk.choices[0].delta.content.encode('utf-8')

def aliAI(messages,model="qwen-plus",**kwargs):
    from openai  import OpenAI
    assert config['aliAI']['api_key']!="", "请在config.yaml中配置ali的api_key"
    assert config['aliAI']['base_url']!="", "请在config.yaml中配置ali的base_url"
    client=OpenAI(
        api_key=config['aliAI']['api_key'],
        base_url=config['aliAI']['base_url']
    )
    completion=client.chat.completions.create(
        model=model,
        messages=messages,
        **kwargs
    )
    return completion.choices[0].message

def doubaoAI(messages,**kwargs):
    from volcenginesdkarkruntime  import Ark
    assert config['doubaoAI']['api_key']!="", "请在config.yaml中配置doubao的api_key"
    assert config['doubaoAI']['ep_point']!="", "请在config.yaml中配置doubao的ep_point"
    client=Ark(
        api_key=config['doubaoAI']['api_key'])
    completion=client.chat.completions.create(
        model=config['doubaoAI']['ep_point'],
        messages=messages,
        **kwargs
    )
    return completion.choices[0].message

def deepseekAI(messages,model="deepseek-chat",**kwargs):
    from openai import OpenAI
    assert config['deepseekAI']['api_key']!="", "请在config.yaml中配置deepseek的api_key"
    assert config['deepseekAI']['base_url']!="", "请在config.yaml中配置deepseek的base_url"
    client=OpenAI(
        api_key=config['deepseekAI']['api_key'],
        base_url=config['deepseekAI']['base_url']
    )
    completion=client.chat.completions.create(
        model=model,
        messages=messages,
        **kwargs
    )
    return completion.choices[0].message

def baichuanAI(messages,model="Baichuan2-Turbo",**kwargs):
    assert config['baichuanAI']['api_key']!="", "请在config.yaml中配置baichuan的api_key"
    assert config['baichuanAI']['base_url']!="", "请在config.yaml中配置baichuan的base_url"
    from openai import OpenAI
    client=OpenAI(
        api_key=config['baichuanAI']['api_key'],
        base_url=config['baichuanAI']['base_url']
    )
    completion=client.chat.completions.create(
        model=model,
        messages=messages,
        **kwargs
    )
    return completion.choices[0].message
    

