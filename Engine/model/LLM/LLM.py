"""  
提示词工程分为两个部分。

第一个部分面向任务构建提示词模板函数，转化为message消息列表

第二部分在不同的大模型上应用消息列表，返回内容

"""
import os
import re
import textwrap
flie_path=os.path.dirname(__file__)
config_path=os.path.join(flie_path,'config.yaml')
import yaml 
import json
with open(config_path  ,'r') as file:
    config=yaml.safe_load(file)

""" 
每个模型具有三个方法。

chat：输入文本,输出文本，可选择流式

apply: 输入messages列表，输出添加了模型输出的message，无法选择流式

response: 输入messages列表，输出模型的text回答，可选择流式

"""

class zhipuAI:
    def __init__(self):
        from zhipuai import ZhipuAI
        assert config['zhipuAI']['api_key'] != "", "请在config.yaml中配置zhipuai的api_key"
        self.client = ZhipuAI(api_key=config['zhipuAI']['api_key'])
    def chat(self,text,model='glm-4-air',stream=False,**kwargs):
        """
        参数：
        text:输入文本
        model：模型型号，默认为glm-4-air
        stream：是否流式返回，默认为False
        其他参数参考zhipu的API文档
        返回：
        文本流式输出
        """
        messages=[{'role':'user','content':text}]
        response = self.client.chat.completions.create(
            model=model,  # 填写需要调用的模型编码
            messages=messages,
            stream=stream,  # 默认关闭流式返回
            **kwargs
        )
        if stream==True:
              return self.yield_output(response)
        else:
            return  response.choices[0].message.content
    def yield_output(self,response):
        for chunk in response:
            yield chunk.choices[0].delta.content
            
    def apply(self,messages,model:str='glm-4-air',**kwargs):
        """
        参数：
        messages:输入的message列表
        model：模型型号，默认为glm-4-air
        无法选择流式
        其他参数参考zhipu的API文档

        返回：
        添加了模型输出的message列表
        """
        response = self.client.chat.completions.create(
            model=model,  # 填写需要调用的模型编码
            messages=messages,
            stream=False,  # 关闭流式返回
            **kwargs
        )
        role=response.choices[0].message.role
        content=response.choices[0].message.content
        messages.append({'role':role,'content':content})
        return messages
    def response(self,messages,model:str='glm-4-airx',stream=False,**kwargs):
        """
        参数：
        messages:输入的message列表
        model：模型型号，默认为glm-4-airx
        stream：是否流式返回，默认为False
        其他参数参考zhipu的API文档
        返回：
        模型的text回答流式输出
        """
        response = self.client.chat.completions.create(
            model=model,  # 填写需要调用的模型编码
            messages=messages,
            stream=stream,  # 默认关闭流式返回
            **kwargs
        )
        if not stream:
            return response.choices[0].message.content
        else:
            return self.yield_output(response)


""" 
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

""" 

class aliAI:
    def __init__(self):
        from openai  import OpenAI
        assert config['aliAI']['api_key']!="", "请在config.yaml中配置ali的api_key"
        assert config['aliAI']['base_url']!="", "请在config.yaml中配置ali的base_url"
        self.client=OpenAI(
            api_key=config['aliAI']['api_key'],
            base_url=config['aliAI']['base_url']
        )
    def yield_output(self,response):
        for chunk in response:
            yield chunk.choices[0].delta.content
    def chat(self,text,model="qwen-plus",stream=False,**kwargs):
        """
        参数：
        text:输入文本
        model：模型型号，默认为qwen-plus
        stream：是否流式返回，默认为False
        其他参数参考openai的API文档
        返回：
        文本字符串
        """
        messages=[{'role':'user','content':text}]
        completion=self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=stream,
            **kwargs
        )
        if not stream:
            return completion.choices[0].message.content
        else:
            return self.yield_output(completion)
    def apply(self,messages,model:str='qwen-plus',**kwargs):
        completion=self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=False,
            **kwargs
        )
        role=completion.choices[0].message.role
        content=completion.choices[0].message.content
        messages.append({'role':role,'content':content})
        return messages
    def response(self,messages,model:str='qwen-plus',stream=True,**kwargs):
        completion=self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=stream,
            **kwargs
        )
        if not stream:
            return completion.choices[0].message.content
        else:
            return self.yield_output(completion)
    
        
"""
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
"""
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


"""
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

"""

class deepseekAI:
    def __init__(self):
        from openai import OpenAI
        assert config['deepseekAI']['api_key']!="", "请在config.yaml中配置deepseek的api_key"
        assert config['deepseekAI']['base_url']!="", "请在config.yaml中配置deepseek的base_url"
        self.client=OpenAI(
            api_key=config['deepseekAI']['api_key'],
            base_url=config['deepseekAI']['base_url']
        )
    def yield_output(self,response):
        for chunk in response:
            yield chunk.choices[0].delta.content
    def yield_code_output(self,response):
        code_buffer=""
        code_start_pattern=re.compile(r'\s*python')
        code_end_pattern=re.compile(r'\s*```')
        in_code_block=False
        for chunk in response:
            #print(chunk.choices[0].delta.content)
            content=chunk.choices[0].delta.content 
            if code_start_pattern.match(content):
                in_code_block=True
                code_buffer=""
                continue
            elif code_end_pattern.match(content):
                in_code_block=False
                try:
                    #print(code_buffer)
                    exec(textwrap.dedent(code_buffer)) #textwrap.dedent()用于去掉公共缩进
                except Exception as e:
                     print(e)
                     print("图表生成失败")
                code_buffer=""
            else:
                if in_code_block:
                    code_buffer+=content
                else:
                    yield content
    def chat(self,text,model="deepseek-chat",stream=False,**kwargs):
        """
        参数：
        text:输入文本
        model：模型型号，默认为deepseek-chat
        stream：是否流式返回，默认为False
        其他参数参考openai的API文档
        返回：
        文本字符串
        """
        messages=[{'role':'user','content':text}]
        completion=self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=stream,
            **kwargs
        )
        if not stream:
            return completion.choices[0].message.content
        else:
            return self.yield_output(completion)
    def apply(self,messages,model:str='deepseek-chat',**kwargs):
        completion=self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=False,
            **kwargs
        )
        role=completion.choices[0].message.role
        content=completion.choices[0].message.content
        messages.append({'role':role,'content':content})
        return messages
    def response(self,messages,model:str='deepseek-chat',stream=True,**kwargs):
        completion=self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=stream,
            **kwargs
        )
        if not stream:
            return completion.choices[0].message.content
        else:
            return self.yield_output(completion)
    def response_code(self,messages,model:str='deepseek-chat',stream=True,**kwargs):
        completion=self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=stream,
            **kwargs
        )
        return self.yield_code_output(completion)

def baichuanAI(messages,model="",**kwargs):
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
    
if __name__=="__main__":
    #测试
    llm=zhipuAI()
    print(llm.chat("你好，请问有什么可以帮助您的吗？"))
