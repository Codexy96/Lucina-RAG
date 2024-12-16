from langchain_community.utilities import SearxSearchWrapper
search = SearxSearchWrapper(searx_host="http://8.218.40.87:32769", k=30)
"""
#request实现
"""
#request实现
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import time

def create_session():
    session = requests.Session()
    retry = Retry(
        total=5,  # 最大重试次数
        backoff_factor=1,  # 等待时间指数增加
        status_forcelist=[500, 502, 503, 504]  # 针对这些状态码重试
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def search_searxng(query):
    start_time= time.time()
    searxng_url = 'http://8.218.40.87:32769'
    params = {'q': query, 'format': 'json'}
    
    session = create_session()
    response = session.get(searxng_url, params=params)
    end_time = time.time()
    print("request 搜索耗时：", end_time - start_time)

    if response.status_code == 200:
        return response.json()
    else:
        print("请求失败，状态码：", response)
        return None
    

if __name__ == '__main__':
    query = "python"
    #results = search_searxng(query)

    #if results:
        #for result in results.get('results', []):
            #print(result['title'], result)

    query = "字节跳动薪资待遇如何？"
    start_time = time.time()
    results = search.run(query,engine='bing')
    end_time = time.time()
    print("langchain 搜索耗时：", end_time - start_time)
    print(results)