#---------------------------------------

##############多模态向量模型#################

##考虑到需要在流式输出中频繁计算余弦相似度，因此将向量以np的形式输出

#encode_image: 支持文本路径或者路径列表，返回向量列表
#encode_text: 支持文本字符串或者字符串列表，返回向量列表




#---------------------------------------

#设置环境变量，多模态向量模型暂时使用阿里服务

import os
os.environ['DASHSCOPE_API_KEY']=""

#----------------------------------------
class Embedding:
    def __init__(self):
        self.dim=1024
        self.name="multimodal-embedding-v1"
    def encode_images(self,image_paths,time_sleep=0.5):
        """
        多批次可以优化的代码：
        resp= dashscope.MultiModalEmbedding.call(
    model="multimodal-embedding-v1",
    input=[{'image':input_data,'text':'这是一个骆驼祥子的书籍照片'},{'text':text}]) 
        
        
        """
        embed_list=[]
        import dashscope
        from http import HTTPStatus
        import time
        if not isinstance(image_paths,list):
            raise TypeError("image_paths参数类型错误，请检查为列表,如果是单个图片路径，请使用encode_image方法")
        for path in image_paths:
            time.sleep(time_sleep)
            if not os.path.exists(path):
                print(f"图片{path}不存在")
                raise FileNotFoundError
            embed=self.encode_image(path)
            if embed is not None:
                embed_list.append(embed)
            else:
                print(f"图片{path}编码失败")
                embed_list.append(None)
        return embed_list
            
    def encode_image(self,image_path):
        import dashscope
        from http import HTTPStatus
        import numpy as np
        if not isinstance(image_path,str):
            raise TypeError("image_path参数类型错误，请检查为字符串,如果是多个图片路径，请使用encode_images方法")
        # 读取图片并转换为Base64
        inputs=self.image_process(image_path)

        # 调用模型接口
        resp = dashscope.MultiModalEmbedding.call(
    model="multimodal-embedding-v1",
    input=inputs)
        if resp.status_code == HTTPStatus.OK:
            return np.array([emb['embedding']        for emb  in    resp['output']['embeddings']][0])
        else:
            print(f"模型服务内部错误，状态码：{resp.status_code}。错误详情：{resp}")
            print(f"参考输入数据：{inputs[0]["image"][:30]}")
            return None
            #raise Exception(resp)
            
    def encode_text(self,text):
        """
        text: str
        output: embedding_list
        
        """
        import dashscope
        from http import HTTPStatus
        import numpy as np
        if isinstance(text,str):
            input = [{'text': text}]
        elif isinstance(text,list):
            input = [{'text': t} for t in text]
        else:
            print("输入数据类型错误，请检查参数为str或list后重试")
            raise TypeError

        # 调用模型接口
        resp = dashscope.MultiModalEmbedding.call(
    model="multimodal-embedding-v1",
    input=input)
        if resp.status_code == HTTPStatus.OK:
            return np.array(  [emb['embedding']       for emb  in    resp['output']['embeddings']])
        else:
            print(f"模型服务内部错误，状态码：{resp.status_code}。")
            raise Exception("模型服务繁忙")
    def images_process(self,image_paths):
        import base64
        import os
        input_images=[]
        for path in image_paths:
            if not os.path.exists(path):
                print(f"图片{path}不存在")
                raise FileNotFoundError
            with open(path, "rb") as image_file:
                # 读取文件并转换为Base64
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                # 设置图像格式
                image_format =path.split('.')[-1]  # 根据实际情况修改，这里默认使用文件结尾
                image_data = f"data:image/{image_format};base64,{base64_image}"
                # 输入数据
                input_images.append({'image': image_data})
        return input_images
    def image_process(self,image_path):
        import base64
        import os
        if isinstance(image_path,str):
            if not os.path.exists(image_path):
                print(f"图片{image_path}不存在")
                raise FileNotFoundError
            with open(image_path, "rb") as image_file:
                # 读取文件并转换为Base64
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                # 设置图像格式
                image_format =image_path.split('.')[-1]  # 根据实际情况修改，这里默认使用文件结尾
                image_data = f"data:image/{image_format};base64,{base64_image}"
                # 输入数据
                inputs = [{'image': image_data}]
                return inputs
        elif isinstance(image_path,list):
            inputs=[]
            for img_path in image_path:
                if not os.path.exists(img_path):
                    print(f"图片{img_path}不存在")
                    raise FileNotFoundError
                with open(img_path, "rb") as image_file:
                    # 读取文件并转换为Base64
                    base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                    # 设置图像格式
                    image_format =img_path.split('.')[-1]  # 根据实际情况修改，这里默认使用文件结尾
                    image_data = f"data:image/{image_format};base64,{base64_image}"
                    # 输入数据
                    inputs.append({'image': image_data})
            return inputs
        else:
            print("输入数据类型错误，请检查参数为str或list后重试")
            raise TypeError

