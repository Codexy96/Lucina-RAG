"""
这是在香港服务器上中转之后再发送内容的duckgo搜索API。

"""
import requests
import json
import configparser
import os
file_path = os.path.dirname(os.path.abspath(__file__))  
config = configparser.ConfigParser()
config.read(os.path.join(file_path, 'config.ini'))
def fetch_search_results(query, top_k=5):
    url =config.get('duckgo','url')
    headers = {"Content-Type": "application/json"}
    
    # 构造请求数据
    data = {
        "query": query,
        "top_k": top_k
    }
    
    # 发送 POST 请求
    response = requests.post(url, headers=headers, json=data)
    
    # 检查请求是否成功
    if response.status_code == 200:
        # 将结果转化为 JSON
        result = response.json()
        
        # 如果需要从结果中提取信息到列表，假设结果是一个数组
        # 根据实际返回内容进行调整
        result_list = result.get('results', [])  # 假设返回的 JSON 中有 'results' 字段
        if result_list == []:
            return []
        for res in  result_list:
            res['content']=res['content'][0:512]
                
        return result_list
    else:
        print(f"请求失败，状态码: {response.status_code}")
        return []
    
import httpx
import time
import random
import asyncio
async def async_search_results(query, top_k=5):
    #delay = random.uniform(0.2, 0.3)
    #await asyncio.sleep(delay)  # 异步睡眠
    url = config.get('duckgo', 'url')
    headers = {"Content-Type": "application/json"}

    # 构造请求数据
    data = {
        "query": query,
        "top_k": top_k
    }

    # 发送异步 POST 请求
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=data)

    # 检查请求是否成功
    if response.status_code == 200:
        # 将结果转化为 JSON
        result = response.json()
        
        # 如果需要从结果中提取信息到列表，假设结果是一个数组
        # 根据实际返回内容进行调整
        result_list = result.get('results', [])  # 假设返回的 JSON 中有 'results' 字段
        if result_list == []:
            return []
        for res in result_list:
            res['content'] = res['content'][0:512]

        return result_list
    else:
        print(f"请求失败，状态码: {response.status_code}")
        return []

def save(results, query):
    # 去除 query 中不符合文件命名的字符
    import re
    import json
    import os
    safe_query = re.sub('[<>:"/\\|?*]', '', query) 
    directory="save"
    if not os.path.exists(directory):
        os.makedirs(directory)
    file_name = os.path.join(directory, f"{safe_query}.json")
    # 将结果保存到文件
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    print(f"结果已保存到文件: {file_name}")


# 使用示例
if __name__ == "__main__":
    query = "低空经济看好，我该如何就业数据公开"
    import asyncio
    querys=[
        "低空经济看好，我该如何就业数据公开",
        "中国经济增速放缓，如何应对？"
    ]
    tasks = [asyncio.ensure_future(async_search_results(query)) for query in querys]
    results = asyncio.get_event_loop().run_until_complete(asyncio.gather(*tasks))
    #print("搜索结果:", results)
    save(results, query)
