#----------------------------------------------------------

        ##########博查搜索接口服务##########

#--------------------------------------------------------

import os 
file_dir=os.path.dirname(__file__)
config_path=os.path.join(file_dir,"../../Setup/config.yaml")
import yaml
with open(config_path,"r",encoding="utf-8") as f:
    config=yaml.load(f,Loader=yaml.FullLoader)
api_key=config["bocha"]["api_key"]
base_url=config["bocha"]["base_url"]

import requests
import requests
import json
import httpx
async def search_(query, freshness, summary, count, api_key=api_key, base_url=base_url):
    url = f"{base_url}/search"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 构建请求体
    body = {
        "query": query,
        "freshness": freshness,
        "summary": summary,
        "count": count
    }
    
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

#多query异步搜索
def search(querys,freshness=None,summary=True,count=10,api_key=api_key,base_url=base_url):
    import asyncio
    loop = asyncio.get_event_loop()
    tasks = [asyncio.ensure_future(search_(query, freshness, summary, count, api_key, base_url)) for query in querys]
    results = loop.run_until_complete(asyncio.gather(*tasks))
    #print(results)
     # 收集有效的返回结果
    web_results = []
    for res in results:
        if res is not None and 'data' in res and 'webPages' in res['data']:
            for item in res['data']['webPages'].get('value', []):
                web_results.append({'content': item['summary'] + '\ntime: ' + item.get('dateLastCrawled', '未知时间')})
    return web_results



if __name__ == '__main__':

    results = search(["手机智能体的2025年发展趋势","智能手表的2025年发展趋势"], freshness="oneWeek", summary=True, count=10, api_key=api_key)
    with open("/root/4.0/Server/Search/Web_search/bocha_result.txt",'w',encoding='utf-8') as f:
        f.write(f"{results}")