class AsyncEmbedding:
    def __init__(self):
        #读取环境变量
        self.api_key=os.getenv('DASHSCOPE_API_KEY') 
        # 请求URL
        self.url = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/multimodal-embedding/multimodal-embedding"
        # 请求头
        self.headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {self.api_key}",
        #"X-DashScope-WorkSpace": "ws_QTggmeAxxxxx"  # 如果需要，可以在这里指定workspace
    }
        self.name="multimodal-embedding-v1"
    async def encode_images(self,image_paths):
        """
        多批次可能的优化的代码：
        contents:[
        {'image':},
        {'image':},
        ]
        """
        import numpy as np
        embed_list=[]
        for path in image_paths:
            embed=await self.encode_image(path)
            embed_list.append(embed)
        return np.array(embed_list)
        
    async def encode_image(self,image_path):
        #获取图片编码
        import requests
        import json
        import aiohttp
        import numpy as np
        input_image=self.image_process(image_path)
         # 请求体
        data = {
        "model": "multimodal-embedding-v1",
        "input": {
            "contents": input_image
        },
        "parameters": {}
    }  
        # 发送POST请求
        async with aiohttp.ClientSession() as session:
            async with session.post(self.url,headers=self.headers,data=json.dumps(data)) as response:
                #检查响应状态码
                if response.status==200:
                    result=await response.json()
                    #提取嵌入向量
                    embeddings=[ item['embedding'] for item in result['output']['embeddings']][0]
                    return np.array(embeddings) 
                else:
                    print(f"请求失败，状态码: {response.status}")
                    print(await response.text())
                    return np.array([])
        """
        response = requests.post(self.url, headers=self.headers, data=json.dumps(data))
        # 检查响应状态码
        if response.status_code == 200:
            result = response.json()
            print(result['w'])
        else:
            print(f"请求失败，状态码: {response.status_code}")
            print(response.text)
        """
    async def encode_text(self,text):
        #获取文本编码
        import requests
        import json
        import numpy as np
        if isinstance(text,str):
            input = [text]
        elif isinstance(text,list):
            input =text
        else:
            print("输入数据类型错误，请检查参数为str或list后重试")
            raise TypeError
        # 请求体
        data = {
        "model": "multimodal-embedding-v1",
        "input": {
            "contents":[
                {"text": t} for t in input
            ]
        },
        "parameters": {}
    }  
        # 发送POST请求
        response = requests.post(self.url, headers=self.headers, data=json.dumps(data))
        # 检查响应状态码
        if response.status_code == 200:
            result = response.json()
            #提取嵌入向量
            embeddings=[ item['embedding'] for item in result['output']['embeddings']]
            return np.array(embeddings)
        else:
            print(f"请求失败，状态码: {response.status_code}")
            print(response.text)
    def images_process(self,image_paths):
        import base64
        import os
        inputs=[]
        for img_path in image_paths:
            with open(img_path,'rb') as image_file:
                # 读取文件并转换为Base64
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                # 设置图像格式
                image_format=img_path.split('.')[-1]  #根据实际情况修改，这里默认使用文件结尾
                image_data=f"data:image/{image_format};base64,{base64_image}"
                # 输入数据
                input_= {'image': image_data}
                inputs.append(input_)
        return inputs

    def image_process(self,image_path):
        import base64
        import os
        if isinstance(image_path,str):
            if not os.path.exists(image_path):
                print(f"图片{image_path}不存在")
                raise FileNotFoundError
            with open(image_path, "rb") as image_file:
                # 读取文件并转换为Base64
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                # 设置图像格式
                image_format =image_path.split('.')[-1]  # 根据实际情况修改，这里默认使用文件结尾
                image_data = f"data:image/{image_format};base64,{base64_image}"
                # 输入数据
                return [{'image': image_data}]
        elif isinstance(image_path,list):
            inputs=[]
            for img_path in image_path:
                if not os.path.exists(img_path):
                    print(f"图片{img_path}不存在")
                    raise FileNotFoundError
                with open(img_path, "rb") as image_file:
                    # 读取文件并转换为Base64
                    base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                    # 设置图像格式
                    image_format =img_path.split('.')[-1]  # 根据实际情况修改，这里默认使用文件结尾
                    image_data = f"data:image/{image_format};base64,{base64_image}"
                    # 输入数据
                    inputs.append({'image': image_data})
            return inputs
        else:
            print("输入数据类型错误，请检查参数为str或list后重试")
            raise TypeError


#test
if __name__=='__main__':
    #model=Embedding()
    #print(model.encode_image(r"/root/script/test.jpeg"))
    #print(model.encode_text(["你好，世界！","你好，世界！","你好，世界！"]))
    #测试
    """
    import torch
    model=AsyncEmbedding()
    import asyncio
    loop = asyncio.get_event_loop()
    tasks = [
        asyncio.ensure_future(model.encode_images([r"/root/script/test.jpeg",r"/root/script/test.jpeg"])),
        asyncio.ensure_future(model.encode_text(["你好，世界！","你好，世界！","你好，世界！"]))
    ]
    loop.run_until_complete(asyncio.wait(tasks))
    for task in tasks:
        print(torch.tensor(task.result()).shape)
    """
    import numpy as np
    model=Embedding()
    print(np.array(model.encode_images([r"/root/script/test.jpeg",r"/root/script/test.jpeg"])).shape)
