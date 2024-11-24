import yaml 
#获取当前脚本所在目录
import os
cur_dir=os.path.dirname(__file__)
#读取配置文件
config_path=os.path.join(cur_dir,"config.yaml")
with open(config_path,'r') as file:
    config=yaml.safe_load(file)
def zhipuAI_embedding(text_list,model="embedding-3",dimensions=512):
    from zhipuai import ZhipuAI
    assert config['zhipuAI']['api_key']!="", "请在config.yaml中配置zhipuai的api_key"
    client = ZhipuAI(api_key=config['zhipuAI']['api_key']) 
    response= client.embeddings.create(
        input=text_list,
        model=model,
        dimensions=dimensions,        
    )
    return [  i.embedding     for i in response.data]
def doubaoAI_embedding(text_list,dimensions=768):
    from volcenginesdkarkruntime import Ark
    client = Ark(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
)
    resp = client.embeddings.create(
    model=config['doubaoembedding']['ep_point'],
    input=text_list,
    dimensions=dimensions,
)
    return [  i.embedding     for i in resp.data]